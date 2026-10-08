"""
Agent 4 — Quantitative Forecasting (see spec.md)
 
Phase 3 gave this agent ARIMA. Phase 6 (this update) adds LSTM as a
**second, comparable model** — not a replacement. ARIMA stays the
primary/default forecast; the LSTM result is attached alongside it so
the two can be compared. If LSTM fails for any reason (e.g. a Windows
environment issue with TensorFlow, too little data, etc.), ARIMA's
result is still returned — the agent never fails just because the
optional upgrade did.
 
Steps (ARIMA, Phase 3):
1. ADF test for stationarity.
2. Fit ARIMA with a simple, fixed order.
3. Forecast 30 trading days with a 95% confidence interval.
 
Steps (LSTM, Phase 6 upgrade):
1. Scale the closing price to [0, 1].
2. Build sliding windows (20 days of history -> predict day 21).
3. Train a small 1-layer LSTM (kept deliberately small — this dataset
   is ~1 year of daily data, not enough to justify a deep network).
4. Forecast 30 days ahead iteratively (predict one day, feed it back in
   as if it were real, predict the next day, and so on).
5. The current sentiment score (if available) is included as a constant
   second input feature alongside price, per spec.md's original idea of
   using sentiment as an auxiliary signal.
 
Depends on `price_data` from the Preprocessor. If that's missing, this
agent skips honestly rather than guessing a forecast out of nowhere.
"""
 
import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
 
from orchestrator.state import AgentState
 
FORECAST_DAYS = 30
LSTM_WINDOW_SIZE = 20
LSTM_EPOCHS = 20
 
 
def _is_stationary(series: pd.Series, significance: float = 0.05) -> bool:
    """ADF test: null hypothesis is 'series has a unit root' (non-stationary).
    If p-value < significance, we reject the null -> series is stationary."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # silence the result_object FutureWarning
        result = adfuller(series.dropna())
    p_value = result[1]
    return p_value < significance
 
 
def _fit_and_forecast(close: pd.Series, steps: int = FORECAST_DAYS) -> dict:
    stationary = _is_stationary(close)
    d = 0 if stationary else 1
 
    # Small, fixed ARIMA order -- good enough for an MVP forecast.
    # (p, d, q) = (5, d, 0): a modest autoregressive component, no fancy tuning.
    order = (5, d, 0)
 
    # yfinance's DatetimeIndex has no explicit frequency set, which makes
    # statsmodels throw "No supported index is available." Fitting on a
    # plain integer index sidesteps that entirely -- we don't need date
    # labels on the forecast output anyway (see what _fit_and_forecast
    # returns: just prices and a percentage, no dates).
    close_for_fit = close.reset_index(drop=True)
 
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # statsmodels is chatty about convergence on short series
        model = ARIMA(close_for_fit, order=order)
        fitted = model.fit()
        forecast_result = fitted.get_forecast(steps=steps)
 
    forecast_mean = forecast_result.predicted_mean
    conf_int = forecast_result.conf_int(alpha=0.05)  # 95% confidence
 
    return {
        "stationary": stationary,
        "order_used": order,
        "forecast_days": steps,
        "last_actual_price": round(float(close.iloc[-1]), 2),
        "forecast_final_price": round(float(forecast_mean.iloc[-1]), 2),
        "forecast_change_pct": round(
            (float(forecast_mean.iloc[-1]) / float(close.iloc[-1]) - 1) * 100, 2
        ),
        "confidence_interval_95": {
            "lower": round(float(conf_int.iloc[-1, 0]), 2),
            "upper": round(float(conf_int.iloc[-1, 1]), 2),
        },
    }
 
 
def _fit_and_forecast_lstm(close: pd.Series, sentiment_score: float = 0.0, steps: int = FORECAST_DAYS) -> dict:
    """LSTM forecast, kept intentionally small and simple (see module docstring).
    Imports TensorFlow lazily so the ARIMA path above never pays the import
    cost (or risk) if this optional upgrade isn't being used."""
    # Lazy imports: keeps TensorFlow optional, and keeps startup fast for
    # anyone just using the ARIMA path.
    from sklearn.preprocessing import MinMaxScaler
    from tensorflow import keras
    from tensorflow.keras import layers
 
    prices = close.values.reshape(-1, 1)
    if len(prices) < LSTM_WINDOW_SIZE + 10:
        raise ValueError(f"Not enough data for an LSTM window of {LSTM_WINDOW_SIZE} days")
 
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(prices).flatten()
 
    # Build sliding windows: X = [sentiment, price_t..price_t+19] -> y = price_t+20
    X, y = [], []
    for i in range(LSTM_WINDOW_SIZE, len(scaled)):
        window = scaled[i - LSTM_WINDOW_SIZE:i]
        # sentiment is a single snapshot score, not a time series, so it's
        # broadcast as a constant extra feature alongside each price step
        features = np.column_stack([window, np.full(LSTM_WINDOW_SIZE, sentiment_score)])
        X.append(features)
        y.append(scaled[i])
    X, y = np.array(X), np.array(y)
 
    model = keras.Sequential([
        layers.Input(shape=(LSTM_WINDOW_SIZE, 2)),
        layers.LSTM(32),
        layers.Dense(1),
    ])
    model.compile(optimizer="adam", loss="mse")
    model.fit(X, y, epochs=LSTM_EPOCHS, batch_size=16, verbose=0)
 
    # Iteratively forecast `steps` days ahead: predict one day, append it
    # to the window, slide forward, predict the next day.
    current_window = scaled[-LSTM_WINDOW_SIZE:].copy()
    predictions_scaled = []
    for _ in range(steps):
        features = np.column_stack([current_window, np.full(LSTM_WINDOW_SIZE, sentiment_score)])
        next_scaled = model.predict(features.reshape(1, LSTM_WINDOW_SIZE, 2), verbose=0)[0, 0]
        predictions_scaled.append(next_scaled)
        current_window = np.append(current_window[1:], next_scaled)
 
    predictions = scaler.inverse_transform(np.array(predictions_scaled).reshape(-1, 1)).flatten()
 
    last_actual = float(close.iloc[-1])
    final_price = float(predictions[-1])
 
    return {
        "model": "LSTM",
        "window_size": LSTM_WINDOW_SIZE,
        "epochs": LSTM_EPOCHS,
        "sentiment_used_as_feature": sentiment_score,
        "forecast_final_price": round(final_price, 2),
        "forecast_change_pct": round((final_price / last_actual - 1) * 100, 2),
    }
 
 
