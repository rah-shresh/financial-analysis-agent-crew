"""
Markowitz Portfolio Optimization (Phase 6 upgrade)
 
This is deliberately NOT a node in the main per-ticker LangGraph chain.
Markowitz optimization answers a different question than the rest of
the pipeline: not "how healthy is this one stock?" but "given these
several stocks, what mix of them minimizes risk / maximizes return?"
That needs 2+ tickers' price histories at once, which the single-ticker
`AgentState` chain isn't built around -- forcing it in would mean
reshaping the whole state object for a feature that's conceptually a
separate request.
 
Usage (see phase6_portfolio_optimizer.py for the CLI entry point):
    result = optimize_portfolio(["TSLA", "AAPL", "MSFT"])
"""
 
import pandas as pd
import yfinance as yf
from pypfopt import EfficientFrontier, risk_models, expected_returns
 
 
def _fetch_close_prices(tickers: list[str], period: str = "1y") -> pd.DataFrame:
    """Fetch adjusted close prices for multiple tickers into one aligned DataFrame
    (columns = tickers, index = dates). Rows where ANY ticker is missing data
    are dropped, since Markowitz needs same-length, aligned return series."""
    # threads=False: yfinance's default multi-ticker download uses background
    # threads, which can hang when this runs inside the MCP server subprocess
    # (stdio transport). Sequential download is plenty fast for a handful of tickers.
    data = yf.download(tickers, period=period, interval="1d", progress=False,
                       auto_adjust=True, threads=False)
 
    if data.empty:
        raise ValueError(f"No data returned for tickers: {tickers}")
 
    # yfinance returns a MultiIndex column structure for multiple tickers
    close_prices = data["Close"] if "Close" in data.columns.get_level_values(0) else data
    close_prices = close_prices.dropna()
 
    if close_prices.empty:
        raise ValueError(
            "No overlapping trading days across all tickers after cleaning -- "
            "check that all ticker symbols are correct and actively traded."
        )
    return close_prices
 
 
def fetch_close_prices_via_mcp(tickers: list[str], period: str = "1y") -> pd.DataFrame:
    """Fetch each ticker's closing prices through the MCP `fetch_ohlcv` tool
    (the same tool the Preprocessor agent uses) and align them into one
    DataFrame. Only the *data download* goes through MCP; the Markowitz math
    below runs locally -- see PHASE7_README.md for why."""
    from mcp_layer.client import call_tool  # lazy: keeps this module importable without MCP
 
    closes = {}
    for ticker in tickers:
        result = call_tool("fetch_ohlcv", {"ticker": ticker, "period": period})
        closes[ticker] = pd.Series(result["close"], index=pd.to_datetime(result["dates"]))
 
    prices = pd.DataFrame(closes).dropna()
    if prices.empty:
        raise ValueError(
            "No overlapping trading days across all tickers after cleaning -- "
            "check that all ticker symbols are correct and actively traded."
        )
    return prices
 
 
def optimize_portfolio(tickers: list[str], period: str = "1y", prices: pd.DataFrame | None = None) -> dict:
    """
    Run Markowitz optimization for the given tickers.
    Returns both a max-Sharpe portfolio and a min-volatility portfolio,
    so the user can see the trade-off rather than just one "answer."
 
    `prices` can be supplied by the caller (e.g. fetched via MCP); if it's
    omitted, prices are downloaded directly from yfinance as before.
    """
    if len(tickers) < 2:
        raise ValueError(
            f"Markowitz optimization needs at least 2 tickers to have anything "
            f"to optimize between (got {tickers}). For a single ticker, use the "
            f"regular analysis pipeline (phase4_run_pipeline.py) instead."
        )
 
    if prices is None:
        prices = _fetch_close_prices(tickers, period=period)
 
    mu = expected_returns.mean_historical_return(prices)
    S = risk_models.sample_cov(prices)
 
    result = {
        "tickers": tickers,
        "period_used": period,
        "trading_days_used": len(prices),
    }
 
    # --- Max Sharpe portfolio ---
    # This can genuinely fail: if every asset's historical return is below
    # the risk-free rate (e.g. a broad downturn period), there's no
    # meaningful "max Sharpe" mix to find. That's a real market condition,
    # not a bug -- report it honestly rather than crashing the whole function.
    try:
        ef_sharpe = EfficientFrontier(mu, S)
        ef_sharpe.max_sharpe()
        sharpe_weights = ef_sharpe.clean_weights()
        sharpe_perf = ef_sharpe.portfolio_performance(verbose=False)
        result["max_sharpe_portfolio"] = {
            "weights": {k: round(v, 4) for k, v in sharpe_weights.items()},
            "expected_annual_return_pct": float(round(sharpe_perf[0] * 100, 2)),
            "annual_volatility_pct": float(round(sharpe_perf[1] * 100, 2)),
            "sharpe_ratio": float(round(sharpe_perf[2], 2)),
        }
    except ValueError as e:
        result["max_sharpe_portfolio"] = None
        result["max_sharpe_error"] = (
            f"Could not compute a max-Sharpe portfolio: {e}. This usually means "
            f"every selected stock underperformed the risk-free rate over this "
            f"period -- a real market condition, not a code error."
        )
 
    # --- Min volatility portfolio (needs a fresh EfficientFrontier instance) ---
    # This doesn't have the "beat the risk-free rate" requirement, so it
    # should succeed even when max_sharpe above can't.
    ef_minvol = EfficientFrontier(mu, S)
    ef_minvol.min_volatility()
    minvol_weights = ef_minvol.clean_weights()
    minvol_perf = ef_minvol.portfolio_performance(verbose=False)
    result["min_volatility_portfolio"] = {
        "weights": {k: round(v, 4) for k, v in minvol_weights.items()},
        "expected_annual_return_pct": float(round(minvol_perf[0] * 100, 2)),
        "annual_volatility_pct": float(round(minvol_perf[1] * 100, 2)),
        "sharpe_ratio": float(round(minvol_perf[2], 2)),
    }
 
    return result
 

