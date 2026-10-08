"""
Phase 1 — First two agents, real orchestrator
================================================
Run the Preprocessor -> Technical Analyst chain via LangGraph and print
the result. This is the first proof that state genuinely flows between
agents instead of running two separate scripts.
 
Usage:
    python phase1_run_pipeline.py TSLA
"""
 
import sys
import json
from orchestrator.graph import run_analysis
 
 
def main():
    ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "TSLA"
 
    print(f"Running Phase 1 pipeline for {ticker}...\n")
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
 
 
if __name__ == "__main__":
    main()
 
