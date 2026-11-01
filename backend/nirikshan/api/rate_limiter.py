"""In-memory sliding-window rate limiter middleware with Retry-After headers."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from nirikshan.config import settings


class SlidingWindowRateLimiter:
    """Sliding-window rate limiter tracking request timestamps per client key."""

    def __init__(
        self,
        max_requests: int | None = None,
        window_seconds: float = 60.0,
    ) -> None:
        self.max_requests = max_requests or settings.rate_limit_per_minute
        self.window_seconds = window_seconds
        self._history: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self.enabled = True

    def set_limit(self, max_requests: int, window_seconds: float = 60.0) -> None:
        """Dynamically reconfigure limit (useful in testing)."""
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def reset(self) -> None:
        """Clear all historical request logs."""
        self._history.clear()

    async def is_allowed(self, client_key: str) -> tuple[bool, int, float]:
        """Check if request is permitted under rate limit.

        Returns: (allowed: bool, remaining: int, retry_after: float)
        """
        if not self.enabled or self.max_requests <= 0:
            return True, 9999, 0.0

        now = time.monotonic()
        window_start = now - self.window_seconds

        async with self._lock:
            # Filter timestamps within current window
            timestamps = [t for t in self._history[client_key] if t > window_start]
            self._history[client_key] = timestamps

            count = len(timestamps)
            if count >= self.max_requests:
                oldest = timestamps[0]
                retry_after = max(1.0, round(self.window_seconds - (now - oldest), 1))
                return False, 0, retry_after

            # Allow request and append timestamp
            self._history[client_key].append(now)
            remaining = self.max_requests - (count + 1)
            return True, remaining, 0.0


rate_limiter = SlidingWindowRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Starlette middleware intercepting requests and applying rate limiting."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Exclude static assets or health checks from strict rate limiting
        if request.url.path in ("/api/health", "/docs", "/openapi.json"):
            return await call_next(request)

        # Identify client by IP or token / user header
        client_key = (
            request.headers.get("X-Forwarded-For")
            or (request.client.host if request.client else "unknown-client")
        )

        allowed, remaining, retry_after = await rate_limiter.is_allowed(client_key)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Too many requests.",
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(int(retry_after)),
                    "X-RateLimit-Limit": str(rate_limiter.max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
