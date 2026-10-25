"""
API tests. Run from the backend/ folder:   pytest -q
 
They use an in-memory fake MongoDB (mongomock) and a stubbed analysis
pipeline, so they need no internet, no Atlas account and no TensorFlow --
they check the API logic itself: auth, ownership, run lifecycle, errors.
"""
 
from datetime import datetime, timezone
 
import mongomock
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
 
from config import settings
 
settings.jwt_secret = "unit-test-secret-" * 3          # >= 32 chars
settings.mongodb_uri = "mongomock://test"
 
from api import security                                  # noqa: E402
from api.ratelimit import auth_limiter                    # noqa: E402
from database import db as dbmod                          # noqa: E402
from orchestrator.graph import AGENT_ORDER                # noqa: E402
from services import run_executor                         # noqa: E402
 
 
# ----------------------------------------------------------------- helpers
def fake_pipeline(ticker, mode="ok"):
    """Stands in for orchestrator.graph.stream_analysis (yields per-agent chunks)."""
    log: list[str] = []
    idx = pd.bdate_range("2025-01-01", periods=60)
    close = pd.Series(np.linspace(100, 120, 60), index=idx)
    df = pd.DataFrame({"Close": close, "SMA_20": close.rolling(20).mean(), "EMA_20": close.ewm(span=20).mean()})
 
    base = {"ticker": ticker, "agent_log": log}
    if mode == "crash":
        raise ValueError("secret internal detail that must never reach the user")
    if mode == "bad_ticker":
        log.append("Preprocessor -> Failed")
        yield {"preprocessor": {**base, "price_data": None, "preprocessing_error":
               "MCP call_tool('fetch_ohlcv') failed: [RuntimeError] Error executing tool fetch_ohlcv: "
               f"No data returned for '{ticker}'. Check the ticker symbol is correct."}}
        return
 
    log.append("Preprocessor -> Done")
    s = {**base, "price_data": df, "preprocessing_error": None}
    yield {"preprocessor": s}
    log.append("Technical Analyst -> Done")
    s = {**s, "technical_metrics": {"latest_close": np.float64(120.0), "sma_20": 115.5, "ema_20": 116.0,
                                    "rsi_14": 62.5, "trend": "above SMA (bullish bias)"}}
    yield {"technical_analyst": s}
    log.append("Sentiment -> Done")
    s = {**s, "sentiment": {"score": 0.12, "label": "positive", "headlines": ["a", "b", "c"]}}
    yield {"sentiment": s}
    log.append("Forecasting -> Done")
    s = {**s, "forecast": {"forecast_days": 30, "forecast_change_pct": 1.5,
                           "confidence_interval_95": {"lower": 90.0, "upper": 140.0},
                           "lstm": {"forecast_change_pct": -2.0}}}
    yield {"forecasting": s}
    log.append("Risk -> Done")
    s = {**s, "risk": {"sharpe_ratio": 0.8, "annualized_volatility_pct": 22.0, "risk_label": "low",
                       "value_at_risk_95": {"daily_pct": -2.1},
                       "monte_carlo": {"horizon_days": 30, "probability_of_loss_pct": 41.0}}}
    yield {"risk": s}
 
 
@pytest.fixture()
def client(monkeypatch):
    mdb = mongomock.MongoClient(tz_aware=True)["test"]
    dbmod.ensure_indexes(mdb)
    dbmod.set_db(mdb)
    auth_limiter.reset()
    monkeypatch.setattr(run_executor, "stream_analysis", fake_pipeline)
    import main
    with TestClient(main.app) as c:
        c.mdb = mdb
        yield c
 
 
def register(client, email="a@example.com", name="Alice", password="correct-horse-battery"):
    r = client.post("/api/auth/register", json={"name": name, "email": email, "password": password})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]
 
 
def auth(token):
    return {"Authorization": f"Bearer {token}"}
 
 
# -------------------------------------------------------------------- health
def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok", "db": "ok"}
 
 
# ---------------------------------------------------------------------- auth
def test_register_returns_token_and_hides_password(client):
    r = client.post("/api/auth/register", json={"name": " Alice ", "email": " A@Example.COM ", "password": "correct-horse-battery"})
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["email"] == "a@example.com" and body["user"]["name"] == "Alice"
    assert "password" not in str(body).lower()
    stored = client.mdb.users.find_one({"email": "a@example.com"})
    assert stored["password_hash"].startswith(("scrypt$", "pbkdf2_sha256$"))
    assert "correct-horse" not in stored["password_hash"]
 
 
