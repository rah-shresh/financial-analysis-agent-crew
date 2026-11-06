"""The dashboard (a different origin from the API) must be allowed in -- and nobody else."""
 
import mongomock
import pytest
from fastapi.testclient import TestClient
 
from config import settings
 
settings.jwt_secret = "unit-test-secret-" * 3
settings.mongodb_uri = "mongomock://test"
 
from database import db as dbmod  # noqa: E402
 
 
@pytest.fixture()
def client():
    dbmod.set_db(mongomock.MongoClient(tz_aware=True)["cors"])
    import main
    with TestClient(main.app) as c:
        yield c
 
 
def preflight(client, origin):
    return client.options(
        "/api/auth/login",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST",
                 "Access-Control-Request-Headers": "authorization,content-type"},
    )
 
 
@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://127.0.0.1:5173"])
def test_both_local_spellings_of_the_dashboard_are_allowed(client, origin):
    r = preflight(client, origin)
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == origin
 
 
def test_other_websites_are_not_allowed(client):
    r = preflight(client, "https://evil.example.com")
    assert "access-control-allow-origin" not in r.headers
 
 
def test_frontend_url_setting_accepts_a_comma_separated_list(monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", " https://app.example.com/ , http://localhost:5173 ")
    import config
    assert config.Settings().frontend_urls == ["https://app.example.com", "http://localhost:5173"]
 











