"""Tenant isolation middleware — enforces tenant boundaries at every layer."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that enforces tenant isolation on every request.

    Guarantees:
    1. Every request has a validated tenant_id (from JWT or header)
    2. Tenant context is injected into request state for downstream use
    3. Cross-tenant access is blocked (logged as security event)
    4. Database queries automatically scoped to tenant
    """

    async def dispatch(self, request: Request, call_next):
        # Skip health checks
        if request.url.path in ("/health",):
            return await call_next(request)

        # Extract tenant_id from JWT claims (set by RBAC middleware)
        tenant_id = getattr(request.state, "tenant_id", None)
        if not tenant_id:
            tenant_id = request.headers.get("X-Tenant-ID")

        if not tenant_id:
            raise HTTPException(
                status_code=401,
                detail="Missing tenant context",
            )

        # Inject tenant context into request state
        request.state.tenant_id = tenant_id

        # Validate X-Tenant-ID header matches JWT claim
        header_tenant = request.headers.get("X-Tenant-ID")
        jwt_tenant = getattr(request.state, "jwt_tenant_id", None)

        # If header is provided, JWT claim MUST also be present and match
        if header_tenant and not jwt_tenant:
            logger.error(
                "tenant_id_header_without_jwt_claim",
                header_tenant=header_tenant,
                path=request.url.path,
            )
            raise HTTPException(
                status_code=403,
                detail="Tenant ID header provided but JWT claim missing",
            )

        if header_tenant and jwt_tenant and header_tenant != jwt_tenant:
            logger.error(
                "tenant_id_mismatch",
                header_tenant=header_tenant,
                jwt_tenant=jwt_tenant,
                path=request.url.path,
            )
            raise HTTPException(
                status_code=403,
                detail="Tenant ID mismatch between header and JWT",
            )

        response = await call_next(request)

        # Add tenant context to response headers for tracing
        response.headers["X-Tenant-ID"] = tenant_id
        return response


# ── PostgreSQL Row-Level Security (RLS) Policy Definitions ──
# These are applied during database migration, not at runtime

RLS_POLICY_SQL = """
-- ═══════════════════════════════════════════════════════════
-- ROW-LEVEL SECURITY POLICIES FOR TENANT ISOLATION
-- Applied to every tenant-scoped table
-- ═══════════════════════════════════════════════════════════

-- Enable RLS on all tenant-scoped tables
ALTER TABLE engagements ENABLE ROW LEVEL SECURITY;
ALTER TABLE scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE work_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE scan_windows ENABLE ROW LEVEL SECURITY;
ALTER TABLE ip_allowlists ENABLE ROW LEVEL SECURITY;

-- Force RLS even for table owners (defense in depth)
ALTER TABLE engagements FORCE ROW LEVEL SECURITY;
ALTER TABLE scans FORCE ROW LEVEL SECURITY;
ALTER TABLE findings FORCE ROW LEVEL SECURITY;
ALTER TABLE reports FORCE ROW LEVEL SECURITY;
ALTER TABLE credentials FORCE ROW LEVEL SECURITY;
ALTER TABLE work_items FORCE ROW LEVEL SECURITY;
ALTER TABLE assets FORCE ROW LEVEL SECURITY;
ALTER TABLE audit_events FORCE ROW LEVEL SECURITY;
ALTER TABLE scan_windows FORCE ROW LEVEL SECURITY;
ALTER TABLE ip_allowlists FORCE ROW LEVEL SECURITY;

-- ── Engagement Policies ──
CREATE POLICY tenant_isolation_engagements ON engagements
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- ── Scan Policies ──
CREATE POLICY tenant_isolation_scans ON scans
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- ── Finding Policies ──
CREATE POLICY tenant_isolation_findings ON findings
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- ── Report Policies ──
CREATE POLICY tenant_isolation_reports ON reports
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- ── Credential Policies (metadata only — secrets in Vault) ──
CREATE POLICY tenant_isolation_credentials ON credentials
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- ── Work Item Policies ──
CREATE POLICY tenant_isolation_work_items ON work_items
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- ── Asset Policies ──
CREATE POLICY tenant_isolation_assets ON assets
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- ── Audit Event Policies ──
CREATE POLICY tenant_isolation_audit ON audit_events
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- ── Scan Window Policies ──
CREATE POLICY tenant_isolation_scan_windows ON scan_windows
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- ── IP Allowlist Policies ──
CREATE POLICY tenant_isolation_ip_allowlists ON ip_allowlists
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- ── Platform admin bypass policy (for cross-tenant operations) ──
-- Only applied to roles with platform_admin flag
CREATE POLICY platform_admin_bypass_engagements ON engagements
    TO vapt_admin
    USING (true)
    WITH CHECK (true);

-- ── Indexes (tenant_id first for RLS performance) ──
CREATE INDEX idx_engagements_tenant ON engagements(tenant_id, status);
CREATE INDEX idx_scans_tenant ON scans(tenant_id, status, created_at DESC);
CREATE INDEX idx_findings_tenant ON findings(tenant_id, severity, status);
CREATE INDEX idx_reports_tenant ON reports(tenant_id, status, created_at DESC);
CREATE INDEX idx_credentials_tenant ON credentials(tenant_id, engagement_id);
CREATE INDEX idx_work_items_tenant ON work_items(tenant_id, status, priority DESC);
CREATE INDEX idx_assets_tenant ON assets(tenant_id);
CREATE INDEX idx_audit_tenant ON audit_events(tenant_id, timestamp DESC);
CREATE INDEX idx_scan_windows_tenant ON scan_windows(tenant_id, engagement_id);
CREATE INDEX idx_ip_allowlists_tenant ON ip_allowlists(tenant_id, list_type, is_active);
"""


class TenantAwareDatabaseSession:
    """Context manager that injects tenant_id into PostgreSQL session.

    Usage:
        async with TenantAwareDatabaseSession(session, tenant_id) as s:
            result = await s.execute(query)  # RLS automatically applied
    """

    def __init__(self, session, tenant_id: str):
        self._session = session
        self._tenant_id = tenant_id

    async def __aenter__(self):
        # Set tenant context for RLS
        await self._session.execute(
            f"SET LOCAL app.current_tenant_id = :tid",
            {"tid": self._tenant_id},
        )
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Reset context (transaction boundary handles this, but be explicit)
        await self._session.execute("RESET app.current_tenant_id")
