"""
Password hashing + JWT helpers.
 
Passwords use scrypt from Python's standard library (hashlib.scrypt) --
a memory-hard, purpose-built password hash. It was chosen over `bcrypt`
because bcrypt ships a compiled (Rust) extension, and this project's
Windows machine has already blocked two such binaries (ormsgpack,
statsmodels' Kalman filter) via Application Control. Stdlib = no new
binary to block. If scrypt is somehow unavailable, PBKDF2-HMAC-SHA256
(also stdlib, OWASP-approved) is used instead. Stored hashes carry their
own parameters, so they can be upgraded later without breaking old ones.
"""
 
import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
 
import jwt
 
from config import settings
 
_SCRYPT_N, _SCRYPT_R, _SCRYPT_P = 2**14, 8, 1
_PBKDF2_ITERATIONS = 600_000
 
 
def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")
 
 
def _unb64(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))
 
 
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    if hasattr(hashlib, "scrypt"):
        dk = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P,
            dklen=32, maxmem=64 * 1024 * 1024,
        )
        return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${_b64(salt)}${_b64(dk)}"
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS, dklen=32)
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${_b64(salt)}${_b64(dk)}"
 
 
def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, *params = stored.split("$")
        if scheme == "scrypt":
            n, r, p, salt, expected = int(params[0]), int(params[1]), int(params[2]), _unb64(params[3]), _unb64(params[4])
            actual = hashlib.scrypt(
                password.encode("utf-8"), salt=salt, n=n, r=r, p=p,
                dklen=len(expected), maxmem=64 * 1024 * 1024,
            )
        elif scheme == "pbkdf2_sha256":
            iters, salt, expected = int(params[0]), _unb64(params[1]), _unb64(params[2])
            actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters, dklen=len(expected))
        else:
            return False
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False
 
 
# Hashed once at import; verified against when a login email doesn't exist,
# so "unknown email" and "wrong password" take the same time (no user enumeration).
DUMMY_HASH = hash_password("not-a-real-password")
 
 
def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
 
 
def decode_access_token(token: str) -> str:
    """Return the user id inside a valid token; raise jwt.PyJWTError otherwise."""
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    return payload["sub"]
 