def test_register_duplicate_email_is_409_case_insensitive(client):
    register(client, email="a@example.com")
    r = client.post("/api/auth/register", json={"name": "B", "email": "A@EXAMPLE.com", "password": "another-long-pass"})
    assert r.status_code == 409
 
 
@pytest.mark.parametrize("payload", [
    {"name": "A", "email": "a@example.com", "password": "short"},
    {"name": "A", "email": "not-an-email", "password": "long-enough-pw"},
    {"name": "   ", "email": "a@example.com", "password": "long-enough-pw"},
    {"name": "A", "email": "a@example.com", "password": "x" * 200},
])
def test_register_validation(client, payload):
    assert client.post("/api/auth/register", json=payload).status_code == 422
 
 
def test_login_success_and_failures_are_indistinguishable(client):
    register(client)
    ok = client.post("/api/auth/login", json={"email": "A@example.com", "password": "correct-horse-battery"})
    assert ok.status_code == 200 and ok.json()["access_token"]
    wrong_pw = client.post("/api/auth/login", json={"email": "a@example.com", "password": "nope-nope-nope"})
    unknown = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "nope-nope-nope"})
    assert wrong_pw.status_code == unknown.status_code == 401
    assert wrong_pw.json() == unknown.json()
 
 
def test_me_requires_valid_token(client):
    token = register(client)
    assert client.get("/api/auth/me", headers=auth(token)).json()["email"] == "a@example.com"
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers=auth("garbage.token.value")).status_code == 401
 
 
def test_expired_token_rejected(client, monkeypatch):
    token = register(client)
    uid = client.get("/api/auth/me", headers=auth(token)).json()["id"]
    monkeypatch.setattr(settings, "jwt_expire_minutes", -5)
    expired = security.create_access_token(uid)
    assert client.get("/api/auth/me", headers=auth(expired)).status_code == 401
 
 
def test_token_for_deleted_user_rejected(client):
    token = register(client)
    client.mdb.users.delete_many({})
    assert client.get("/api/auth/me", headers=auth(token)).status_code == 401
 
 
def test_login_rate_limited(client, monkeypatch):
    monkeypatch.setattr(auth_limiter, "max_calls", 3)
    for _ in range(3):
        client.post("/api/auth/login", json={"email": "x@example.com", "password": "whatever-pass"})
    r = client.post("/api/auth/login", json={"email": "x@example.com", "password": "whatever-pass"})
    assert r.status_code == 429 and "Retry-After" in r.headers
 
 
def test_password_hashing_unit():
    h1, h2 = security.hash_password("hunter2hunter2"), security.hash_password("hunter2hunter2")
    assert h1 != h2                                          # unique salt each time
    assert security.verify_password("hunter2hunter2", h1)
    assert not security.verify_password("wrong", h1)
    assert not security.verify_password("x", "garbage-not-a-hash")
 
 
# ------------------------------------------------------------------ analysis
@pytest.mark.parametrize("ticker", ["TSLA; DROP TABLE", "A" * 16, "", "TS LA", "../etc"])
def test_invalid_ticker_rejected(client, ticker):
    token = register(client)
    assert client.post("/api/analysis/run", json={"ticker": ticker}, headers=auth(token)).status_code == 422
 
 
def test_run_requires_auth(client):
    assert client.post("/api/analysis/run", json={"ticker": "TSLA"}).status_code == 401
 
 
def test_full_run_lifecycle_and_report(client):
    token = register(client)
    r = client.post("/api/analysis/run", json={"ticker": " tsla "}, headers=auth(token))
    assert r.status_code == 202
    assert r.json()["ticker"] == "TSLA" and r.json()["status"] == "queued"
    run_id = r.json()["id"]
 
    run = client.get(f"/api/analysis/{run_id}", headers=auth(token)).json()
    assert run["status"] == "completed"
    assert run["completed_agents"] == AGENT_ORDER and run["agent_order"] == AGENT_ORDER
    assert len(run["agent_log"]) == 5 and run["report_id"]
 
    rep = client.get(f"/api/analysis/{run_id}/report", headers=auth(token))
    assert rep.status_code == 200
    report = rep.json()
    assert report["ticker"] == "TSLA" and "TSLA last closed at $120.00" in report["summary"]
    assert "disagree" in report["summary"]                   # ARIMA +1.5 vs LSTM -2.0
    assert report["overview"]["forecast_models_agree"] is False
    assert report["errors"] == {} and "not financial advice" in report["disclaimer"].lower()
    series = report["price_series"]
    assert len(series["dates"]) == len(series["close"]) == 60
    assert series["sma_20"][0] is None and series["sma_20"][-1] is not None   # NaN -> null, valid JSON
    assert "buy" not in report["summary"].lower().split()    # no trade advice
 
    listing = client.get("/api/reports", headers=auth(token)).json()
    assert len(listing) == 1 and listing[0]["id"] == run["report_id"] and "price_series" not in listing[0]
    assert client.get(f"/api/reports/{run['report_id']}", headers=auth(token)).json()["id"] == run["report_id"]
 
 
