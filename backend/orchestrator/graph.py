"""
Phase 1 orchestrator.
 
This is intentionally the simplest possible LangGraph: two nodes, one
edge. Preprocessor -> Technical Analyst -> END. This is what proves
"multi-agent" is real — the state object is genuinely passed from one
agent to the next, not just two scripts run back to back.
 
More agents (Sentiment, Forecasting, Risk) get added to this same graph
in later phases, per spec.md.
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
 
