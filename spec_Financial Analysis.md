# Financial Analysis Agent Crew — Complete Project Specification

## 1. Project Title & Type
**Financial Analysis Agent Crew** — Multi-Agent AI System for Market & Investment Analysis
Type: AI-powered financial research and portfolio decision-support platform (agentic AI + quantitative finance)

## 2. Problem Statement
Individual investors and analysts need to combine several disconnected skills to evaluate a stock or portfolio: cleaning raw price data, computing technical/fundamental indicators, reading market sentiment from news, forecasting future price movement, and quantifying risk. Doing this manually is slow and inconsistent. This project automates the entire pipeline using a crew of cooperating AI agents, each responsible for one specialized task, coordinated by an orchestrator.

## 3. Objectives
- Build 5 specialized agents (Preprocessing, Technical Analysis, Sentiment, Forecasting, Risk/Portfolio) that each do one job well.
- Orchestrate them with LangGraph so they can run independently or as a full pipeline.
- Integrate MCP (Model Context Protocol) so agents share context/tools through a standard interface rather than hardcoded function calls.
- Produce a structured, explainable investment report (metrics + forecast + risk score) for a given stock/portfolio.
- Keep the entire stack free to build and deploy.

## 4. High-Level Architecture
```
                     ┌────────────┐
                     │    USER    │
                     └─────┬──────┘
                           │  "Analyze AAPL and optimize my portfolio"
                           ▼
                 ┌───────────────────┐
                 │   FastAPI Backend │
                 └─────────┬─────────┘
                           ▼
                 ┌───────────────────┐
                 │  Orchestrator      │  (LangGraph)
                 └─────────┬─────────┘
        ┌──────────┬───────┼────────┬───────────┐
        ▼          ▼       ▼        ▼           ▼
   Preprocessor  Technical Sentiment Forecasting  Risk/Portfolio
     Agent        Agent    Agent      Agent          Agent
        │          │        │          │              │
        └──────────┴────────┴──────────┴──────────────┘
                           ▼
                  ┌──────────────────┐
                  │  MCP Layer        │  (data/tool access: yfinance, news, math libs)
                  └──────────────────┘
                           ▼
                  ┌──────────────────┐
                  │  Report Generator │
                  └─────────┬─────────┘
                           ▼
                 ┌───────────────────┐
                 │ React Dashboard    │  (Vite + Tailwind + Zustand + Recharts)
                 └───────────────────┘
```

## 5. Tech Stack (100% Free Tier)

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3.11 | ML/data ecosystem, matches your existing skillset |
| Agent orchestration | LangGraph + LangChain | State graph for multi-agent flow, tool-calling |
| Context/tool protocol | MCP (Model Context Protocol) | Standardized way for agents to reach tools/data sources |
| LLM | Groq API (Llama 3) primary, Google Gemini API fallback | Both have generous free tiers; you've used both before |
| Market data | `yfinance` | Free, no key required, OHLCV + fundamentals |
| News/sentiment source | `feedparser` (Google News/Reuters RSS) | Free, unlimited, no auth |
| Sentiment analysis | `TextBlob` / `VADER` | Local, free, no API cost |
| Data processing | `pandas`, `numpy`, `scikit-learn` | Cleaning, imputation, feature selection |
| Technical indicators | `pandas-ta` | SMA/EMA/RSI etc., free |
| Time-series forecasting | `statsmodels` (ARIMA) | Free, classical baseline |
| Deep learning forecasting | TensorFlow/Keras (LSTM) | Free, trainable on Google Colab free GPU |
| Portfolio optimization | `PyPortfolioOpt` | Free, implements Markowitz/Efficient Frontier |
| Risk metrics | `numpy`/`scipy` (Sharpe, VaR, Monte Carlo) | Pure math, no dependency cost |
| Backend API | FastAPI | Async, lightweight, easy to deploy on Render free tier |
| Frontend | React (Vite) | Full control over the custom "analyst ledger" design; Vite gives fast dev reload |
| Styling | Tailwind CSS | Utility classes — no separate CSS files to hand-write per component |
| State management | Zustand | One small store file for auth + analysis state — far less boilerplate than Redux |
| API calls | Axios (single `api.js` with base URL + interceptor) | One place to attach the JWT token to every request — pages don't repeat fetch logic |
| Auth persistence | Zustand `persist` middleware | Login state survives refresh automatically, no manual localStorage code |
| Charts | Recharts | Pre-built LineChart/PieChart/AreaChart components — no custom SVG or D3 needed |
| Real-time agent progress | Socket.IO client | Live "agent running" updates without polling the API repeatedly |
| Icons | lucide-react | Consistent icon set, no separate icon-hunting |
| Frontend hosting | Vercel (free tier) | Auto-deploys from GitHub, zero server config |
| Database | MongoDB Atlas (free M0 tier) | Stores run history, reports, cached data |
| Caching | In-memory dict / local JSON (Redis optional, skip for free tier) | Avoids hitting rate limits repeatedly |
| Real-time server | FastAPI + python-socketio | Broadcasts agent-progress events to the connected React client |
| Deployment | Frontend: Vercel · Backend: Render · DB: MongoDB Atlas | All free tiers |
| Dev tooling | Claude Code | Used to accelerate agent/tool scaffolding |

