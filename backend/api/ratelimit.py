"""
Tiny in-memory sliding-window rate limiter for the auth endpoints
(brute-force protection). In-memory means: per server process, and it
resets on restart -- fine for a single-instance deployment; a multi-
instance deployment would need a shared store (e.g. Redis).
"""
 
import threading
import time
from collections import defaultdict, deque
 
from fastapi import HTTPException, Request
 
 
class RateLimiter:
    def __init__(self, max_calls: int, window_seconds: int) -> None:
        self.max_calls = max_calls
        self.window = window_seconds
        self._calls: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()
 
    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            q = self._calls[key]
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.max_calls:
                retry_after = max(1, int(self.window - (now - q[0])))
                raise HTTPException(
                    status_code=429,
                    detail="Too many attempts. Please wait a moment and try again.",
                    headers={"Retry-After": str(retry_after)},
                )
            q.append(now)
 
    def reset(self) -> None:
        with self._lock:
            self._calls.clear()
 
 
# 10 register/login attempts per minute per client address
auth_limiter = RateLimiter(max_calls=10, window_seconds=60)
 
 
def limit_auth(request: Request) -> None:
    auth_limiter.check(request.client.host if request.client else "unknown")
 










