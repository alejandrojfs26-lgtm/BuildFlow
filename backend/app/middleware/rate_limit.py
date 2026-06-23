import time
from collections import defaultdict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import AppError


class InMemoryRateLimiter:
    def __init__(self):
        self._attempts: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_attempts: int = 10, window_seconds: int = 60) -> None:
        now = time.time()
        cutoff = now - window_seconds
        self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]
        if len(self._attempts[key]) >= max_attempts:
            raise AppError("Too many requests", code="rate_limit", status_code=429)
        self._attempts[key].append(now)


rate_limiter = InMemoryRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/"):
            client_ip = request.client.host if request.client else "unknown"
            rate_limiter.check(client_ip, max_attempts=100, window_seconds=60)
        return await call_next(request)
