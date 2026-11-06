from fastapi import APIRouter, Depends, HTTPException, Query
 
from api.deps import get_current_user, parse_object_id
from api.schemas import ReportFull, ReportSummary
from database.db import get_db
from utils.currency import infer_currency

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _overview(doc: dict) -> dict:
    """The stored overview, with `currency` filled in for reports saved before it was recorded
    (their prices are in the ticker's home currency, which the suffix tells us)."""
    return {"currency": infer_currency(doc["ticker"]), **doc["overview"]}


def report_to_summary(doc: dict) -> ReportSummary:
    return ReportSummary(
        id=str(doc["_id"]), run_id=doc["run_id"], ticker=doc["ticker"],
        created_at=doc["created_at"], overview=_overview(doc),
    )
 
 
def report_to_full(doc: dict) -> ReportFull:
    return ReportFull(
        id=str(doc["_id"]), run_id=doc["run_id"], ticker=doc["ticker"],
        created_at=doc["created_at"], overview=_overview(doc), summary=doc["summary"],
        technical=doc.get("technical"), sentiment=doc.get("sentiment"),
        forecast=doc.get("forecast"), risk=doc.get("risk"), price_series=doc.get("price_series"),
        agent_log=doc.get("agent_log", []), errors=doc.get("errors", {}), disclaimer=doc["disclaimer"],
    )
 
 
def get_owned_report(report_id: str, user: dict) -> dict:
    doc = get_db().reports.find_one({"_id": parse_object_id(report_id, "Report"), "user_id": str(user["_id"])})
    if doc is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return doc
 
 
@router.get("", response_model=list[ReportSummary])
def list_reports(limit: int = Query(20, ge=1, le=50), skip: int = Query(0, ge=0),
                 user: dict = Depends(get_current_user)):
    """Newest first. Summaries only (no charts/series) -- open one for the full report."""
    cursor = (
        get_db().reports.find({"user_id": str(user["_id"])})
        .sort("created_at", -1).skip(skip).limit(limit)
    )
    return [report_to_summary(d) for d in cursor]
 
 
@router.get("/{report_id}", response_model=ReportFull)
def get_report(report_id: str, user: dict = Depends(get_current_user)):
    return report_to_full(get_owned_report(report_id, user))
 










