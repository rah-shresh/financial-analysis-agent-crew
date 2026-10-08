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
 
import sys
import os
 
# Allow "from orchestrator..." / sibling-package imports to work when this
# file is launched as a standalone subprocess (its working dir is the
# backend/ folder, but Python's default path handling needs a little help).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
import pandas as pd
import yfinance as yf
import feedparser
from mcp.server.fastmcp import FastMCP
 
 
mcp = FastMCP("financial-analysis-tools")
 
 
@mcp.tool()
def fetch_ohlcv(ticker: str, period: str = "1y") -> dict:
    """Fetch daily OHLCV (Open/High/Low/Close/Volume) price history for a ticker.
 
    Returns a JSON-serializable dict: {"dates": [...], "open": [...], ...}
    rather than a DataFrame, since MCP tool results travel over the wire
    as plain data.
    """
    df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No data returned for '{ticker}'. Check the ticker symbol is correct.")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
 
    return {
        "ticker": ticker,
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
    info = yf.Ticker(ticker).info
    return {
        "ticker": ticker,
        "pe_ratio": info.get("trailingPE"),
        "roe": info.get("returnOnEquity"),
        "profit_margin": info.get("profitMargins"),
    }
 
 
@mcp.tool()
def fetch_news_headlines(ticker: str, max_headlines: int = 10) -> dict:
    """Fetch recent news headlines for a ticker from Google News RSS."""
    url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
 
    if feed.bozo and not feed.entries:
        raise ConnectionError(f"Could not fetch or parse the news feed for {ticker}")
 
    headlines = [entry.title for entry in feed.entries[:max_headlines]]
    if not headlines:
        raise ValueError(f"No recent headlines found for {ticker}")
 
    return {"ticker": ticker, "headlines": headlines}
 
 
if __name__ == "__main__":
    mcp.run()
 

