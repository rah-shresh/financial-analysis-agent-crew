from datetime import datetime, timezone
 
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
 
from api.deps import get_current_user, parse_object_id
from api.schemas import ReportFull, RunPublic, RunRequest
from database.db import get_db
from orchestrator.graph import AGENT_ORDER
from services.run_executor import execute_run
 
router = APIRouter(prefix="/api/analysis", tags=["analysis"])
 
 
def build_agents(doc: dict) -> list[dict]:
    """Every agent in pipeline order. Finished ones come from the saved results; the
    first unfinished one of a running run is 'running'; the rest are 'queued' (or
    'skipped' if the run already ended without reaching them)."""
    results = doc.get("agent_results", {})
    ended = doc["status"] in ("completed", "failed")
    running_marked = False
    agents = []
    for name in AGENT_ORDER:
        if name in results:
            agents.append({"name": name, **results[name]})
        elif ended:
            agents.append({"name": name, "status": "skipped", "message": "This run ended before it got here."})
        elif doc["status"] == "running" and not running_marked:
            running_marked = True
            agents.append({"name": name, "status": "running"})
        else:
            agents.append({"name": name, "status": "queued"})
    return agents
 
 
def run_to_public(doc: dict) -> RunPublic:
    return RunPublic(
        id=str(doc["_id"]),
        ticker=doc["ticker"],
        status=doc["status"],
        created_at=doc["created_at"],
        started_at=doc.get("started_at"),
        finished_at=doc.get("finished_at"),
        error=doc.get("error"),
        agent_order=AGENT_ORDER,
        completed_agents=doc.get("completed_agents", []),
        agents=build_agents(doc),
        agent_log=doc.get("agent_log", []),
        report_id=doc.get("report_id"),
    )
 
 
def _get_owned_run(run_id: str, user: dict) -> dict:
    # Filtering by user_id means someone else's run looks exactly like a missing one (404).
    run = get_db().analysis_runs.find_one({"_id": parse_object_id(run_id, "Analysis run"), "user_id": str(user["_id"])})
    if run is None:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return run
 
 
@router.post("/run", response_model=RunPublic, status_code=202)
def start_run(body: RunRequest, background: BackgroundTasks, user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = str(user["_id"])
 
    # One active analysis per user: protects the free-tier data sources and server resources.
    if db.analysis_runs.find_one({"user_id": user_id, "status": {"$in": ["queued", "running"]}}):
        raise HTTPException(status_code=429, detail="You already have an analysis in progress. Wait for it to finish first.")
 
    run = {
        "user_id": user_id,
        "ticker": body.ticker,
        "status": "queued",
        "created_at": datetime.now(timezone.utc),
        "completed_agents": [],
        "agent_log": [],
    }
    run["_id"] = db.analysis_runs.insert_one(run).inserted_id
    background.add_task(execute_run, str(run["_id"]))
    return run_to_public(run)
 
 
@router.get("/{run_id}", response_model=RunPublic)
def get_run(run_id: str, user: dict = Depends(get_current_user)):
    return run_to_public(_get_owned_run(run_id, user))
 
 
@router.get("/{run_id}/report", response_model=ReportFull)
def get_run_report(run_id: str, user: dict = Depends(get_current_user)):
    run = _get_owned_run(run_id, user)
    if run["status"] in ("queued", "running"):
        raise HTTPException(status_code=409, detail="This analysis hasn't finished yet")
    if run["status"] == "failed" or not run.get("report_id"):
        raise HTTPException(status_code=404, detail=run.get("error") or "No report was produced for this run")
    from api.reports import get_owned_report, report_to_full
    return report_to_full(get_owned_report(run["report_id"], user))
 












