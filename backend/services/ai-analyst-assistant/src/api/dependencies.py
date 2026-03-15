"""FastAPI dependency injection for auth and services."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

import httpx
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from src.config.settings import settings
from src.pipelines.orchestrator import PipelineOrchestrator

logger = structlog.get_logger()

security = HTTPBearer()

# Singleton orchestrator instance (initialized on app startup)
_orchestrator: PipelineOrchestrator | None = None

# JWKS cache
_jwks_cache: dict | None = None
_jwks_fetched_at: float = 0


@dataclass
class AuthUser:
    """Authenticated user extracted from JWT."""

    id: str
    email: str
    name: str
    tenant_id: str
    roles: list[str]


async def _get_jwks() -> dict:
    """Fetch and cache Keycloak JWKS (refresh every 5 minutes)."""
    global _jwks_cache, _jwks_fetched_at
    now = datetime.utcnow().timestamp()
    if _jwks_cache and (now - _jwks_fetched_at) < 300:
        return _jwks_cache

    jwks_url = (
        f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"
        "/protocol/openid-connect/certs"
    )
    async with httpx.AsyncClient(verify=settings.keycloak_tls_ca_path or True) as client:
        resp = await client.get(jwks_url, timeout=10)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_fetched_at = now

    return _jwks_cache


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthUser:
    """Extract and validate user from JWT token.

    Verifies the JWT signature against Keycloak's JWKS endpoint,
    checks expiration, audience, and issuer, then extracts
    tenant_id, roles, and user identity from the validated claims.
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    try:
        jwks = await _get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Find matching signing key
        rsa_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = key
                break

        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="JWT signing key not found in JWKS",
            )

        issuer = (
            f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"
        )
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=issuer,
        )

        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing required claim: tenant_id",
            )

        return AuthUser(
            id=payload["sub"],
            email=payload.get("email", ""),
            name=payload.get("name", ""),
            tenant_id=tenant_id,
            roles=payload.get("roles", []),
        )

    except JWTError as e:
        logger.warning("jwt_validation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {e}",
        ) from e
    except httpx.HTTPError as e:
        logger.error("jwks_fetch_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to validate token: identity provider unavailable",
        ) from e


def get_orchestrator() -> PipelineOrchestrator:
    """Return the singleton pipeline orchestrator."""
    if _orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI pipeline not initialized",
        )
    return _orchestrator


def set_orchestrator(orchestrator: PipelineOrchestrator) -> None:
    """Set the singleton orchestrator (called during app startup)."""
    global _orchestrator
    _orchestrator = orchestrator
