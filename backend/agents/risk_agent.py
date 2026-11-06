"""
Agent 5 — Risk & Portfolio Optimization (see spec.md)
 
Phase 4 gave this agent Sharpe ratio + Value at Risk. This update
(Phase 6) adds **Monte Carlo simulation** as a third technique, still
single-ticker, so it slots into the existing chain with no architecture
change.
 
Markowitz multi-asset optimization is NOT in this file -- it genuinely
needs 2+ tickers to mean anything (there's nothing to "optimize" for a
single asset; its weight would trivially be 100%). It lives in a
separate module (`portfolio_optimizer.py`) with its own entry point,
since it's a different kind of request ("optimize a portfolio") than
what this per-ticker analysis chain does ("analyze one stock").
 
Depends on `price_data` from the Preprocessor.
"""
 
import numpy as np
import pandas as pd
 
from orchestrator.state import AgentState
from utils.currency import format_money, infer_currency
 
RISK_FREE_RATE_ANNUAL = 0.07  # approx. a safe benchmark (e.g. short-term govt bond yield)
TRADING_DAYS_PER_YEAR = 252
VAR_CONFIDENCE = 0.95
MONTE_CARLO_SIMULATIONS = 2000
MONTE_CARLO_HORIZON_DAYS = 30
 
 
def _compute_sharpe_ratio(daily_returns: pd.Series) -> float:
    """Annualized Sharpe ratio: (mean excess return / std dev of returns),
    scaled to a yearly figure since daily returns are tiny numbers."""
    daily_risk_free = RISK_FREE_RATE_ANNUAL / TRADING_DAYS_PER_YEAR
    excess_returns = daily_returns - daily_risk_free
 
    mean_excess = excess_returns.mean()
    std_excess = excess_returns.std()
 
    if std_excess == 0 or np.isnan(std_excess):
        return 0.0
 
    sharpe_daily = mean_excess / std_excess
    sharpe_annualized = sharpe_daily * np.sqrt(TRADING_DAYS_PER_YEAR)
    return float(sharpe_annualized)
 
 
def _compute_historical_var(daily_returns: pd.Series, confidence: float = VAR_CONFIDENCE) -> float:
    """Historical VaR: the loss threshold that returns don't exceed
    `confidence`% of the time, based on actual historical returns
    (no distribution assumption, unlike parametric VaR)."""
    # e.g. at 95% confidence, VaR is the 5th percentile of the return distribution
    percentile = (1 - confidence) * 100
    var_return = np.percentile(daily_returns.dropna(), percentile)
    return float(var_return)  # a negative number, e.g. -0.032 = a 3.2% one-day loss threshold
 
 
def _run_monte_carlo(close: pd.Series, daily_returns: pd.Series,
                      n_simulations: int = MONTE_CARLO_SIMULATIONS,
                      horizon_days: int = MONTE_CARLO_HORIZON_DAYS) -> dict:
    """Simulate many possible future price paths using Geometric Brownian
    Motion, parameterized from the stock's own historical mean return and
    volatility. This is a stress-test, not a prediction -- it answers
    "what's the range of plausible outcomes", not "what will happen."
    """
    mu = daily_returns.mean()       # historical average daily return (drift)
    sigma = daily_returns.std()     # historical daily volatility
    last_price = float(close.iloc[-1])
 
    rng = np.random.default_rng(seed=None)  # no fixed seed -- genuinely random each run
    # Generate all random shocks at once: shape (n_simulations, horizon_days)
    daily_shocks = rng.normal(loc=mu, scale=sigma, size=(n_simulations, horizon_days))
 
    # Each simulation is a cumulative product of (1 + daily_return) starting from last_price
    price_paths = last_price * np.cumprod(1 + daily_shocks, axis=1)
    final_prices = price_paths[:, -1]
 
    return {
        "simulations_run": n_simulations,
        "horizon_days": horizon_days,
        "starting_price": round(last_price, 2),
        "mean_final_price": round(float(np.mean(final_prices)), 2),
        "median_final_price": round(float(np.median(final_prices)), 2),
        "percentile_5": round(float(np.percentile(final_prices, 5)), 2),
        "percentile_95": round(float(np.percentile(final_prices, 95)), 2),
        "probability_of_loss_pct": round(float(np.mean(final_prices < last_price) * 100), 1),
        "worst_case_5pct": round(float(np.percentile(final_prices, 5)), 2),
        "best_case_95pct": round(float(np.percentile(final_prices, 95)), 2),
        # Per-day band across all simulations (day 1..horizon) for the fan chart.
        "fan": {
            "p5": [round(float(v), 2) for v in np.percentile(price_paths, 5, axis=0)],
            "median": [round(float(v), 2) for v in np.percentile(price_paths, 50, axis=0)],
            "p95": [round(float(v), 2) for v in np.percentile(price_paths, 95, axis=0)],
        },
    }
 
 
