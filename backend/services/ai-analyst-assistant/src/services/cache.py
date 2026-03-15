"""Redis-backed cache for AI analysis results."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis
import structlog

from src.config.settings import settings

logger = structlog.get_logger()


class CacheService:
    """Redis cache with JSON serialization and TTL support."""

    def __init__(self) -> None:
        self._redis: redis.Redis | None = None

    async def connect(self) -> None:
        self._redis = redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
        logger.info("redis_connected", url=settings.redis_url)

    async def disconnect(self) -> None:
        if self._redis:
            await self._redis.close()

    async def get(self, key: str) -> dict[str, Any] | None:
        """Get cached JSON value or None if not found."""
        if not self._redis:
            return None
        try:
            raw = await self._redis.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            logger.warning("cache_get_error", key=key)
            return None

    async def set(self, key: str, value: dict[str, Any], ttl: int = 3600) -> None:
        """Cache a JSON-serializable value with TTL in seconds."""
        if not self._redis:
            return
        try:
            await self._redis.set(key, json.dumps(value), ex=ttl)
        except Exception:
            logger.warning("cache_set_error", key=key)

    async def delete(self, key: str) -> None:
        """Delete a cached value."""
        if not self._redis:
            return
        try:
            await self._redis.delete(key)
        except Exception:
            logger.warning("cache_delete_error", key=key)

    async def invalidate_pattern(self, pattern: str) -> None:
        """Delete all keys matching a pattern (for cache busting)."""
        if not self._redis:
            return
        try:
            cursor = None
            while cursor != 0:
                cursor, keys = await self._redis.scan(
                    cursor=cursor or 0, match=pattern, count=100
                )
                if keys:
                    await self._redis.delete(*keys)
        except Exception:
            logger.warning("cache_invalidate_error", pattern=pattern)
