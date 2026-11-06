"""The Monte Carlo fan (per-day percentile band) feeds the dashboard's risk chart."""
 
import numpy as np
import pandas as pd
 
from agents.risk_agent import MONTE_CARLO_HORIZON_DAYS, _run_monte_carlo
 
 
def test_fan_band_is_consistent_with_the_summary_numbers():
    rng = np.random.default_rng(1)
    close = pd.Series(100 + np.cumsum(rng.normal(0.1, 1.5, 250)))
    mc = _run_monte_carlo(close, close.pct_change().dropna())
    fan = mc["fan"]
 
    assert len(fan["p5"]) == len(fan["median"]) == len(fan["p95"]) == MONTE_CARLO_HORIZON_DAYS
    assert all(lo <= mid <= hi for lo, mid, hi in zip(fan["p5"], fan["median"], fan["p95"]))
    assert (fan["p95"][-1] - fan["p5"][-1]) > (fan["p95"][0] - fan["p5"][0])        # widens over time
    assert fan["p5"][-1] == mc["worst_case_5pct"] and fan["p95"][-1] == mc["best_case_95pct"]
 










