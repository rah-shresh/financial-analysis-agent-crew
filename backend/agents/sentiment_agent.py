"""
Agent 3 — Sentiment & Market Intelligence (see spec.md)
 
Pulls recent headlines for the ticker from Google News RSS (free, no API
key, no rate-limit headaches) and scores them with TextBlob. Writes
`sentiment` into the shared state: an average polarity score (-1 to 1)
plus the headlines that were scored, so the UI can show "why" behind
the number.
 
Runs independently of the other agents — it only needs the ticker
symbol, not anything the Preprocessor or Technical Analyst produced.
If news fetching fails (no internet, feed down, etc.), it fails
honestly rather than inventing a neutral score and pretending that's
real data.
 
Phase 7 update: headline fetching goes through the MCP `fetch_news_headlines`
tool instead of calling feedparser directly. Scoring (TextBlob) is
unchanged — that's local computation, not an external data source.
"""
 
from textblob import TextBlob
 
from orchestrator.state import AgentState
from mcp_layer.client import call_tool
 
MAX_HEADLINES = 10
 
 
def _fetch_headlines(ticker: str) -> list[str]:
    """Pull recent headlines mentioning the ticker via the MCP
    `fetch_news_headlines` tool."""
    result = call_tool("fetch_news_headlines", {"ticker": ticker, "max_headlines": MAX_HEADLINES})
    return result["headlines"]
 
 
def _score_headlines(headlines: list[str]) -> float:
    """Average TextBlob polarity across all headlines, rounded to 3 decimals."""
    scores = [TextBlob(h).sentiment.polarity for h in headlines]
    return round(sum(scores) / len(scores), 3)
 
 
def _label(score: float) -> str:
    if score > 0.1:
        return "positive"
    if score < -0.1:
        return "negative"
    return "neutral"
 
 
def sentiment_node(state: AgentState) -> AgentState:
    """LangGraph node: reads state['ticker'], writes state['sentiment']."""
    log = state.get("agent_log", [])
    ticker = state["ticker"]
 
    try:
        headlines = _fetch_headlines(ticker)
        score = _score_headlines(headlines)
        label = _label(score)
 
        log.append(f"Sentiment \u2192 Done (score {score:+.2f}, {label}, {len(headlines)} headlines)")
        return {
            **state,
            "sentiment": {
                "score": score,
                "label": label,
                "headlines": headlines,
            },
            "sentiment_error": None,
            "agent_log": log,
        }
    except Exception as e:
        log.append(f"Sentiment \u2192 Failed ({e})")
        return {
            **state,
            "sentiment": None,
            "sentiment_error": str(e),
            "agent_log": log,
        }
 










