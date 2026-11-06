"""
MCP Server (Phase 7)
 
Wraps the external data sources -- yfinance (prices + fundamentals) and the
news RSS feed -- as MCP tools, using Anthropic's Model Context Protocol
(the real protocol, via the official `mcp` Python SDK, not a custom
imitation of it).
 
Per spec.md: this is a REFACTOR. The logic inside each tool function
below is the exact same logic that was already working directly inside
the agents (preprocessor_agent.py, technical_agent.py, sentiment_agent.py) in earlier phases -- it has just moved here, behind
a standard tool-calling interface, so any agent (or any other MCP client,
in principle) can reach these data sources the same documented way instead
of importing the libraries directly.
 
Run standalone for a manual smoke test:
    python mcp_layer/server.py
(it will just sit waiting for a client over stdio -- Ctrl+C to quit)
 
Normally, you don't run this directly -- mcp_layer/client.py spawns it
as a subprocess automatically.
"""
 
import calendar
import re
import sys
import os
import time
from urllib.parse import quote_plus
 
# Allow "from orchestrator..." / sibling-package imports to work when this
# file is launched as a standalone subprocess (its working dir is the
# backend/ folder, but Python's default path handling needs a little help).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
import pandas as pd
import yfinance as yf
import feedparser
from mcp.server.fastmcp import FastMCP

from utils.currency import infer_currency
from utils.tickers import base_symbol, news_edition, not_found_hint


mcp = FastMCP("financial-analysis-tools")

# Yahoo's `.info` is a slow network call and three tools want it (currency, fundamentals,
# company name), so it is fetched once per ticker and reused for a few minutes. This server
# process lives for the whole pipeline run, which is exactly the window the cache is for.
_INFO_TTL_SECONDS = 600
_info_cache: dict[str, tuple[float, dict]] = {}


def _info(ticker: str) -> dict:
    cached = _info_cache.get(ticker)
    if cached and time.monotonic() - cached[0] < _INFO_TTL_SECONDS:
        return cached[1]
    info = yf.Ticker(ticker).info or {}
    _info_cache[ticker] = (time.monotonic(), info)
    return info


def _currency(ticker: str) -> str:
    """The currency this ticker's prices are quoted in: Yahoo's own answer, else a guess from the suffix."""
    try:
        code = yf.Ticker(ticker).fast_info["currency"]
        if code:
            return str(code)
    except Exception:
        pass
    return infer_currency(ticker)


# "Tata Consultancy Services Limited" -> "Tata Consultancy Services": legal suffixes only add noise to a news search.
_LEGAL_SUFFIX = re.compile(r"[,\s]+(?:inc|incorporated|corporation|corp|limited|ltd|plc|co|company|n\.v|s\.a|ag|se)\.?$", re.I)


# News older than this says little about today's mood, and "Prediction for Tomorrow: 9 Oct" pages and
# stock-quote pages are SEO filler rather than news -- none of them should move the sentiment score.
_NEWS_MAX_AGE_DAYS = 14
_JUNK_HEADLINE = re.compile(r"prediction for tomorrow|stock price,? news,? quote", re.I)


def _is_fresh(entry) -> bool:
    published = getattr(entry, "published_parsed", None)
    if not published:
        return True                    # an undated item is kept rather than guessed stale
    return time.time() - calendar.timegm(published) <= _NEWS_MAX_AGE_DAYS * 86400


def _company_name(ticker: str) -> str | None:
    try:
        info = _info(ticker)
    except Exception:
        return None
    name = (info.get("longName") or info.get("shortName") or "").strip()
    while True:
        shorter = _LEGAL_SUFFIX.sub("", name)
        if shorter == name:
            break
        name = shorter
    return name or None
 
 
@mcp.tool()
def fetch_ohlcv(ticker: str, period: str = "1y") -> dict:
    """Fetch daily OHLCV (Open/High/Low/Close/Volume) price history for a ticker.
 
    Returns a JSON-serializable dict: {"dates": [...], "open": [...], ...}
    rather than a DataFrame, since MCP tool results travel over the wire
    as plain data.
    """
    df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No data returned for '{ticker}'. {not_found_hint(ticker)}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
 
    return {
        "ticker": ticker,
        "currency": _currency(ticker),
        "dates": [d.strftime("%Y-%m-%d") for d in df.index],
        "open": df["Open"].tolist(),
        "high": df["High"].tolist(),
        "low": df["Low"].tolist(),
        "close": df["Close"].tolist(),
        "volume": df["Volume"].tolist(),
    }
 
 
@mcp.tool()
def fetch_fundamentals(ticker: str) -> dict:
    """Fetch a few fundamental ratios for a ticker (P/E, ROE, profit margin).
    Missing fields come back as None rather than a guessed value -- not
    every ticker (e.g. ETFs) exposes every field."""
    info = _info(ticker)
    return {
        "ticker": ticker,
        "pe_ratio": info.get("trailingPE"),
        "roe": info.get("returnOnEquity"),
        "profit_margin": info.get("profitMargins"),
    }
 
 
@mcp.tool()
def fetch_news_headlines(ticker: str, max_headlines: int = 10) -> dict:
    """Fetch recent news headlines for a ticker from Google News RSS.

    Searches by company name when Yahoo knows it ("Tata Consultancy Services" stock) -- a bare
    exchange-suffixed symbol like TCS.NS also pulls in articles about its peers -- and uses the
    news edition of the stock's home market."""
    name = _company_name(ticker)
    query = f'"{name}" stock' if name else f"{base_symbol(ticker)} stock"
    query += f" when:{_NEWS_MAX_AGE_DAYS}d"                      # Google News's own "last N days" filter
    hl, gl, ceid = news_edition(ticker)
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl={hl}&gl={gl}&ceid={ceid}"
    feed = feedparser.parse(url)
 
    if feed.bozo and not feed.entries:
        raise ConnectionError(f"Could not fetch or parse the news feed for {ticker}")
 
    # The search filter isn't airtight, so check the dates too; also drop filler pages and repeats.
    headlines, seen = [], set()
    for entry in feed.entries:
        title = entry.title.strip()
        key = re.sub(r"\W+", " ", title.lower()).strip()
        if key in seen or _JUNK_HEADLINE.search(title) or not _is_fresh(entry):
            continue
        seen.add(key)
        headlines.append(title)
        if len(headlines) >= max_headlines:
            break
    if not headlines:
        raise ValueError(f"No headlines from the last {_NEWS_MAX_AGE_DAYS} days found for {ticker}")
 
    return {"ticker": ticker, "headlines": headlines}
 
 
if __name__ == "__main__":
    mcp.run()
 

