"""
Agent 1 — Data Preprocessor (see spec.md)
 
Same fetch + clean logic as Phase 0 — now wrapped as a LangGraph node
function instead of a standalone script. It reads `ticker` from the
shared state and writes `price_data` (a cleaned DataFrame with SMA/EMA)
back into it for the next agent to use.
 
Phase 7 update: the data fetch no longer calls yfinance directly — it
goes through the MCP tool `fetch_ohlcv` instead (see mcp_layer/server.py
and mcp_layer/client.py). Everything below `_fetch_data` (cleaning,
indicators) is completely unchanged — this was a refactor of the data
*source*, not the logic.
"""
 
import pandas as pd
 
from orchestrator.state import AgentState
from mcp_layer.client import call_tool
from utils.currency import infer_currency


def _fetch_data(ticker: str, period: str = "1y") -> tuple[pd.DataFrame, str]:
    """Fetch OHLCV data via the MCP `fetch_ohlcv` tool and rebuild it as a
    DataFrame — the tool returns plain JSON-serializable lists (MCP results
    travel as data, not Python objects), so it's reconstructed here into
    the same shape the rest of this agent (and Phase 0-6) already expects.
    Also returns the currency the prices are quoted in."""
    result = call_tool("fetch_ohlcv", {"ticker": ticker, "period": period})
 
    df = pd.DataFrame(
        {
            "Open": result["open"],
            "High": result["high"],
            "Low": result["low"],
            "Close": result["close"],
            "Volume": result["volume"],
        },
        index=pd.to_datetime(result["dates"]),
    )
    df.index.name = "Date"
    return df, result.get("currency") or infer_currency(ticker)
 
 
def _clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.ffill().bfill()
 
    returns = df["Close"].pct_change()
    mean, std = returns.mean(), returns.std()
    z_scores = (returns - mean) / std
    outlier_mask = z_scores.abs() > 3
 
    if outlier_mask.sum() > 0:
        cap_upper = mean + 3 * std
        cap_lower = mean - 3 * std
        capped_returns = returns.clip(lower=cap_lower, upper=cap_upper)
        cleaned_close = df["Close"].copy()
        for i in range(1, len(cleaned_close)):
            if outlier_mask.iloc[i]:
                prev_price = cleaned_close.iloc[i - 1]
                cleaned_close.iloc[i] = prev_price * (1 + capped_returns.iloc[i])
        df["Close"] = cleaned_close
    return df
 
 
def _add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    return df
 
 
def preprocessor_node(state: AgentState) -> AgentState:
    """LangGraph node: reads state['ticker'], writes state['price_data']."""
    ticker = state["ticker"]
    log = state.get("agent_log", [])
 
    try:
        raw_df, currency = _fetch_data(ticker)
        clean_df = _clean_data(raw_df)
        enriched_df = _add_indicators(clean_df)
 
        log.append(f"Preprocessor \u2192 Done ({len(enriched_df)} rows cleaned)")
        return {
            **state,
            "price_data": enriched_df,
            "currency": currency,
            "preprocessing_error": None,
            "agent_log": log,
        }
    except Exception as e:
        log.append(f"Preprocessor \u2192 Failed ({e})")
        return {
            **state,
            "price_data": None,
            "currency": None,
            "preprocessing_error": str(e),
            "agent_log": log,
        }
 










