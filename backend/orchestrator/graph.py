"""
Orchestrator — now at Phase 4 (all 5 agents).
 
Chain: Preprocessor -> Technical Analyst -> Sentiment -> Forecasting -> Risk -> END.
 
This completes the core 5-agent chain from spec.md. Phase 5 is the
"full pipeline checkpoint" -- run this end to end on a real ticker and
confirm every agent produces (or honestly skips) its part before moving
on to any advanced upgrades (LSTM, Monte Carlo, Markowitz, MCP).
"""
 
from langgraph.graph import StateGraph, END
 
from orchestrator.state import AgentState
from agents.preprocessor_agent import preprocessor_node
from agents.technical_agent import technical_node
from agents.sentiment_agent import sentiment_node
from agents.forecasting_agent import forecasting_node
from agents.risk_agent import risk_node
 
 
def build_graph():
    graph = StateGraph(AgentState)
 
    graph.add_node("preprocessor", preprocessor_node)
    graph.add_node("technical_analyst", technical_node)
    graph.add_node("sentiment", sentiment_node)
    graph.add_node("forecasting", forecasting_node)
    graph.add_node("risk", risk_node)
 
    graph.set_entry_point("preprocessor")
    graph.add_edge("preprocessor", "technical_analyst")
    graph.add_edge("technical_analyst", "sentiment")
    graph.add_edge("sentiment", "forecasting")
    graph.add_edge("forecasting", "risk")
    graph.add_edge("risk", END)
 
    return graph.compile()
 
 
def run_analysis(ticker: str) -> AgentState:
    """Run the full (current) pipeline for one ticker and return the final state."""
    app = build_graph()
    initial_state: AgentState = {"ticker": ticker.upper(), "agent_log": []}
    final_state = app.invoke(initial_state)
    return final_state
 
 
# Display/processing order of the agents (node names as registered above).
# The API uses this so a frontend can show queued / done agents.
AGENT_ORDER = ["preprocessor", "technical_analyst", "sentiment", "forecasting", "risk"]
 
 
def stream_analysis(ticker: str):
    """Run the pipeline and yield one {node_name: state} chunk as EACH agent
    finishes (LangGraph "updates" mode). Every node in this project returns
    the full state, so the last chunk's state is the final result. This is
    what lets the API save progress to the database mid-run instead of only
    at the end."""
    app = build_graph()
    initial_state: AgentState = {"ticker": ticker.upper(), "agent_log": []}
    yield from app.stream(initial_state, stream_mode="updates")
 