## 6. Agent Specifications

### Agent 1 — Data Preprocessor
**Input:** Raw ticker symbol, date range
**Responsibilities:**
- Fetch OHLCV data via `yfinance`
- Handle missing values (mean/median imputation)
- Detect and treat outliers (Z-score + Winsorization)
- Normalize/scale features
**Output:** Clean pandas DataFrame passed to downstream agents

### Agent 2 — Technical & Statistical Analyst
**Input:** Cleaned price data
**Responsibilities:**
- Compute SMA/EMA (20/50/200-day), RSI, MACD
- Compute descriptive stats (mean, std dev, variance)
- Pull fundamental ratios (P/E, ROE, profit margin) via `yfinance`
- Compute correlation/covariance vs. a market index
**Output:** JSON of computed metrics

### Agent 3 — Sentiment & Market Intelligence
**Input:** Ticker/company name
**Responsibilities:**
- Pull recent headlines via RSS (Google News/Reuters)
- Run `TextBlob`/`VADER` polarity scoring
- Label sentiment positive/negative/neutral, aggregate a daily score
**Output:** Sentiment score (-1 to 1) + top headlines

### Agent 4 — Quantitative Forecasting
**Input:** Cleaned price data + sentiment score
**Responsibilities (core, build first):**
- Run ADF test for stationarity, decompose trend/seasonality
- Fit ARIMA for short-term baseline forecast — this is the only forecasting model required for the agent to count as "working"
**Responsibilities (later upgrade, only after ARIMA works end-to-end):**
- Fit LSTM for sequence-based forecast (uses sentiment as an auxiliary feature) — swap in as a second, comparable model, not a replacement dependency for the pipeline to function
**Output:** Predicted price trajectory (e.g., next 30 days) with confidence range

### Agent 5 — Risk & Portfolio Optimization
**Input:** Historical returns of selected assets, forecasted returns
**Responsibilities (core, build first):**
- Compute Sharpe ratio, Alpha, Beta
- Compute Value at Risk (95% confidence) using the historical/parametric method (closed-form, no simulation)
**Responsibilities (later upgrade, only after the above works end-to-end):**
- Run Markowitz optimization (max Sharpe / min volatility) via `PyPortfolioOpt` — only meaningful once you're analyzing 2+ assets together
- Run Monte Carlo simulation (Geometric Brownian Motion) for stress-testing
**Output:** Optimized asset weights, VaR, risk score (0–100)

### Orchestrator (LangGraph)
- Routes user query to relevant agents (not all queries need all 5 agents)
- Manages shared state object passed between agent nodes
- Handles agent failure gracefully (skip failed agent, note it in final report, never fabricate missing output)

### MCP Integration Layer
- Wraps each data/tool source (yfinance, RSS feed, PyPortfolioOpt, LLM call) as an MCP tool
- Agents call tools through the MCP interface instead of importing libraries directly — this is what makes them "MCP-integrated" for the resume claim
- Benefit: any agent can discover and call any registered tool without hardcoded imports, and tools can be swapped/upgraded independently
- **Build order note:** implement this last (see Phase 7 below), after each agent already works with direct library calls. Introducing MCP at the same time as the core agent logic doubles the number of things that can break at once.

## 7. Database Schema (MongoDB Atlas)

**users** — `{ _id, name, email, password_hash, created_at }`
**analysis_runs** — `{ _id, user_id, ticker, agents_used[], status, created_at, completed_at }`
**agent_outputs** — `{ _id, run_id, agent_name, input, output, duration_ms, status, error }`
**reports** — `{ _id, run_id, summary, metrics, forecast, risk_score, recommendations, generated_at }`
**cached_market_data** — `{ _id, ticker, date_range, data, fetched_at }` (avoids re-hitting yfinance)

## 8. API Endpoints (FastAPI)

```
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me

POST /api/analysis/run          # body: { ticker, agents: [...] }
GET  /api/analysis/{run_id}     # status + progress
GET  /api/analysis/{run_id}/report   # final report

GET  /api/reports               # list past reports for a user
GET  /api/reports/{id}

GET  /api/health
```

## 9. Frontend / Dashboard (React)

**Structure:** Single-page app, React Router for navigation, Zustand for auth + analysis state, Axios for all API calls (one `api.js` file with the JWT attached via interceptor — no per-page fetch boilerplate).

