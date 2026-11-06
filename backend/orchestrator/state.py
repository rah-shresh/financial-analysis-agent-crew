"""
Shared state for the agent graph.
 
This is the single object that flows through every agent node. Each agent
reads what it needs from it and writes its own results back into it —
this is what makes it a real multi-agent pipeline instead of separate
scripts: one agent's output becomes the next agent's input.
"""
 
from typing import TypedDict, Optional, List
import pandas as pd
 
 
class AgentState(TypedDict, total=False):
    # ---- input ----
    ticker: str
 
    # ---- written by the Preprocessor agent ----
    price_data: Optional[pd.DataFrame]   # cleaned OHLCV + SMA/EMA
    currency: Optional[str]              # ISO code the prices are quoted in (USD, INR, ...)
    preprocessing_error: Optional[str]
 
    # ---- written by the Technical Analyst agent ----
    technical_metrics: Optional[dict]
    technical_error: Optional[str]

    # ---- written by the Sentiment agent ----
    sentiment: Optional[dict]
    sentiment_error: Optional[str]

    # ---- written by the Forecasting agent ----
    forecast: Optional[dict]
    forecast_error: Optional[str]

    # ---- written by the Risk agent ----
    risk: Optional[dict]
    risk_error: Optional[str]
 
    # ---- shared across all agents: a running log for the UI's
    #      "Agent Logs Panel" (see spec.md, Phase 9) ----
    agent_log: List[str]
 