def forecasting_node(state: AgentState) -> AgentState:
    """LangGraph node: reads state['price_data'], writes state['forecast']."""
    log = state.get("agent_log", [])
 
    if state.get("price_data") is None:
        log.append("Forecasting \u2192 Skipped (no clean price data available)")
        return {
            **state,
            "forecast": None,
            "forecast_error": "Skipped: preprocessing failed, no data to forecast",
            "agent_log": log,
        }
 
    try:
        close = state["price_data"]["Close"]
        result = _fit_and_forecast(close)
 
        direction = "up" if result["forecast_change_pct"] > 0 else "down"
        log.append(
            f"Forecasting \u2192 Done ({result['forecast_days']}-day ARIMA: "
            f"{direction} {abs(result['forecast_change_pct'])}%)"
        )
 
        # LSTM is a best-effort second opinion (Phase 6 upgrade). If it fails
        # for any reason, the ARIMA result above is still returned untouched.
        try:
            sentiment = state.get("sentiment")
            sentiment_score = sentiment["score"] if sentiment else 0.0
            lstm_result = _fit_and_forecast_lstm(close, sentiment_score=sentiment_score)
            result["lstm"] = lstm_result
            lstm_direction = "up" if lstm_result["forecast_change_pct"] > 0 else "down"
            log.append(
                f"Forecasting \u2192 LSTM done ({lstm_direction} {abs(lstm_result['forecast_change_pct'])}%)"
            )
        except Exception as lstm_error:
            result["lstm"] = None
            log.append(f"Forecasting \u2192 LSTM skipped ({lstm_error})")
 
        return {
            **state,
            "forecast": result,
            "forecast_error": None,
            "agent_log": log,
        }
    except Exception as e:
        log.append(f"Forecasting \u2192 Failed ({e})")
        return {
            **state,
            "forecast": None,
            "forecast_error": str(e),
            "agent_log": log,
        }
 










