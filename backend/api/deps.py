"""Shared FastAPI dependencies."""
 
import jwt
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
 
from api.security import decode_access_token
from database.db import get_db
 
_bearer = HTTPBearer(auto_error=False)
 
_UNAUTHORIZED = HTTPException(
    status_code=401,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)
 
 
def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    """Resolve the logged-in user from the Bearer token, or raise 401."""
    if creds is None:
        raise _UNAUTHORIZED
    try:
        user_id = decode_access_token(creds.credentials)
        user = get_db().users.find_one({"_id": ObjectId(user_id)})
    except (jwt.PyJWTError, InvalidId, KeyError, TypeError):
        raise _UNAUTHORIZED
    if user is None:
        raise _UNAUTHORIZED
    return user
 
 
def parse_object_id(value: str, what: str = "Resource") -> ObjectId:
    """Malformed ids get a 404, the same as ids that don't exist."""
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=404, detail=f"{what} not found")
 










