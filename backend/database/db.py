"""MongoDB connection + indexes. One shared MongoClient (it's thread-safe)."""
 
import logging
 
from pymongo import ASCENDING, DESCENDING, MongoClient
 
from config import settings
 
log = logging.getLogger("fincrew.db")
 
_db = None
 
 
def get_db():
    """Lazily create the connection on first use."""
    global _db
    if _db is None:
        client = MongoClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=5000,  # fail in 5s, not 30s, if Atlas is unreachable
            tz_aware=True,                  # datetimes come back timezone-aware (UTC)
        )
        _db = client[settings.mongodb_db]
        ensure_indexes(_db)
    return _db
 
 
def set_db(db) -> None:
    """Swap in another database object (used by the tests)."""
    global _db
    _db = db
 
 
def ensure_indexes(db) -> None:
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.analysis_runs.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    db.reports.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
 
 
def ping() -> None:
    get_db().command("ping")
 