**Pages:**
- **`/login`, `/register`** — simple forms, JWT stored via Zustand `persist` (auto-survives refresh)
- **`/` (New Analysis)** — enter ticker(s), pick which agents to run, submit
- **`/analysis/:runId` (Live Progress)** — the page that must visibly show this is a *multi-agent system*, not a single input→output box. Contents:
  - **Agent Logs Panel** — one line per agent, updated live via Socket.IO as each finishes, e.g.:
    ```
    Preprocessor      → Done (412 rows cleaned)
    Technical Analyst → Done (RSI 58, SMA20 > SMA50)
    Sentiment Agent    → Done (score +0.65)
    Forecast Agent     → Running…
    Risk Agent         → Queued
    ```
  - Loading-state copy per stage while it's active: "Fetching data…", "Analyzing sentiment…", "Running forecast…", "Computing risk…" — not a single generic spinner for the whole run
  - Status badges (queued / running / done / failed) next to each agent name
- **`/reports/:id` (Report View)** — organized as **tabs**, not one long scroll, so each agent's output has its own space:
  - **Overview tab** — structured summary card (not plain text), e.g.:
    ```
    Stock: TSLA
    Risk: Medium
    30-day forecast: +7%
    Recommendation: Hold / below-benchmark position size
    ```
  - **Technical tab** — price chart with SMA/EMA overlays (Recharts `LineChart`), fundamental ratios as small stat cards
  - **Sentiment tab** — sentiment gauge + recent headlines list
  - **Prediction tab** — forecast chart, actual vs. predicted with a shaded confidence band (Recharts `AreaChart`)
  - **Portfolio tab** — Sharpe ratio, VaR, Monte Carlo fan chart (once Phase 6 is built), portfolio weights pie chart (Recharts `PieChart`, once multi-asset support exists)
- **`/history`** — list of past runs (from `GET /api/reports`), click through to any report

**Design direction:** the "analyst's ledger" aesthetic already prototyped (ruled lines, serif headings, monospace figures, ink/stamp accent colors) rather than a generic SaaS dashboard template — build this with Tailwind utility classes directly, no component library needed for the visual style. Structured cards (Overview, per-tab stat cards) and the Agent Logs Panel are what make the UI visibly match a multi-agent backend instead of looking like a single-box input/output tool — treat these as required, not optional polish.

**Build order within Phase 9:** New Analysis page → Agent Logs Panel on the Live Progress page (this is the highest-impact piece per the feedback above) → tabbed Report View → History. Don't build the pie/fan charts before the Agent Logs Panel exists — the live multi-agent feel matters more than any single chart.

