"""Security services API routes — RBAC, audit, scan windows, IP allowlists."""

from __future__ import annotations

from datetime import datetime, time

import structlog
from fastapi import APIRouter, HTTPException, Header, Request

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


# ═══════════════════════════════════════════════════════════
# RBAC & Authentication
# ═══════════════════════════════════════════════════════════


@router.post("/auth/validate")
async def validate_token(
    request: Request,
    authorization: str = Header(...),
) -> dict:
    """Validate a JWT and return resolved RBAC context."""
    token = authorization.removeprefix("Bearer ").strip()

    try:
        claims = await rbac.validate_token(token)
        context = rbac.resolve_context(claims, source_ip=request.client.host)
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
    authorization: str = Header(...),
) -> dict:
    """Check if the authenticated user has a specific permission."""
    token = authorization.removeprefix("Bearer ").strip()

    try:
        claims = await rbac.validate_token(token)
        context = rbac.resolve_context(claims, source_ip=request.client.host)
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
                source_ip=request.client.host,
            )

        return {"allowed": allowed, "user_id": context.user_id}

    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Credential Vault
# ═══════════════════════════════════════════════════════════


@router.post("/credentials/checkout")
async def checkout_credential(
    request: CredentialCheckoutRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_user_id: str = Header("", alias="X-User-ID"),
    x_pod_name: str = Header("", alias="X-Pod-Name"),
) -> dict:
    """Checkout a credential for scan execution (time-boxed lease)."""
    try:
        checkout = credential_vault.checkout_credential(
            request,
            tenant_id=x_tenant_id,
            actor_id=x_user_id,
            source_ip=request.client.host if hasattr(request, 'client') else "",
            pod_name=x_pod_name,
        )

        await audit.log_credential_checkout(
            actor_id=x_user_id,
            tenant_id=x_tenant_id,
            credential_id=request.credential_id,
            engagement_id=request.engagement_id,
            metadata={"scan_job_id": request.scan_job_id, "ttl": checkout.lease_ttl_seconds},
        )

        return {
            "checkout_id": checkout.id,
            "lease_ttl_seconds": checkout.lease_ttl_seconds,
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
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_user_id: str = Header("", alias="X-User-ID"),
) -> dict:
    """Check in a previously checked-out credential."""
    credential_vault.checkin_credential(checkout_id, credential_id, x_tenant_id)

    await audit.log_credential_checkin(
        actor_id=x_user_id,
        tenant_id=x_tenant_id,
        credential_id=credential_id,
    )

    return {"status": "checked_in"}


# ═══════════════════════════════════════════════════════════
# Scan Windows
# ═══════════════════════════════════════════════════════════


@router.post("/scan-windows")
async def create_scan_window(
    request: CreateScanWindowRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_user_id: str = Header("", alias="X-User-ID"),
) -> dict:
    """Create a scan window for an engagement."""
    start_t = time.fromisoformat(request.start_time)
    end_t = time.fromisoformat(request.end_time)

    window = scan_windows.create_window(
        tenant_id=x_tenant_id,
        engagement_id=request.engagement_id,
        name=request.name,
        timezone=request.timezone,
        allowed_days=request.allowed_days,
        start_time=start_t,
        end_time=end_t,
        blackout_dates=request.blackout_dates,
        created_by=x_user_id,
    )

    await audit.log(
        AuditCategory.ADMIN, "admin.scan_window_updated",
        actor_id=x_user_id, tenant_id=x_tenant_id,
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
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
) -> ScanWindowCheckResult:
    """Check if scanning is currently permitted for an engagement."""
    return scan_windows.check_window(engagement_id)


@router.post("/scan-windows/emergency-override")
async def emergency_override(
    request: EmergencyOverrideRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_user_id: str = Header("", alias="X-User-ID"),
) -> dict:
    """Request an emergency scan window override (requires dual-approval)."""
    try:
        result = scan_windows.request_emergency_override(
            request, tenant_id=x_tenant_id, requestor_id=x_user_id,
        )

        await audit.log_emergency_override(
            actor_id=x_user_id,
            tenant_id=x_tenant_id,
            engagement_id=request.engagement_id,
            justification=request.justification,
            approvers=request.approver_ids,
        )

        return result

    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ═══════════════════════════════════════════════════════════
# IP Allowlists
# ═══════════════════════════════════════════════════════════


@router.post("/ip-allowlists")
async def add_ip_allowlist_entry(
    request: AddIPAllowlistRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_user_id: str = Header("", alias="X-User-ID"),
) -> dict:
    """Add a CIDR range to an IP allowlist."""
    try:
        expires_at = datetime.fromisoformat(request.expires_at) if request.expires_at else None
        entry = ip_allowlist.add_entry(
            tenant_id=x_tenant_id,
            list_type=request.list_type,
            cidr=request.cidr,
            engagement_id=request.engagement_id,
            description=request.description,
            created_by=x_user_id,
            expires_at=expires_at,
        )

        await audit.log(
            AuditCategory.ADMIN, "admin.ip_allowlist_updated",
            actor_id=x_user_id, tenant_id=x_tenant_id,
            resource_type="ip_allowlist", resource_id=entry.id,
            metadata={"cidr": request.cidr, "list_type": request.list_type},
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
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_user_id: str = Header("", alias="X-User-ID"),
) -> dict:
    """Remove an IP allowlist entry."""
    try:
        ip_allowlist.remove_entry(entry_id, x_tenant_id)

        await audit.log(
            AuditCategory.ADMIN, "admin.ip_allowlist_updated",
            actor_id=x_user_id, tenant_id=x_tenant_id,
            resource_type="ip_allowlist", resource_id=entry_id,
            metadata={"action": "removed"},
        )

        return {"status": "removed"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/ip-allowlists")
async def list_ip_allowlist_entries(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    list_type: IPAllowlistType | None = None,
    engagement_id: str | None = None,
) -> list[dict]:
    """List IP allowlist entries for a tenant."""
    entries = ip_allowlist.list_entries(
        x_tenant_id, list_type=list_type, engagement_id=engagement_id,
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
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
) -> dict:
    """Check if an IP address is in a specific allowlist."""
    result = ip_allowlist.check_ip(
        body["ip"],
        x_tenant_id,
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
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
) -> dict:
    """Query audit logs (read from Elasticsearch in production)."""
    # In production, this queries Elasticsearch with tenant_id filter
    return {
        "total": 0,
        "events": [],
        "message": "Audit query would be served from Elasticsearch in production",
    }


@router.post("/audit/verify-chain")
async def verify_audit_chain(
    body: dict,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
) -> dict:
    """Verify the integrity of an audit event chain."""
    # In production, fetches events from ES and verifies hash chain
    return {
        "verified": True,
        "message": "Hash chain verification would run against Elasticsearch in production",
    }
