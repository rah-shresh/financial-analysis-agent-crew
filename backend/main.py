"""
FastAPI application entry point.
 
Run (from the backend/ folder):
    uvicorn main:app --reload
Interactive API docs (try every endpoint in the browser):
    http://127.0.0.1:8000/docs
"""
 
import logging
from contextlib import asynccontextmanager
 
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
 
from api import analysis, auth, reports
from config import settings
from database.db import get_db, ping
from services.run_executor import sweep_stale_runs
 
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("fincrew")
 
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate()                      # clear error if .env is incomplete
    try:
        get_db()
        ping()
    except Exception as e:
        raise RuntimeError(
            "Could not connect to MongoDB. Check MONGODB_URI, and in Atlas: "
            "Network Access must allow your IP (0.0.0.0/0 for testing) and the database "
            f"user/password must be correct (URL-encode special characters). Detail: {e}"
        ) from e
    swept = sweep_stale_runs()
    if swept:
        log.warning("Marked %d unfinished run(s) from a previous server session as failed", swept)
    yield
 
 
app = FastAPI(title="Financial Analysis Agent Crew", version="0.8.0", lifespan=lifespan)
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],   # only the dashboard's own origin, not "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
 
app.include_router(auth.router)
app.include_router(analysis.router)
app.include_router(reports.router)
 
 
@app.get("/api/health", tags=["health"])
def health():
    try:
        ping()
    except Exception:
        raise HTTPException(status_code=503, detail="database unreachable")
    return {"status": "ok", "db": "ok"}
 