## 10. Folder Structure
```
financial-analysis-crew/
├── backend/
│   ├── agents/
│   │   ├── preprocessor_agent.py
│   │   ├── technical_agent.py
│   │   ├── sentiment_agent.py
│   │   ├── forecasting_agent.py
│   │   └── risk_portfolio_agent.py
│   ├── orchestrator/
│   │   ├── graph.py            # LangGraph state graph
│   │   └── state.py
│   ├── mcp/
│   │   ├── tools_registry.py
│   │   ├── yfinance_tool.py
│   │   ├── news_tool.py
│   │   └── portfolio_tool.py
│   ├── realtime/
│   │   └── socket_server.py     # emits agent-progress events
│   ├── database/
│   │   ├── models.py
│   │   └── db.py
│   ├── api/
│   │   ├── auth.py
│   │   ├── analysis.py
│   │   └── reports.py
│   ├── config.py
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AgentProgress.jsx
│   │   │   ├── AgentLogsPanel.jsx   # live per-agent log lines
│   │   │   ├── SummaryCard.jsx       # structured Overview card
│   │   │   ├── Tabs.jsx              # Overview/Technical/Sentiment/Prediction/Portfolio
│   │   │   ├── PriceChart.jsx
│   │   │   ├── ForecastChart.jsx
│   │   │   ├── RiskPanel.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── NewAnalysis.jsx
│   │   │   ├── LiveProgress.jsx
│   │   │   ├── ReportView.jsx
│   │   │   └── History.jsx
│   │   ├── store/
│   │   │   ├── authStore.js     # Zustand, persisted
│   │   │   └── analysisStore.js
│   │   ├── services/
│   │   │   ├── api.js           # Axios instance + JWT interceptor
│   │   │   └── socket.js        # Socket.IO client
│   │   └── App.jsx
│   └── package.json
├── data/
│   └── cache/
├── tests/
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## 11. Development Phases

**Guiding rule: build in layers, not all at once.** Each phase below must run and produce a visible result on its own before you start the next one. Do not open a new phase's files until the previous phase's output is something you can point to and explain. "First make it work, then make it smart" — not the reverse.

- **Phase 0 — Foundation (no agents, no orchestration):** Plain Python script that fetches OHLCV data for one ticker via `yfinance`, cleans it, and prints/plots basic price + SMA/EMA. No LangGraph yet. This proves the data layer works before any agent logic sits on top of it.
- **Phase 1 — First two agents, real orchestrator:** Wrap the Phase 0 logic into a Preprocessor agent and a Technical Analyst agent. Connect them with the simplest possible LangGraph chain (2 nodes, one edge). This is the actual proof that "multi-agent" is real, not just separate scripts — the orchestrator must genuinely pass state between the two nodes.
- **Phase 2 — Add Sentiment agent:** Extend the chain to 3 nodes. Validate that sentiment output actually reaches the shared state the other agents can see.
- **Phase 3 — Add Forecasting agent (ARIMA only):** Do not touch LSTM yet. Get a working, explainable ARIMA forecast flowing through the chain end-to-end first.
- **Phase 4 — Add Risk agent (Sharpe + VaR only):** Skip Monte Carlo and Markowitz for now. A single-asset Sharpe ratio and VaR calculation is enough to complete the 5-agent chain.
- **Phase 5 — Full pipeline checkpoint:** All 5 agents connected, one ticker, one end-to-end run producing a report. This is your first genuinely demoable version — do not skip straight to advanced features from here without this checkpoint working cleanly.
- **Phase 6 — Advanced upgrades (optional, time-permitting):** LSTM as a second forecasting option, Monte Carlo simulation, Markowitz multi-asset optimization. Add these only after Phase 5 is solid.
- **Phase 7 — MCP integration:** Wrap the existing tool calls (yfinance, RSS, PyPortfolioOpt) behind the MCP interface. Do this last, once the direct-import version already works — MCP should be a refactor of working code, not something you debug at the same time as the agent logic itself.
- **Phase 8 — Persistence & API:** FastAPI backend + MongoDB Atlas (users, runs, reports).
- **Phase 9 — Dashboard:** React frontend (Vite + Tailwind + Zustand + Recharts + Socket.IO client) — build against the already-working API from Phase 8, page by page (New Analysis → Live Progress → Report View → History), not all at once.
- **Phase 10 — Deploy:** Render (backend) + Vercel (frontend) + MongoDB Atlas (DB), then full end-to-end test on the deployed URL.

**Common failure mode to avoid:** building all 5 agents' advanced logic (LSTM, Monte Carlo, full MCP) before a single end-to-end run works. If you get stuck, the fix is almost always to cut scope back to the last phase that worked, not to add more.

## 12. Security Requirements
- Passwords hashed with bcrypt
- JWT for session auth
- All API keys (Groq, Gemini) in `.env`, never committed
- `.gitignore` excludes `.env`, `__pycache__/`, cached data dumps
- Input validation on ticker symbols and date ranges (prevent injection into external API calls)
- Rate-limit the `/analysis/run` endpoint to avoid hammering free-tier data sources

## 13. AI Safety / Disclaimers
- Every report must state it is for educational/informational purposes, not financial advice
- Forecasts must show confidence intervals, not single-point guarantees
- Clearly separate "computed fact" (e.g., current P/E ratio) from "model prediction" (e.g., 30-day forecast)
- If an agent fails, the report says so explicitly rather than silently omitting that section

## 14. Testing
- **Unit tests:** SMA/EMA calculation, Sharpe ratio formula, VaR formula, imputation logic
- **Agent tests:** feed known input → verify expected output shape/range for each agent
- **Orchestration tests:** verify partial-agent runs (e.g., only Technical + Risk requested) work correctly
- **API tests:** register/login, run analysis, fetch report

## 15. End-to-End Example Flow
User submits: *"Analyze TSLA and give me a risk-adjusted view."*
1. Orchestrator selects: Preprocessor → Technical → Sentiment → Forecasting → Risk
2. Preprocessor fetches & cleans TSLA OHLCV data
3. Technical Analyst computes SMA/EMA/RSI + fundamental ratios
4. Sentiment Agent scores latest TSLA news headlines
5. Forecasting Agent runs ARIMA + LSTM using cleaned data + sentiment score, predicts 30-day trend
6. Risk Agent computes Sharpe ratio, VaR (95%), runs Monte Carlo simulation
7. Report Generator compiles everything into one structured report with a plain-language summary
8. React dashboard renders charts + summary (live-updated via Socket.IO during the run); report is saved to MongoDB for history

## 16. Resume-Ready Feature List (once built)
- Multi-agent architecture with LangGraph orchestration
- MCP-based tool/context sharing across agents
- Technical + fundamental + sentiment + forecasting + risk analysis pipeline
- Automated, structured investment reports with risk scoring
- Real-time agent-progress streaming via Socket.IO to a custom React dashboard
- Full free-tier deployment (Render + Vercel + MongoDB Atlas)
