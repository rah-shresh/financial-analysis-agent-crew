"""
Phase 6, Part 2 — Markowitz Portfolio Optimization
=====================================================
Separate from the main per-ticker pipeline (phase4_run_pipeline.py).
This answers "what mix of these stocks is optimal?", not "how healthy
is this one stock?".
 
Phase 7 update: the price *download* goes through the MCP `fetch_ohlcv`
tool (an external data source, like everywhere else in the project).
The Markowitz *math* runs locally -- computation isn't wrapped by MCP,
same as RSI/ARIMA/Monte Carlo. (An MCP `optimize_portfolio` tool was
tried first and dropped: see PHASE7_README.md.)
 
Usage:
    python phase6_portfolio_optimizer.py TSLA AAPL MSFT
    python phase6_portfolio_optimizer.py TSLA AAPL MSFT GOOGL AMZN
"""
 
import sys
import json
from agents.portfolio_optimizer import fetch_close_prices_via_mcp, optimize_portfolio
 
 
def main():
    tickers = [t.upper() for t in sys.argv[1:]]
 
    if len(tickers) < 2:
        print("Please provide at least 2 tickers, e.g.:")
        print("  python phase6_portfolio_optimizer.py TSLA AAPL MSFT")
        sys.exit(1)
 
    print(f"Optimizing a portfolio of: {', '.join(tickers)}...")
 
    try:
        prices = fetch_close_prices_via_mcp(tickers)
        result = optimize_portfolio(tickers, prices=prices)
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        # str(e) can be empty for some exception types (e.g. certain
        # asyncio/anyio internals), which gives an unhelpfully blank
        # message -- always show the exception's type too so there's
        # something to debug from even when the message itself is empty.
        print(f"Portfolio optimization failed: [{type(e).__name__}] {e}")
        import traceback
        traceback.print_exc()
 
 
if __name__ == "__main__":
    main()
 

