"""
Simple in-process sliding-window rate limiter.

Good enough for a single uvicorn worker. For multiple workers / instances,
swap the storage for Redis.
"""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, max_calls: int, period_seconds: int, scope: str):
        self.max_calls = max_calls
        self.period = period_seconds
        self.scope = scope
        self._hits: dict[str, deque] = defaultdict(deque)

    def _key(self, request: Request) -> str:
        # X-Forwarded-For is client-controlled, so only the socket peer is trusted.
        # Behind a reverse proxy, run uvicorn with --proxy-headers --forwarded-allow-ips.
        ip = request.client.host if request.client else "?"
        return f"{self.scope}:{ip}"

    async def __call__(self, request: Request) -> None:
        key = self._key(request)
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.period:
            hits.popleft()
        if len(hits) >= self.max_calls:
            retry = int(self.period - (now - hits[0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Try again in {retry}s.",
                headers={"Retry-After": str(retry)},
            )
        hits.append(now)


login_limiter = RateLimiter(10, 60, "login")
register_limiter = RateLimiter(5, 300, "register")
otp_limiter = RateLimiter(10, 300, "otp")
ai_limiter = RateLimiter(30, 60, "ai")
