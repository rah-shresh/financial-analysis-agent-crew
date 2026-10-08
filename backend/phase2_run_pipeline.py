"""
Phase 2 — Sentiment agent added
================================================
Chain is now: Preprocessor -> Technical Analyst -> Sentiment -> END.
 
Usage:
    python phase2_run_pipeline.py TSLA
"""
 
import sys
import json
from orchestrator.graph import run_analysis
 
 
def main():
    ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "TSLA"
 
    print(f"Running Phase 2 pipeline for {ticker}...\n")
    final_state = run_analysis(ticker)
 
    print("=" * 55)
    print("AGENT LOG")
    print("=" * 55)
    for line in final_state.get("agent_log", []):
        print(" ", line)
 
    print("\n" + "=" * 55)
    print("TECHNICAL METRICS")
    print("=" * 55)
    metrics = final_state.get("technical_metrics")
    if metrics:
        print(json.dumps(metrics, indent=2, default=str))
    else:
        print("No metrics available:", final_state.get("technical_error"))
 
    print("\n" + "=" * 55)
    print("SENTIMENT")
    print("=" * 55)
    sentiment = final_state.get("sentiment")
    if sentiment:
        print(f"Score: {sentiment['score']:+.3f} ({sentiment['label']})")
        print("Headlines scored:")
        for h in sentiment["headlines"]:
            print(" -", h)
    else:
        print("No sentiment available:", final_state.get("sentiment_error"))
 
 
if __name__ == "__main__":
    main()
 