def risk_node(state: AgentState) -> AgentState:
    """LangGraph node: reads state['price_data'], writes state['risk']."""
    log = state.get("agent_log", [])
 
    if state.get("price_data") is None:
        log.append("Risk \u2192 Skipped (no clean price data available)")
        return {
            **state,
            "risk": None,
            "risk_error": "Skipped: preprocessing failed, no data to assess",
            "agent_log": log,
        }
 
    try:
        close = state["price_data"]["Close"]
        daily_returns = close.pct_change().dropna()
 
        if len(daily_returns) < 20:
            raise ValueError(f"Not enough data to assess risk reliably ({len(daily_returns)} days)")
 
        sharpe = _compute_sharpe_ratio(daily_returns)
        var_95_pct = _compute_historical_var(daily_returns, VAR_CONFIDENCE)
 
        latest_price = float(close.iloc[-1])
        var_95_dollar = round(latest_price * var_95_pct, 2)
        currency = state.get("currency") or infer_currency(state["ticker"])
 
        annualized_volatility = float(daily_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR))
 
        result = {
            "sharpe_ratio": round(sharpe, 2),
            "annualized_volatility_pct": round(annualized_volatility * 100, 2),
            "value_at_risk_95": {
                "daily_pct": round(var_95_pct * 100, 2),
                "daily_dollar_per_share": var_95_dollar,
                "interpretation": (
                    f"On 95% of trading days, a one-day loss is not expected to exceed "
                    f"{abs(round(var_95_pct * 100, 2))}% (~{format_money(abs(var_95_dollar), currency)} per share "
                    f"at the current price)."
                ),
            },
        }
 
        risk_label = "high" if annualized_volatility > 0.5 else ("moderate" if annualized_volatility > 0.25 else "low")
        result["risk_label"] = risk_label
 
        log.append(
            f"Risk \u2192 Done (Sharpe {result['sharpe_ratio']}, "
            f"volatility {risk_label}, VaR95 {result['value_at_risk_95']['daily_pct']}%)"
        )
 
        # Monte Carlo is a best-effort addition -- Sharpe/VaR above are
        # already complete and useful even if this part fails.
        try:
            mc_result = _run_monte_carlo(close, daily_returns)
            result["monte_carlo"] = mc_result
            log.append(
                f"Risk \u2192 Monte Carlo done ({mc_result['simulations_run']} sims, "
                f"{mc_result['probability_of_loss_pct']}% chance of loss in {mc_result['horizon_days']}d)"
            )
        except Exception as mc_error:
            result["monte_carlo"] = None
            log.append(f"Risk \u2192 Monte Carlo skipped ({mc_error})")
        return {
            **state,
            "risk": result,
            "risk_error": None,
            "agent_log": log,
        }
    except Exception as e:
        log.append(f"Risk \u2192 Failed ({e})")
        return {
            **state,
            "risk": None,
            "risk_error": str(e),
            "agent_log": log,
        }
 












