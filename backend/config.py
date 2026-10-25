"""
Central configuration. Every secret/setting comes from environment
variables (loaded from backend/.env in development) -- nothing sensitive
is hardcoded anywhere in the project.
"""
 
import os
from pathlib import Path
 
from dotenv import load_dotenv
 
_ENV_PATH = Path(__file__).resolve().parent / ".env"
# utf-8-sig: Windows Notepad can save a hidden BOM character at the start of the
# file, which would otherwise silently corrupt the first variable's name.
load_dotenv(_ENV_PATH, encoding="utf-8-sig")
 
 
def _env_file_hint() -> str:
    """Say WHICH of the usual Windows mistakes it is, instead of a generic error."""
    if _ENV_PATH.exists():
        return (f"Found {_ENV_PATH}, but it doesn't define the value(s) above. Open it and check: "
                "each line is NAME=value (no spaces around '='), the values are filled in, "
                "and the file is saved as UTF-8 (not UTF-16).")
    if _ENV_PATH.with_name(".env.txt").exists():
        return "Found '.env.txt' -- rename it to exactly '.env' (Notepad adds .txt to the name)."
    return f"No .env file exists at {_ENV_PATH}. Create it there (copy .env.example to .env)."
 
 
class Settings:
    def __init__(self) -> None:
        self.mongodb_uri = os.environ.get("MONGODB_URI", "")
        self.mongodb_db = os.environ.get("MONGODB_DB", "financial_crew")
        self.jwt_secret = os.environ.get("JWT_SECRET", "")
        self.jwt_expire_minutes = int(os.environ.get("JWT_EXPIRE_MINUTES", "1440"))  # 24h
        self.frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
        # How many analyses may execute at the same time (extra ones wait as "queued").
        self.max_concurrent_runs = int(os.environ.get("MAX_CONCURRENT_RUNS", "2"))
 
    def validate(self) -> None:
        """Fail fast at startup, with instructions, instead of crashing later."""
        problems = []
        if not self.mongodb_uri:
            problems.append("MONGODB_URI is not set (your MongoDB Atlas connection string).")
        if len(self.jwt_secret) < 32:
            problems.append(
                "JWT_SECRET is missing or shorter than 32 characters. Generate one with:\n"
                '    python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )
        if problems:
            raise RuntimeError(
                "Configuration error:\n  - " + "\n  - ".join(problems) + "\n\n" + _env_file_hint()
            )
 
 
settings = Settings()
 









