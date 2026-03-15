"""CSRF protection middleware — custom-header verification.

Browser-based CSRF attacks cannot set custom headers on cross-origin requests
without a successful CORS preflight. By requiring a custom X-Requested-With
header on all state-changing requests, we ensure that only legitimate
same-origin (or CORS-approved) clients can make mutating API calls.
"""

from __future__ import annotations

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_SKIP_PATHS = frozenset({"/health", "/v1/health", "/metrics"})


class CSRFMiddleware(BaseHTTPMiddleware):
    """Reject state-changing requests missing the X-Requested-With header."""

    async def dispatch(self, request: Request, call_next):
        if request.method in _SAFE_METHODS:
            return await call_next(request)

        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        requested_with = request.headers.get("X-Requested-With")
        if not requested_with:
            logger.warning(
                "csrf_rejected",
                method=request.method,
                path=request.url.path,
                client=request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Missing required X-Requested-With header"},
            )

        return await call_next(request)
