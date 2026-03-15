"""FastAPI dependency injection for auth and services."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.pipelines.orchestrator import PipelineOrchestrator

security = HTTPBearer()

# Singleton orchestrator instance (initialized on app startup)
_orchestrator: PipelineOrchestrator | None = None


@dataclass
class AuthUser:
    """Authenticated user extracted from JWT."""

    id: str
    email: str
    name: str
    tenant_id: str
    roles: list[str]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthUser:
    """Extract and validate user from JWT token.

    In production, this verifies the JWT against Keycloak's JWKS endpoint
    and extracts the tenant_id, roles, and user identity.
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    # Production: Verify JWT signature, check expiration, extract claims.
    # Stub implementation for development:
    return AuthUser(
        id="analyst-001",
        email="analyst@vapt-platform.local",
        name="Test Analyst",
        tenant_id="tenant-001",
        roles=["analyst"],
    )


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
