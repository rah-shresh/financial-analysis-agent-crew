"""
Agent 2 — Technical & Statistical Analyst (see spec.md)
 
Reads `price_data` from the shared state (written by the Preprocessor)
and writes `technical_metrics` — SMA/EMA snapshot, RSI, and a couple of
fundamental ratios pulled from yfinance.
 
If the Preprocessor failed, this agent does NOT try to fabricate numbers —
it records that it was skipped and why. This is the "never silently skip
a failed agent" rule from spec.md.
 
Phase 7 update: fundamentals now come through the MCP `fetch_fundamentals`
tool instead of a direct yfinance call. RSI/SMA/EMA stay exactly as before
— those are pure math on data already in `state['price_data']`, not an
external data source, so there's nothing for MCP to wrap there.
"""
 
import pandas as pd
 
from orchestrator.state import AgentState
from mcp_layer.client import call_tool
 
 
def _compute_rsi(close: pd.Series, period: int = 14) -> float:
    """Standard RSI (Relative Strength Index) over the given period."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
 
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
 
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])
 
 
def _fetch_fundamentals(ticker: str) -> dict:
    """Best-effort fetch of a couple of fundamental ratios, via the MCP
    `fetch_fundamentals` tool. Not all tickers expose all fields (e.g. ETFs
    don't have a P/E), so missing fields are reported as None rather than
    guessed — the tool itself handles that, this just drops the redundant
    `ticker` key the tool includes in its response."""
    result = call_tool("fetch_fundamentals", {"ticker": ticker})
    return {
        "pe_ratio": result.get("pe_ratio"),
        "roe": result.get("roe"),
        "profit_margin": result.get("profit_margin"),
    }
 
 
def technical_node(state: AgentState) -> AgentState:
    """LangGraph node: reads state['price_data'], writes state['technical_metrics']."""
    log = state.get("agent_log", [])
    ticker = state["ticker"]
 
    if state.get("price_data") is None:
        # Preprocessor failed — don't fabricate technical numbers, just skip honestly
        log.append("Technical Analyst \u2192 Skipped (no clean price data available)")
        return {
            **state,
            "technical_metrics": None,
            "technical_error": "Skipped: preprocessing failed, no data to analyze",
            "agent_log": log,
        }
 
    try:
        df = state["price_data"]
        latest = df.iloc[-1]
 
        metrics = {
            "latest_close": round(float(latest["Close"]), 2),
            "sma_20": round(float(latest["SMA_20"]), 2) if pd.notna(latest["SMA_20"]) else None,
            "ema_20": round(float(latest["EMA_20"]), 2) if pd.notna(latest["EMA_20"]) else None,
            "rsi_14": round(_compute_rsi(df["Close"]), 2),
            "trend": "above SMA (bullish bias)" if latest["Close"] > latest["SMA_20"] else "below SMA (bearish bias)",
        }
 
        try:
            metrics["fundamentals"] = _fetch_fundamentals(ticker)
        except Exception as fe:
            # Fundamentals are a "nice to have" — don't fail the whole agent over them
            metrics["fundamentals"] = None
            log.append(f"Technical Analyst \u2192 fundamentals unavailable ({fe})")
 
        log.append(f"Technical Analyst \u2192 Done (RSI {metrics['rsi_14']}, {metrics['trend']})")
        return {
            **state,
            "technical_metrics": metrics,
            "technical_error": None,
            "agent_log": log,
        }
    except Exception as e:
        log.append(f"Technical Analyst \u2192 Failed ({e})")
        return {
            **state,
            "technical_metrics": None,
            "technical_error": str(e),
            "agent_log": log,
        }
 