def test_bad_ticker_run_fails_with_friendly_error(client, monkeypatch):
    monkeypatch.setattr(run_executor, "stream_analysis", lambda t: fake_pipeline(t, "bad_ticker"))
    token = register(client)
    run_id = client.post("/api/analysis/run", json={"ticker": "ZZZZ"}, headers=auth(token)).json()["id"]
    run = client.get(f"/api/analysis/{run_id}", headers=auth(token)).json()
    assert run["status"] == "failed"
    assert run["error"].startswith("No data returned for 'ZZZZ'") and "MCP" not in run["error"]
    assert client.get(f"/api/analysis/{run_id}/report", headers=auth(token)).status_code == 404
    assert client.get("/api/reports", headers=auth(token)).json() == []
 
 
def test_unexpected_crash_does_not_leak_internals(client, monkeypatch):
    monkeypatch.setattr(run_executor, "stream_analysis", lambda t: fake_pipeline(t, "crash"))
    token = register(client)
    run_id = client.post("/api/analysis/run", json={"ticker": "TSLA"}, headers=auth(token)).json()["id"]
    run = client.get(f"/api/analysis/{run_id}", headers=auth(token)).json()
    assert run["status"] == "failed" and "secret internal detail" not in str(run)
 
 
def test_one_active_run_per_user(client):
    token = register(client)
    uid = client.get("/api/auth/me", headers=auth(token)).json()["id"]
    client.mdb.analysis_runs.insert_one({"user_id": uid, "ticker": "AAPL", "status": "running",
                                         "created_at": datetime.now(timezone.utc)})
    r = client.post("/api/analysis/run", json={"ticker": "TSLA"}, headers=auth(token))
    assert r.status_code == 429
 
 
def test_report_before_finish_is_409(client):
    token = register(client)
    uid = client.get("/api/auth/me", headers=auth(token)).json()["id"]
    rid = client.mdb.analysis_runs.insert_one({"user_id": uid, "ticker": "AAPL", "status": "running",
                                               "created_at": datetime.now(timezone.utc)}).inserted_id
    assert client.get(f"/api/analysis/{rid}/report", headers=auth(token)).status_code == 409
 
 
def test_users_cannot_see_each_others_data(client):
    alice = register(client, email="alice@example.com")
    bob = register(client, email="bob@example.com", name="Bob")
    run_id = client.post("/api/analysis/run", json={"ticker": "TSLA"}, headers=auth(alice)).json()["id"]
    report_id = client.get(f"/api/analysis/{run_id}", headers=auth(alice)).json()["report_id"]
 
    assert client.get(f"/api/analysis/{run_id}", headers=auth(bob)).status_code == 404
    assert client.get(f"/api/analysis/{run_id}/report", headers=auth(bob)).status_code == 404
    assert client.get(f"/api/reports/{report_id}", headers=auth(bob)).status_code == 404
    assert client.get("/api/reports", headers=auth(bob)).json() == []
    assert client.get("/api/reports", headers=auth(alice)).json() != []
 
 
def test_malformed_ids_are_404(client):
    token = register(client)
    assert client.get("/api/analysis/not-an-id", headers=auth(token)).status_code == 404
    assert client.get("/api/reports/not-an-id", headers=auth(token)).status_code == 404
 
 
def test_sweep_marks_orphaned_runs_failed(client):
    rid = client.mdb.analysis_runs.insert_one({"user_id": "u", "ticker": "X", "status": "running",
                                               "created_at": datetime.now(timezone.utc)}).inserted_id
    assert run_executor.sweep_stale_runs() == 1
    doc = client.mdb.analysis_runs.find_one({"_id": rid})
    assert doc["status"] == "failed" and "restarted" in doc["error"]
 
 
def test_reports_pagination(client):
    token = register(client)
    for t in ("AAPL", "MSFT", "TSLA"):
        client.post("/api/analysis/run", json={"ticker": t}, headers=auth(token))
    all_ = client.get("/api/reports", headers=auth(token)).json()
    assert [r["ticker"] for r in all_] == ["TSLA", "MSFT", "AAPL"]          # newest first
    assert len(client.get("/api/reports?limit=2", headers=auth(token)).json()) == 2
    assert client.get("/api/reports?limit=0", headers=auth(token)).status_code == 422
 










