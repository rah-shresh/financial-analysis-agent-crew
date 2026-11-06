"""Users see the agent log, so internal MCP plumbing text must not leak into it."""
 
from services.report_builder import clean_log_line
 
 
def test_mcp_wrapper_is_stripped_but_the_real_reason_stays():
    raw = ("Preprocessor \u2192 Failed (MCP call_tool('fetch_ohlcv') failed: [RuntimeError] "
           "Error executing tool fetch_ohlcv: No data returned for 'ZZZZ'. Check the ticker symbol is correct.)")
    assert clean_log_line(raw) == ("Preprocessor \u2192 Failed (No data returned for 'ZZZZ'. "
                                   "Check the ticker symbol is correct.)")
 
 
def test_normal_lines_are_untouched():
    for line in ["Preprocessor \u2192 Done (251 rows cleaned)", "Risk \u2192 Monte Carlo done (2000 sims, 53.7% chance of loss in 30d)"]:
        assert clean_log_line(line) == line
 











