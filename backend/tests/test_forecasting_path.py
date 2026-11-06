"""The day-by-day forecast paths feed the dashboard's forecast chart."""
 
import numpy as np
import pandas as pd
 
from agents.forecasting_agent import FORECAST_DAYS, _fit_and_forecast, _fit_and_forecast_lstm
 
 
def _close(n=250, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2025-01-01", periods=n)
    idx.freq = None                                     # yfinance's index has no frequency
    return pd.Series(100 + np.cumsum(rng.normal(0.1, 1.5, n)), index=idx)
 
 
def test_arima_path_is_aligned_ordered_and_continues_the_series():
    close = _close()
    result = _fit_and_forecast(close)
    path = result["path"]
 
    assert len(path["dates"]) == len(path["arima"]) == len(path["ci_lower"]) == len(path["ci_upper"]) == FORECAST_DAYS
    dates = pd.to_datetime(path["dates"])
    assert dates[0] > close.index[-1] and dates.is_monotonic_increasing
    assert all(d.weekday() < 5 for d in dates)                      # weekdays only
    assert all(lo <= mid <= hi for lo, mid, hi in zip(path["ci_lower"], path["arima"], path["ci_upper"]))
    # the headline numbers are the last day of the path
    assert path["arima"][-1] == result["forecast_final_price"]
    assert path["ci_lower"][-1] == result["confidence_interval_95"]["lower"]
    # uncertainty widens with the horizon
    assert (path["ci_upper"][-1] - path["ci_lower"][-1]) > (path["ci_upper"][0] - path["ci_lower"][0])
 
 
def test_lstm_path_lines_up_with_arima_path():
    close = _close()
    lstm = _fit_and_forecast_lstm(close, sentiment_score=0.1)
    assert len(lstm["path"]) == FORECAST_DAYS
    assert lstm["path"][-1] == lstm["forecast_final_price"]
 











