"""
Executes one analysis run in the background and records its progress in
MongoDB after EVERY agent finishes, so a client polling
GET /api/analysis/{run_id} sees live progress.
 
Run lifecycle:  queued -> running -> completed | failed
 - completed: price data was available; the report holds every section
              that could be produced (agents that failed/skipped are
              listed honestly under report.errors, never faked).
 - failed:    no usable price data (e.g. wrong ticker) or an unexpected error.
"""
 
import logging
import re
import threading
from datetime import datetime, timezone
 
from bson import ObjectId
 
from config import settings
from database.db import get_db
from orchestrator.graph import stream_analysis
from services.report_builder import build_report
 
log = logging.getLogger("fincrew.runner")
 
# Caps simultaneous analyses (ARIMA/LSTM are CPU/RAM heavy); extra runs wait as "queued".
_slots = threading.BoundedSemaphore(settings.max_concurrent_runs)
 
 
def _now() -> datetime:
    return datetime.now(timezone.utc)
 
 
def friendly_error(message: str) -> str:
    """Strip the MCP plumbing wrapper so users see the actual reason."""
    match = re.search(r"Error executing tool \w+: (.*)$", message or "", re.S)
    return (match.group(1) if match else message or "Unknown error").strip()
 
 
def sweep_stale_runs() -> int:
    """On startup, runs still 'queued'/'running' belong to a server that
    died mid-run -- mark them failed so they don't block their owners."""
    result = get_db().analysis_runs.update_many(
        {"status": {"$in": ["queued", "running"]}},
        {"$set": {
            "status": "failed",
            "error": "The server restarted before this analysis finished. Please run it again.",
            "finished_at": _now(),
        }},
    )
    return result.modified_count
 
 
def _update(run_id: ObjectId, **fields) -> None:
    get_db().analysis_runs.update_one({"_id": run_id}, {"$set": fields})
 
 
def execute_run(run_id_str: str) -> None:
    db = get_db()
    run_id = ObjectId(run_id_str)
    run = db.analysis_runs.find_one({"_id": run_id})
    if run is None:
        return
 
    with _slots:
        _update(run_id, status="running", started_at=_now())
        try:
            final_state = None
            completed: list[str] = []
            for chunk in stream_analysis(run["ticker"]):
                node, node_state = next(iter(chunk.items()))
                final_state = node_state          # every node returns the full state
                completed.append(node)
                _update(run_id, completed_agents=list(completed),
                        agent_log=list(node_state.get("agent_log", [])))
 
            if final_state is None:
                raise RuntimeError("The pipeline produced no output")
 
            if final_state.get("price_data") is None:
                _update(run_id, status="failed", finished_at=_now(),
                        error=friendly_error(final_state.get("preprocessing_error", "")))
                return
 
            report = build_report(final_state, run_id_str, run["user_id"])
            report_id = db.reports.insert_one(report).inserted_id
            _update(run_id, status="completed", finished_at=_now(), report_id=str(report_id))
        except Exception:
            log.exception("Run %s crashed", run_id_str)   # full details stay in the server log
            _update(run_id, status="failed", finished_at=_now(),
                    error="The analysis failed unexpectedly. Please try again.")
 










