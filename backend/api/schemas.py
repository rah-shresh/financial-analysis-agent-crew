"""Request/response models (validation happens here, before any logic runs)."""
 
import re
from datetime import datetime
from typing import Any, Optional
 
from pydantic import BaseModel, Field, field_validator
 
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# Letters, digits and . - ^ = (e.g. TSLA, BRK-B, RELIANCE.NS, ^GSPC). Validated
# BEFORE the ticker is ever passed to an external service.
_TICKER_RE = re.compile(r"^[A-Za-z0-9.\-^=]{1,15}$")
 
 
def _clean_email(value: str) -> str:
    value = value.strip().lower()
    if len(value) > 254 or not _EMAIL_RE.match(value):
        raise ValueError("Enter a valid email address")
    return value
 
 
class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: str
    password: str = Field(min_length=8, max_length=128)
 
    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name can't be blank")
        return v
 
    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return _clean_email(v)
 
 
class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=128)
 
    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return _clean_email(v)
 
 
class UserPublic(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime
 
 
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
 
 
class RunRequest(BaseModel):
    ticker: str
 
    @field_validator("ticker")
    @classmethod
    def _ticker(cls, v: str) -> str:
        v = v.strip()
        if not _TICKER_RE.match(v):
            raise ValueError("Ticker may only contain letters, digits and . - ^ = (max 15 characters)")
        return v.upper()
 
 
class RunPublic(BaseModel):
    id: str
    ticker: str
    status: str                       # queued | running | completed | failed
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    agent_order: list[str]
    completed_agents: list[str]
    agent_log: list[str]
    report_id: Optional[str] = None
 
 
class ReportSummary(BaseModel):
    id: str
    run_id: str
    ticker: str
    created_at: datetime
    overview: dict[str, Any]
 
 
class ReportFull(ReportSummary):
    summary: str
    technical: Optional[dict[str, Any]] = None
    sentiment: Optional[dict[str, Any]] = None
    forecast: Optional[dict[str, Any]] = None
    risk: Optional[dict[str, Any]] = None
    price_series: Optional[dict[str, Any]] = None
    agent_log: list[str]
    errors: dict[str, str]
    disclaimer: str
 










