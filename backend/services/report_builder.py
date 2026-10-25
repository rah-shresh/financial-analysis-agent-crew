"""
Turns the final agent state into the report document stored in MongoDB.
 
The written summary is built from rules over the actual numbers -- no
LLM involved yet, so it can't invent anything. It states what the agents
found and flags the caveats (model disagreement, wide ranges, a crude
sentiment scorer). It deliberately does NOT produce buy/sell/hold advice.
"""
 
import math
from datetime import datetime, timezone
from typing import Any
 
import numpy as np
 
DISCLAIMER = (
    "For educational and informational purposes only. This is not financial advice. "
    "Forecasts are statistical estimates with wide uncertainty, not predictions of what will happen."
)
 
 
def to_jsonable(obj: Any) -> Any:
    """Recursively convert numpy scalars / NaN / inf / tuples into plain
    JSON- and BSON-safe values (NaN and inf are not valid JSON)."""
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, np.generic):
        obj = obj.item()
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj
 
 
def _price_series(df) -> dict:
    """Compact series the dashboard can chart: dates, close, SMA-20, EMA-20."""
    return to_jsonable({
        "dates": [d.strftime("%Y-%m-%d") for d in df.index],
        "close": [round(float(v), 2) for v in df["Close"]],
        "sma_20": df["SMA_20"].round(2).tolist(),
        "ema_20": df["EMA_20"].round(2).tolist(),
    })
 
 
def _rsi_zone(rsi: float) -> str:
    if rsi >= 70:
        return "overbought territory"
    if rsi <= 30:
        return "oversold territory"
    return "the neutral range"
 
 
def build_overview(state: dict) -> dict:
    """The few headline signals for the dashboard's Overview card."""
    tech, sent, fc, risk = (state.get(k) for k in ("technical_metrics", "sentiment", "forecast", "risk"))
    overview: dict[str, Any] = {"ticker": state["ticker"]}
    if tech:
        overview.update(latest_close=tech["latest_close"], trend=tech["trend"], rsi_14=tech["rsi_14"])
    if sent:
        overview.update(sentiment_label=sent["label"], sentiment_score=sent["score"])
    if fc:
        overview["forecast_arima_pct"] = fc["forecast_change_pct"]
        lstm = fc.get("lstm")
        if lstm:
            overview["forecast_lstm_pct"] = lstm["forecast_change_pct"]
            overview["forecast_models_agree"] = (fc["forecast_change_pct"] > 0) == (lstm["forecast_change_pct"] > 0)
    if risk:
        overview.update(
            risk_label=risk["risk_label"],
            sharpe_ratio=risk["sharpe_ratio"],
            var_95_daily_pct=risk["value_at_risk_95"]["daily_pct"],
        )
        mc = risk.get("monte_carlo")
        if mc:
            overview["probability_of_loss_30d_pct"] = mc["probability_of_loss_pct"]
    return to_jsonable(overview)
 
 
def build_summary(state: dict) -> str:
    t = state["ticker"]
    tech, sent, fc, risk = (state.get(k) for k in ("technical_metrics", "sentiment", "forecast", "risk"))
    parts = []
 
    if tech:
        direction = "above" if "above" in tech["trend"] else "below"
        parts.append(
            f"{t} last closed at ${tech['latest_close']:.2f}, {direction} its 20-day average "
            f"(${tech['sma_20']:.2f}), and RSI of {tech['rsi_14']:.1f} sits in {_rsi_zone(tech['rsi_14'])}."
        )
    if sent:
        parts.append(
            f"Across {len(sent['headlines'])} recent headlines, news sentiment scores {sent['score']:+.2f} "
            f"({sent['label']}). Note: this scorer is a simple word-based model and often under-reads "
            f"financial headlines, so treat it as a rough signal."
        )
    if fc:
        ci = fc["confidence_interval_95"]
        line = (
            f"Over the next {fc['forecast_days']} trading days, ARIMA projects {fc['forecast_change_pct']:+.1f}% "
            f"(95% range ${ci['lower']:.0f}-${ci['upper']:.0f})"
        )
        lstm = fc.get("lstm")
        if lstm:
            agree = (fc["forecast_change_pct"] > 0) == (lstm["forecast_change_pct"] > 0)
            line += (
                f", while LSTM projects {lstm['forecast_change_pct']:+.1f}% "
                f"- the two models {'agree' if agree else 'disagree'} on direction"
            )
        parts.append(line + ". The range is wide: treat the numbers as scenarios, not predictions.")
    if risk:
        text = (
            f"Annualized volatility is {risk['annualized_volatility_pct']:.1f}% ({risk['risk_label']}), "
            f"the Sharpe ratio is {risk['sharpe_ratio']:.2f}, and historically a one-day loss has not "
            f"exceeded {abs(risk['value_at_risk_95']['daily_pct']):.1f}% on 95% of days."
        )
        mc = risk.get("monte_carlo")
        if mc:
            text += (
                f" Monte Carlo simulation puts the chance of a lower price after "
                f"{mc['horizon_days']} days at {mc['probability_of_loss_pct']:.0f}%."
            )
        parts.append(text)
 
    return " ".join(parts) if parts else "No analysis sections were available for this run."
 
 
def build_report(state: dict, run_id: str, user_id: str) -> dict:
    errors = {
        agent: msg
        for agent, msg in (
            ("preprocessor", state.get("preprocessing_error")),
            ("technical_analyst", state.get("technical_error")),
            ("sentiment", state.get("sentiment_error")),
            ("forecasting", state.get("forecast_error")),
            ("risk", state.get("risk_error")),
        )
        if msg
    }
    return {
        "run_id": run_id,
        "user_id": user_id,
        "ticker": state["ticker"],
        "created_at": datetime.now(timezone.utc),
        "overview": build_overview(state),
        "summary": build_summary(state),
        "technical": to_jsonable(state.get("technical_metrics")),
        "sentiment": to_jsonable(state.get("sentiment")),
        "forecast": to_jsonable(state.get("forecast")),
        "risk": to_jsonable(state.get("risk")),
        "price_series": _price_series(state["price_data"]),
        "agent_log": list(state.get("agent_log", [])),
        "errors": errors,
        "disclaimer": DISCLAIMER,
    }
 










