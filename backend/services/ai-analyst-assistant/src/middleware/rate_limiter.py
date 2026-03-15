"""Rate limiting middleware — enforces per-tenant and per-analyst request budgets."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

import structlog
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.settings import settings

logger = structlog.get_logger()


class _SlidingWindowCounter:
    """Simple in-process sliding window rate limiter.

    For production at scale, replace with Redis-backed implementation
    (e.g., redis INCR + EXPIRE or sliding window log in Redis).
    """

    def __init__(self) -> None:
        self._windows: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        timestamps = self._windows[key]
        # Prune expired entries
        self._windows[key] = [t for t in timestamps if t > cutoff]
        if len(self._windows[key]) >= limit:
            return False
        self._windows[key].append(now)
        return True


_counter = _SlidingWindowCounter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce per-tenant and per-analyst rate limits on AI service endpoints."""

    async def dispatch(self, request: Request, call_next):
        # Skip health and metrics endpoints
        if request.url.path in ("/v1/health", "/health", "/metrics"):
            return await call_next(request)

        # Extract identity from request state (set by auth dependency)
        # For middleware-level enforcement, parse the JWT tenant_id claim
        tenant_id = request.headers.get("X-Tenant-ID", "unknown")
        analyst_id = request.headers.get("X-User-ID", "unknown")

        # Per-tenant rate limit
        tenant_key = f"tenant:{tenant_id}"
        if not _counter.is_allowed(tenant_key, settings.rate_limit_per_tenant_per_minute):
            logger.warning(
                "rate_limit_exceeded",
                tenant_id=tenant_id,
                limit_type="per_tenant",
                limit=settings.rate_limit_per_tenant_per_minute,
            )
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {settings.rate_limit_per_tenant_per_minute} requests/minute per tenant",
            )

        # Per-analyst rate limit
        analyst_key = f"analyst:{analyst_id}"
        if not _counter.is_allowed(analyst_key, settings.rate_limit_per_analyst_per_minute):
            logger.warning(
                "rate_limit_exceeded",
                analyst_id=analyst_id,
                limit_type="per_analyst",
                limit=settings.rate_limit_per_analyst_per_minute,
            )
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {settings.rate_limit_per_analyst_per_minute} requests/minute per analyst",
            )

        return await call_next(request)
