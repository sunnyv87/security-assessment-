"""Rate limiting middleware — enforces per-tenant and per-analyst request budgets via Redis."""

from __future__ import annotations

import structlog
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

import redis.asyncio as redis

from src.config.settings import settings

logger = structlog.get_logger()

# Redis-backed sliding window rate limiter.
# Uses INCR + EXPIRE for atomic, distributed counters shared across all replicas.
_redis: redis.Redis | None = None


async def _get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def _is_allowed(key: str, limit: int, window_seconds: int = 60) -> bool:
    """Check and increment a sliding window counter in Redis."""
    r = await _get_redis()
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, window_seconds, nx=True)
    results = await pipe.execute()
    current_count = results[0]
    return current_count <= limit


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce per-tenant and per-analyst rate limits on AI service endpoints."""

    async def dispatch(self, request: Request, call_next):
        # Skip health and metrics endpoints
        if request.url.path in ("/v1/health", "/health", "/metrics"):
            return await call_next(request)

        # Extract identity from request headers (set by auth/gateway)
        tenant_id = request.headers.get("X-Tenant-ID", "unknown")
        analyst_id = request.headers.get("X-User-ID", "unknown")

        # Per-tenant rate limit
        tenant_key = f"ratelimit:tenant:{tenant_id}"
        if not await _is_allowed(tenant_key, settings.rate_limit_per_tenant_per_minute):
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
        analyst_key = f"ratelimit:analyst:{analyst_id}"
        if not await _is_allowed(analyst_key, settings.rate_limit_per_analyst_per_minute):
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
