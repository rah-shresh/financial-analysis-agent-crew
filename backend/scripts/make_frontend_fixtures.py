"""
Regenerates the frontend's test fixtures from the REAL backend, so the
dashboard is tested against what the API genuinely returns (null SMA values,
forecast paths, Monte Carlo fans...) instead of hand-written JSON that could
drift from reality.
 
Real LangGraph pipeline, real ARIMA/LSTM/Monte Carlo, in-memory fake MongoDB;
only the three network calls (prices / fundamentals / news) are faked.
 
    python scripts/make_frontend_fixtures.py
"""
 
import json
import sys
from pathlib import Path
from unittest.mock import patch
 
BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
OUT = BACKEND.parent / "frontend" / "src" / "test" / "fixtures"
OUT.mkdir(parents=True, exist_ok=True)
 
import mongomock                                      # noqa: E402
import numpy as np                                    # noqa: E402
import pandas as pd                                   # noqa: E402
from fastapi.testclient import TestClient             # noqa: E402
 
from config import settings                           # noqa: E402
 
settings.jwt_secret = "fixture-generation-secret-" * 2
settings.mongodb_uri = "mongomock://fixtures"
 
from api.analysis import run_to_public                # noqa: E402
from database import db as dbmod                      # noqa: E402
from services import run_executor                     # noqa: E402
 
rng = np.random.default_rng(11)
N = 251
DATES = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2025-10-01", periods=N)]
CLOSE = (300 + np.cumsum(rng.normal(0.25, 3, N))).tolist()
OHLCV = {"ticker": "TSLA", "currency": "USD", "dates": DATES, "open": CLOSE, "high": [c + 1 for c in CLOSE],
         "low": [c - 1 for c in CLOSE], "close": CLOSE, "volume": [1_000_000] * N}
FUND = {"ticker": "TSLA", "pe_ratio": 45.2, "roe": 0.1243, "profit_margin": 0.0871}
NEWS = {"ticker": "TSLA", "headlines": [
    "Tesla stock jumps 5% on better-than-expected deliveries report - CNBC",
    "Analysts split on near-term margin outlook for Tesla - Reuters",
    "Regulators open new probe into driver-assistance claims - Bloomberg",
    "Why Tesla (TSLA) stock is trading up today - Yahoo Finance",
]}
 
 
def fake_call_tool(name, args, **kw):
    return {"fetch_ohlcv": OHLCV, "fetch_fundamentals": FUND, "fetch_news_headlines": NEWS}[name]
 
 
def failing_call_tool(name, args, **kw):
    if name == "fetch_ohlcv":
        raise RuntimeError("MCP call_tool('fetch_ohlcv') failed: [RuntimeError] Error executing tool "
                           "fetch_ohlcv: No data returned for 'ZZZZ'. Check the ticker symbol is correct.")
    if name == "fetch_news_headlines":
        raise RuntimeError("MCP call_tool('fetch_news_headlines') failed: [RuntimeError] no headlines")
    return fake_call_tool(name, args)
 
 
def dump(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, allow_nan=False), encoding="utf-8")
    print(f"  wrote {name}")
 
 
def new_client():
    mdb = mongomock.MongoClient(tz_aware=True)["fixtures"]
    dbmod.ensure_indexes(mdb)
    dbmod.set_db(mdb)
    import main
    return TestClient(main.app), mdb
 
 
def patched(call_tool):
    return (patch("agents.preprocessor_agent.call_tool", side_effect=call_tool),
            patch("agents.technical_agent.call_tool", side_effect=call_tool),
            patch("agents.sentiment_agent.call_tool", side_effect=call_tool))
 
 
def register(client):
    r = client.post("/api/auth/register", json={"name": "Fixture User", "email": "f@example.com", "password": "fixture-password"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
 
 
print("Scenario 1: successful run (real pipeline)")
real_stream = run_executor.stream_analysis
snapshot = {}
 
 
def stream_with_snapshot(ticker):
    for i, chunk in enumerate(real_stream(ticker)):
        yield chunk
        if i == 1:   # progress for the first two agents is saved by now -> genuine mid-run state
            doc = mdb.analysis_runs.find_one({})
            snapshot["run"] = json.loads(run_to_public(doc).model_dump_json())
 
 
a, b, c = patched(fake_call_tool)
with a, b, c, patch.object(run_executor, "stream_analysis", stream_with_snapshot):
    client, mdb = new_client()
    with client:
        h = register(client)
        run = client.post("/api/analysis/run", json={"ticker": "TSLA"}, headers=h).json()
        completed = client.get(f"/api/analysis/{run['id']}", headers=h).json()
        report = client.get(f"/api/reports/{completed['report_id']}", headers=h).json()
        listing = client.get("/api/reports", headers=h).json()
 
assert completed["status"] == "completed" and snapshot["run"]["status"] == "running"
dump("run_completed.json", completed)
dump("run_running.json", snapshot["run"])
dump("report.json", report)
dump("reports_list.json", listing)
 
print("Scenario 2: failed run (bad ticker)")
a, b, c = patched(failing_call_tool)
with a, b, c:
    run_executor.stream_analysis = real_stream
    client, mdb = new_client()
    with client:
        h = register(client)
        run = client.post("/api/analysis/run", json={"ticker": "ZZZZ"}, headers=h).json()
        failed = client.get(f"/api/analysis/{run['id']}", headers=h).json()
assert failed["status"] == "failed"
dump("run_failed.json", failed)
print("done")
 













