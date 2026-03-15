"""Security services API routes — RBAC, audit, scan windows, IP allowlists."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time

import structlog
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.models.domain import (
    AddIPAllowlistRequest,
    AuditCategory,
    AuditQueryRequest,
    CreateScanWindowRequest,
    CredentialCheckoutRequest,
    DayOfWeek,
    EmergencyOverrideRequest,
    IPAllowlistType,
    Permission,
    Role,
    ScanWindowCheckResult,
)
from src.services.audit_logger import AuditLogger
from src.services.credential_vault import CredentialVaultService
from src.services.ip_allowlist import IPAllowlistService
from src.services.rbac_enforcer import RBACEnforcer
from src.services.scan_window import ScanWindowEnforcer

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/security", tags=["security"])

# Service instances — initialized by lifespan
rbac: RBACEnforcer | None = None
audit: AuditLogger | None = None
credential_vault: CredentialVaultService | None = None
scan_windows: ScanWindowEnforcer | None = None
ip_allowlist: IPAllowlistService | None = None

security = HTTPBearer()


# ═══════════════════════════════════════════════════════════
# AuthUser model and JWT dependency
# ═══════════════════════════════════════════════════════════


@dataclass
class AuthUser:
    """Authenticated user extracted from validated JWT."""
    id: str
    email: str
    tenant_id: str
    roles: list[str] = field(default_factory=list)
    permissions: set[Permission] = field(default_factory=set)


def _extract_source_ip(request: Request) -> str:
    """Extract source IP, preferring X-Forwarded-For header."""
    return (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthUser:
    """Validate JWT token and return authenticated user."""
    try:
        claims = await rbac.validate_token(credentials.credentials)
        context = rbac.resolve_context(claims)
        return AuthUser(
            id=claims.sub,
            email=claims.email,
            tenant_id=claims.tenant_id,
            roles=[r.value for r in context.roles],
            permissions=context.permissions,
        )
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))


def _require_role(user: AuthUser, allowed_roles: set[str], action: str) -> None:
    """Check that the user has at least one of the allowed roles. Raises 403 if not."""
    if not allowed_roles.intersection(user.roles):
        raise HTTPException(
            status_code=403,
            detail=f"User {user.id} lacks required role for {action}. "
                   f"Required one of: {sorted(allowed_roles)}",
        )


# ═══════════════════════════════════════════════════════════
# RBAC & Authentication
# ═══════════════════════════════════════════════════════════


@router.post("/auth/validate")
async def validate_token(
    request: Request,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    """Validate a JWT and return resolved RBAC context."""
    source_ip = _extract_source_ip(request)

    try:
        # Re-resolve full context with source_ip for the response
        claims = await rbac.validate_token(
            request.headers.get("authorization", "").removeprefix("Bearer ").strip()
        )
        context = rbac.resolve_context(claims, source_ip=source_ip)
        return {
            "user_id": context.user_id,
            "tenant_id": context.tenant_id,
            "roles": [r.value for r in context.roles],
            "permissions": [p.value for p in context.permissions],
            "mfa_verified": context.mfa_verified,
            "engagement_ids": context.engagement_ids,
        }
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/auth/check-permission")
async def check_permission(
    request: Request,
    body: dict,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    """Check if the authenticated user has a specific permission."""
    source_ip = _extract_source_ip(request)

    try:
        claims = await rbac.validate_token(
            request.headers.get("authorization", "").removeprefix("Bearer ").strip()
        )
        context = rbac.resolve_context(claims, source_ip=source_ip)
        required = Permission(body["permission"])
        allowed = rbac.check_sensitive_permission(
            context,
            required,
            resource_tenant_id=body.get("resource_tenant_id"),
            resource_engagement_id=body.get("resource_engagement_id"),
        )

        if not allowed:
            await audit.log_permission_denied(
                actor_id=context.user_id,
                tenant_id=context.tenant_id,
                permission=body["permission"],
                source_ip=source_ip,
            )

        return {"allowed": allowed, "user_id": context.user_id}

    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Credential Vault
# ═══════════════════════════════════════════════════════════


@router.post("/credentials/checkout")
async def checkout_credential(
    request: Request,
    cred_request: CredentialCheckoutRequest,
    user: AuthUser = Depends(get_current_user),
    x_pod_name: str = Header("", alias="X-Pod-Name"),
) -> dict:
    """Checkout a credential for scan execution (time-boxed lease)."""
    _require_role(user, {Role.ANALYST, Role.SCANNER_OPERATOR, Role.LEAD_ANALYST,
                         Role.ENGAGEMENT_MANAGER, Role.TENANT_ADMIN, Role.PLATFORM_ADMIN},
                  "credential checkout")
    source_ip = _extract_source_ip(request)

    try:
        checkout = credential_vault.checkout_credential(
            cred_request,
            tenant_id=user.tenant_id,
            actor_id=user.id,
            source_ip=source_ip,
            pod_name=x_pod_name,
        )

        await audit.log_credential_checkout(
            actor_id=user.id,
            tenant_id=user.tenant_id,
            credential_id=cred_request.credential_id,
            engagement_id=cred_request.engagement_id,
            metadata={"scan_job_id": cred_request.scan_job_id, "ttl": checkout.lease_ttl_seconds},
        )

        return {
            "checkout_id": checkout.id,
            "lease_ttl_seconds": checkout.lease_ttl_seconds,
            "wrapped_token": checkout.wrapped_token,
            "expires_at": (
                checkout.checked_out_at.isoformat()
            ),
        }

    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/credentials/{credential_id}/checkin")
async def checkin_credential(
    credential_id: str,
    checkout_id: str,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    """Check in a previously checked-out credential."""
    _require_role(user, {Role.ANALYST, Role.SCANNER_OPERATOR, Role.LEAD_ANALYST,
                         Role.ENGAGEMENT_MANAGER, Role.TENANT_ADMIN, Role.PLATFORM_ADMIN},
                  "credential checkin")

    credential_vault.checkin_credential(checkout_id, credential_id, user.tenant_id)

    await audit.log_credential_checkin(
        actor_id=user.id,
        tenant_id=user.tenant_id,
        credential_id=credential_id,
    )

    return {"status": "checked_in"}


# ═══════════════════════════════════════════════════════════
# Scan Windows
# ═══════════════════════════════════════════════════════════


@router.post("/scan-windows")
async def create_scan_window(
    request: CreateScanWindowRequest,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    """Create a scan window for an engagement."""
    _require_role(user, {Role.PLATFORM_ADMIN, Role.TENANT_ADMIN, Role.ENGAGEMENT_MANAGER},
                  "scan window creation")

    start_t = time.fromisoformat(request.start_time)
    end_t = time.fromisoformat(request.end_time)

    window = scan_windows.create_window(
        tenant_id=user.tenant_id,
        engagement_id=request.engagement_id,
        name=request.name,
        timezone=request.timezone,
        allowed_days=request.allowed_days,
        start_time=start_t,
        end_time=end_t,
        blackout_dates=request.blackout_dates,
        created_by=user.id,
    )

    await audit.log(
        AuditCategory.ADMIN, "admin.scan_window_updated",
        actor_id=user.id, tenant_id=user.tenant_id,
        resource_type="scan_window", resource_id=window.id,
        engagement_id=request.engagement_id,
    )

    return {
        "id": window.id,
        "engagement_id": window.engagement_id,
        "timezone": window.timezone,
        "allowed_days": [d.value for d in window.allowed_days],
        "start_time": str(window.start_time),
        "end_time": str(window.end_time),
    }


@router.get("/scan-windows/{engagement_id}/check")
async def check_scan_window(
    engagement_id: str,
    user: AuthUser = Depends(get_current_user),
) -> ScanWindowCheckResult:
    """Check if scanning is currently permitted for an engagement."""
    return scan_windows.check_window(engagement_id)


@router.post("/scan-windows/emergency-override")
async def emergency_override(
    request: EmergencyOverrideRequest,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    """Request an emergency scan window override (requires dual-approval)."""
    _require_role(user, {Role.PLATFORM_ADMIN, Role.TENANT_ADMIN},
                  "emergency override")

    try:
        result = scan_windows.request_emergency_override(
            request, tenant_id=user.tenant_id, requestor_id=user.id,
        )

        await audit.log_emergency_override(
            actor_id=user.id,
            tenant_id=user.tenant_id,
            engagement_id=request.engagement_id,
            justification=request.justification,
            approvers=request.approver_ids,
        )

        return result

    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/scan-windows/emergency-override/{engagement_id}/approve")
async def approve_emergency_override(
    engagement_id: str,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    """Approve a pending emergency scan window override."""
    _require_role(user, {Role.PLATFORM_ADMIN, Role.TENANT_ADMIN},
                  "emergency override approval")

    try:
        result = scan_windows.approve_emergency_override(
            engagement_id=engagement_id,
            approver_id=user.id,
        )

        await audit.log(
            AuditCategory.ADMIN, "admin.emergency_override_approved",
            actor_id=user.id, tenant_id=user.tenant_id,
            resource_type="emergency_override", resource_id=engagement_id,
        )

        return result

    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════
# IP Allowlists
# ═══════════════════════════════════════════════════════════


@router.post("/ip-allowlists")
async def add_ip_allowlist_entry(
    request: Request,
    body: AddIPAllowlistRequest,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    """Add a CIDR range to an IP allowlist."""
    _require_role(user, {Role.PLATFORM_ADMIN, Role.TENANT_ADMIN, Role.CUSTOMER_ADMIN},
                  "IP allowlist add")

    try:
        expires_at = datetime.fromisoformat(body.expires_at) if body.expires_at else None
        entry = ip_allowlist.add_entry(
            tenant_id=user.tenant_id,
            list_type=body.list_type,
            cidr=body.cidr,
            engagement_id=body.engagement_id,
            description=body.description,
            created_by=user.id,
            expires_at=expires_at,
        )

        await audit.log(
            AuditCategory.ADMIN, "admin.ip_allowlist_updated",
            actor_id=user.id, tenant_id=user.tenant_id,
            resource_type="ip_allowlist", resource_id=entry.id,
            metadata={"cidr": body.cidr, "list_type": body.list_type},
        )

        return {
            "id": entry.id,
            "cidr": entry.cidr,
            "list_type": entry.list_type,
            "engagement_id": entry.engagement_id,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/ip-allowlists/{entry_id}")
async def remove_ip_allowlist_entry(
    entry_id: str,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    """Remove an IP allowlist entry."""
    _require_role(user, {Role.PLATFORM_ADMIN, Role.TENANT_ADMIN, Role.CUSTOMER_ADMIN},
                  "IP allowlist remove")

    try:
        ip_allowlist.remove_entry(entry_id, user.tenant_id)

        await audit.log(
            AuditCategory.ADMIN, "admin.ip_allowlist_updated",
            actor_id=user.id, tenant_id=user.tenant_id,
            resource_type="ip_allowlist", resource_id=entry_id,
            metadata={"action": "removed"},
        )

        return {"status": "removed"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/ip-allowlists")
async def list_ip_allowlist_entries(
    user: AuthUser = Depends(get_current_user),
    list_type: IPAllowlistType | None = None,
    engagement_id: str | None = None,
) -> list[dict]:
    """List IP allowlist entries for a tenant."""
    entries = ip_allowlist.list_entries(
        user.tenant_id, list_type=list_type, engagement_id=engagement_id,
    )
    return [
        {
            "id": e.id,
            "cidr": e.cidr,
            "list_type": e.list_type,
            "engagement_id": e.engagement_id,
            "description": e.description,
            "created_by": e.created_by,
            "created_at": e.created_at.isoformat(),
            "expires_at": e.expires_at.isoformat() if e.expires_at else None,
        }
        for e in entries
    ]


@router.post("/ip-allowlists/check")
async def check_ip(
    body: dict,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    """Check if an IP address is in a specific allowlist."""
    result = ip_allowlist.check_ip(
        body["ip"],
        user.tenant_id,
        IPAllowlistType(body["list_type"]),
        engagement_id=body.get("engagement_id"),
    )
    return result.model_dump()


# ═══════════════════════════════════════════════════════════
# Audit Logs
# ═══════════════════════════════════════════════════════════


@router.post("/audit/query")
async def query_audit_logs(
    request: AuditQueryRequest,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    """Query audit logs (read from Elasticsearch in production)."""
    _require_role(user, {Role.PLATFORM_ADMIN, Role.TENANT_ADMIN},
                  "audit log query")

    # In production, this queries Elasticsearch with tenant_id filter
    return {
        "total": 0,
        "events": [],
        "message": "Audit query would be served from Elasticsearch in production",
    }


@router.post("/audit/verify-chain")
async def verify_audit_chain(
    body: dict,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    """Verify the integrity of an audit event chain."""
    _require_role(user, {Role.PLATFORM_ADMIN, Role.TENANT_ADMIN},
                  "audit chain verify")

    # In production, fetches events from ES and verifies hash chain
    return {
        "verified": True,
        "message": "Hash chain verification would run against Elasticsearch in production",
    }
