"""
Phase 4 — Risk agent added (Sharpe + VaR only)
================================================
Chain is now the full 5 agents: Preprocessor -> Technical Analyst ->
Sentiment -> Forecasting -> Risk -> END.
 
Running this successfully end to end on a real ticker is also the
Phase 5 "full pipeline checkpoint" from spec.md -- there's no separate
code for Phase 5, just confirmation that this chain works cleanly
before moving on to any advanced upgrades.
 
Usage:
    python phase4_run_pipeline.py TSLA
"""
 
import sys
import json
from orchestrator.graph import run_analysis
 
 
def main():
    ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "TSLA"
 
    print(f"Running full pipeline for {ticker}...\n")
    final_state = run_analysis(ticker)
 
    print("=" * 55)
    print("AGENT LOG")
    print("=" * 55)
    for line in final_state.get("agent_log", []):
        print(" ", line)
 
    sections = [
        ("TECHNICAL METRICS", "technical_metrics", "technical_error"),
        ("SENTIMENT", "sentiment", "sentiment_error"),
        ("FORECAST (ARIMA, 30-day)", "forecast", "forecast_error"),
        ("RISK (Sharpe + VaR)", "risk", "risk_error"),
    ]
    for title, data_key, error_key in sections:
        print("\n" + "=" * 55)
        print(title)
        print("=" * 55)
        data = final_state.get(data_key)
        if data:
            print(json.dumps(data, indent=2, default=str))
        else:
            print("Not available:", final_state.get(error_key))
 
 
if __name__ == "__main__":
    main()
 
