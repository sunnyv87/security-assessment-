"""RBAC enforcement service — JWT validation, permission checks, tenant boundary."""

from __future__ import annotations

import json
from datetime import datetime

import httpx
import structlog
from jose import JWTError, jwt
from redis import asyncio as aioredis

from src.config.settings import settings
from src.models.domain import (
    Permission,
    RBACContext,
    Role,
    ROLE_PERMISSIONS,
    TokenClaims,
)

logger = structlog.get_logger()


class RBACEnforcer:
    """Validates JWTs, resolves roles/permissions, enforces tenant boundaries."""

    def __init__(self) -> None:
        self._jwks_cache: dict | None = None
        self._jwks_fetched_at: float = 0
        self._redis: aioredis.Redis | None = None

    async def init(self) -> None:
        self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()

    # ── JWT Validation ──

    async def validate_token(self, token: str) -> TokenClaims:
        """Validate JWT signature and extract claims.

        Raises:
            PermissionError: If token is invalid, expired, or missing required claims.
        """
        jwks = await self._get_jwks()

        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            # Find matching key
            rsa_key = None
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    rsa_key = key
                    break

            if not rsa_key:
                raise PermissionError("JWT signing key not found in JWKS")

            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=[settings.jwt_algorithm],
                audience=settings.jwt_audience,
                issuer=f"{settings.keycloak_url}/realms/{settings.keycloak_realm}",
            )

            # Extract tenant_id (required claim)
            tenant_id = payload.get("tenant_id")
            if not tenant_id:
                raise PermissionError("Missing required claim: tenant_id")

            # Require MFA for sensitive operations
            mfa_verified = payload.get("mfa_verified", False)

            return TokenClaims(
                sub=payload["sub"],
                iss=payload["iss"],
                aud=payload.get("aud", ""),
                tenant_id=tenant_id,
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                email=payload.get("email", ""),
                name=payload.get("name", ""),
                mfa_verified=mfa_verified,
                engagement_ids=payload.get("engagement_ids", []),
                iat=payload.get("iat", 0),
                exp=payload.get("exp", 0),
            )

        except JWTError as e:
            raise PermissionError(f"Invalid JWT: {e}") from e

    # ── Permission Resolution ──

    def resolve_context(self, claims: TokenClaims, source_ip: str = "") -> RBACContext:
        """Resolve JWT claims into a full RBAC context with permissions."""
        roles = []
        all_permissions: set[Permission] = set()

        for role_name in claims.roles:
            try:
                role = Role(role_name)
                roles.append(role)
                role_perms = ROLE_PERMISSIONS.get(role, set())
                all_permissions.update(role_perms)
            except ValueError:
                logger.error(
                    "unknown_role_rejected",
                    role=role_name,
                    user_id=claims.sub,
                    tenant_id=claims.tenant_id,
                )
                raise PermissionError(
                    f"Unknown role '{role_name}' in JWT for user {claims.sub}. "
                    f"Token contains invalid role claims and has been rejected."
                )

        # Add explicit permissions from token (for fine-grained overrides)
        for perm_name in claims.permissions:
            try:
                all_permissions.add(Permission(perm_name))
            except ValueError:
                pass

        return RBACContext(
            user_id=claims.sub,
            tenant_id=claims.tenant_id,
            roles=roles,
            permissions=all_permissions,
            engagement_ids=claims.engagement_ids,
            mfa_verified=claims.mfa_verified,
            source_ip=source_ip,
        )

    # ── Authorization Checks ──

    def check_permission(
        self,
        context: RBACContext,
        required_permission: Permission,
        *,
        require_mfa: bool = False,
        resource_tenant_id: str | None = None,
        resource_engagement_id: str | None = None,
    ) -> bool:
        """Check if the RBAC context grants the required permission.

        Enforces:
        1. Permission exists in resolved role permissions
        2. Tenant boundary (user can only access own tenant's resources)
        3. Engagement assignment (analyst can only access assigned engagements)
        4. MFA requirement for sensitive operations
        """
        # Tenant boundary enforcement
        if resource_tenant_id and resource_tenant_id != context.tenant_id:
            # Platform admins can cross tenant boundaries
            if Role.PLATFORM_ADMIN not in context.roles:
                logger.warning(
                    "cross_tenant_access_denied",
                    user_id=context.user_id,
                    user_tenant=context.tenant_id,
                    resource_tenant=resource_tenant_id,
                )
                return False

        # MFA check
        if require_mfa and not context.mfa_verified:
            logger.warning(
                "mfa_required",
                user_id=context.user_id,
                permission=required_permission,
            )
            return False

        # Permission check
        if required_permission not in context.permissions:
            return False

        # Engagement assignment check (for analyst/lead_analyst roles only)
        if resource_engagement_id and context.engagement_ids:
            is_analyst_role = any(
                r in (Role.ANALYST, Role.LEAD_ANALYST) for r in context.roles
            )
            if is_analyst_role and resource_engagement_id not in context.engagement_ids:
                logger.warning(
                    "engagement_not_assigned",
                    user_id=context.user_id,
                    engagement_id=resource_engagement_id,
                )
                return False

        return True

    def require_permission(
        self,
        context: RBACContext,
        required_permission: Permission,
        **kwargs,
    ) -> None:
        """Like check_permission but raises PermissionError on failure."""
        if not self.check_permission(context, required_permission, **kwargs):
            raise PermissionError(
                f"User {context.user_id} lacks permission {required_permission} "
                f"in tenant {context.tenant_id}"
            )

    # ── Sensitive Operation Permissions ──

    # Operations requiring MFA
    MFA_REQUIRED_PERMISSIONS: set[Permission] = {
        Permission.CREDENTIAL_CHECKOUT,
        Permission.CREDENTIAL_DELETE,
        Permission.ADMIN_MANAGE_TENANTS,
        Permission.ADMIN_EMERGENCY_OVERRIDE,
        Permission.REPORT_DELIVER,
        Permission.ENGAGEMENT_DELETE,
    }

    def check_sensitive_permission(
        self,
        context: RBACContext,
        required_permission: Permission,
        **kwargs,
    ) -> bool:
        """Check permission with automatic MFA enforcement for sensitive operations."""
        require_mfa = required_permission in self.MFA_REQUIRED_PERMISSIONS
        return self.check_permission(
            context, required_permission, require_mfa=require_mfa, **kwargs
        )

    # ── JWKS Caching ──

    async def _get_jwks(self) -> dict:
        """Fetch and cache Keycloak JWKS (refresh every 5 minutes)."""
        now = datetime.utcnow().timestamp()
        if self._jwks_cache and (now - self._jwks_fetched_at) < 300:
            return self._jwks_cache

        # Try Redis cache first
        if self._redis:
            cached = await self._redis.get("jwks:keycloak")
            if cached:
                self._jwks_cache = json.loads(cached)
                self._jwks_fetched_at = now
                return self._jwks_cache

        # Fetch from Keycloak — use CA cert for TLS verification
        ssl_verify = settings.keycloak_tls_ca_path if settings.keycloak_tls_ca_path else True
        async with httpx.AsyncClient(verify=ssl_verify) as client:
            resp = await client.get(settings.jwks_url, timeout=10)
            resp.raise_for_status()
            self._jwks_cache = resp.json()
            self._jwks_fetched_at = now

        # Cache in Redis
        if self._redis:
            await self._redis.set(
                "jwks:keycloak",
                json.dumps(self._jwks_cache),
                ex=300,
            )

        return self._jwks_cache
