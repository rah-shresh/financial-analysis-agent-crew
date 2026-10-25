from datetime import datetime, timezone
 
from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError
 
from api.deps import get_current_user
from api.ratelimit import limit_auth
from api.schemas import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from api.security import DUMMY_HASH, create_access_token, hash_password, verify_password
from database.db import get_db
 
router = APIRouter(prefix="/api/auth", tags=["auth"])
 
 
def user_to_public(doc: dict) -> UserPublic:
    return UserPublic(id=str(doc["_id"]), name=doc["name"], email=doc["email"], created_at=doc["created_at"])
 
 
@router.post("/register", response_model=TokenResponse, status_code=201, dependencies=[Depends(limit_auth)])
def register(body: RegisterRequest):
    doc = {
        "name": body.name,
        "email": body.email,
        "password_hash": hash_password(body.password),
        "created_at": datetime.now(timezone.utc),
    }
    try:
        result = get_db().users.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    doc["_id"] = result.inserted_id
    return TokenResponse(access_token=create_access_token(str(doc["_id"])), user=user_to_public(doc))
 
 
@router.post("/login", response_model=TokenResponse, dependencies=[Depends(limit_auth)])
def login(body: LoginRequest):
    user = get_db().users.find_one({"email": body.email})
    # Always run one password verification (against a dummy hash when the
    # email is unknown) so response time doesn't reveal which emails exist.
    ok = verify_password(body.password, user["password_hash"] if user else DUMMY_HASH)
    if user is None or not ok:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(str(user["_id"])), user=user_to_public(user))
 
 
@router.get("/me", response_model=UserPublic)
def me(user: dict = Depends(get_current_user)):
    return user_to_public(user)
 










