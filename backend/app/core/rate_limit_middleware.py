"""
Rate Limiting Middleware for AI Investment Advisor.

Implements an in-memory, thread-safe, sliding-window rate limiter per client IP
(and optional authenticated user token) with granular route-specific buckets:
1. Auth Endpoints (/auth/login, /auth/register): Strict brute-force protection (10 req/min).
2. AI Generation (/advisor/ask, /research, /compare, /scenarios/simulate): Quota protection (20 req/min).
3. Document Ingestion (/documents/upload): Disk and processing flood protection (10 uploads/min).
4. General Endpoints: Standard protection (120 req/min).

Returns standard HTTP 429 Too Many Requests with Retry-After header and structured JSON.
Bypasses /health checks, OPTIONS preflight, and automated test environments.
"""

from collections import defaultdict
from datetime import datetime, timezone
import logging
import os
import threading
import time
from typing import NamedTuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings

logger = logging.getLogger("api.rate_limit")


class RateLimitRule(NamedTuple):
    limit: int
    window_seconds: int


# Tiered limits: (max_requests, window_seconds)
RULES: dict[str, RateLimitRule] = {
    # High-risk brute-force protection
    "auth": RateLimitRule(limit=10, window_seconds=60),
    # Expensive GenAI token budget protection
    "ai_generation": RateLimitRule(limit=20, window_seconds=60),
    # File upload disk/memory protection
    "upload": RateLimitRule(limit=10, window_seconds=60),
    # General API baseline
    "default": RateLimitRule(limit=120, window_seconds=60),
}


class SlidingWindowRateLimiter:
    """Thread-safe sliding window rate limiter using monotonic timestamps."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # key -> list of monotonic timestamps
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.monotonic()

    def _cleanup(self, now: float) -> None:
        """Periodically remove stale client buckets to prevent memory accumulation."""
        if now - self._last_cleanup < 120.0:
            return
        self._last_cleanup = now
        stale_keys = [
            k for k, timestamps in self._buckets.items()
            if not timestamps or now - timestamps[-1] > 120.0
        ]
        for k in stale_keys:
            self._buckets.pop(k, None)

    def is_allowed(self, client_key: str, rule: RateLimitRule) -> tuple[bool, int]:
        """
        Check if client request is within rate limit.
        Returns (is_allowed, retry_after_seconds).
        """
        now = time.monotonic()
        bucket_key = f"{client_key}:{rule.limit}:{rule.window_seconds}"
        window_start = now - rule.window_seconds

        with self._lock:
            self._cleanup(now)
            timestamps = self._buckets[bucket_key]

            # Filter out timestamps outside the active sliding window
            valid_timestamps = [ts for ts in timestamps if ts > window_start]
            self._buckets[bucket_key] = valid_timestamps

            if len(valid_timestamps) >= rule.limit:
                # Earliest timestamp in the window determines when the next slot frees up
                oldest_in_window = valid_timestamps[0]
                retry_after = max(1, int(oldest_in_window + rule.window_seconds - now) + 1)
                return False, retry_after

            # Record this request
            valid_timestamps.append(now)
            return True, 0


_limiter = SlidingWindowRateLimiter()


def _get_client_key(request: Request) -> str:
    """Extract client IP, honoring X-Forwarded-For if present, or fallback to host."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = "unknown_client"

    # If an Authorization header is provided, include a hashed slice to separate concurrent users behind a NAT
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        token_snippet = auth[-8:]
        return f"{client_ip}:{token_snippet}"

    return client_ip


def _resolve_rule_for_path(path: str, method: str) -> RateLimitRule:
    """Match request route to the appropriate rate limit tier."""
    lower_path = path.lower()

    # Auth routes (login, register)
    if lower_path.startswith("/auth/login") or lower_path.startswith("/auth/register"):
        return RULES["auth"]

    # File uploads
    if lower_path.startswith("/documents/upload"):
        return RULES["upload"]

    # AI generation & research routes
    if (
        lower_path.startswith("/advisor/ask")
        or lower_path.startswith("/research")
        or lower_path.startswith("/compare")
        or lower_path.startswith("/scenarios/simulate")
    ):
        return RULES["ai_generation"]

    return RULES["default"]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Starlette middleware intercepting requests to enforce rate limits."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Bypass CORS preflight OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)

        # Bypass health and monitoring endpoints
        path = request.url.path
        if path.startswith("/health") or path in ("/favicon.ico", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        # Bypass rate limiting in test environments
        if os.getenv("TESTING") == "1" or settings.app_env == "test":
            return await call_next(request)

        rule = _resolve_rule_for_path(path, request.method)
        client_key = _get_client_key(request)

        allowed, retry_after = _limiter.is_allowed(client_key, rule)
        if not allowed:
            logger.warning(
                "Rate limit exceeded for %s on %s %s (limit: %d req/%ds). Retry-After: %ds",
                client_key,
                request.method,
                path,
                rule.limit,
                rule.window_seconds,
                retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit reached. Please wait {retry_after} seconds before retrying.",
                    "detail": f"Rate limit reached. Please wait {retry_after} seconds before retrying.",
                    "retry_after": retry_after,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(rule.limit),
                    "X-RateLimit-Window": f"{rule.window_seconds}s",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rule.limit)
        response.headers["X-RateLimit-Window"] = f"{rule.window_seconds}s"
        return response
