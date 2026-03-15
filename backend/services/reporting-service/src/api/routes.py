"""FastAPI routes for report generation, approval, and delivery."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from src.config.settings import settings
from src.models.domain import (
    ApproveReportRequest,
    DeliverReportRequest,
    GenerateReportRequest,
    ReportRecord,
    ReportResponse,
    ReportStatus,
)
from src.pipeline.generator import ReportGenerator

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

# In-memory store for demo; production would use PostgreSQL
_reports: dict[str, ReportRecord] = {}

# Shared generator instance — initialized by lifespan
generator: ReportGenerator | None = None

security = HTTPBearer()

# ── JWKS cache ──
_jwks_cache: dict | None = None
_jwks_fetched_at: float = 0


# ── Auth ──


@dataclass
class AuthUser:
    """Authenticated user extracted from JWT."""

    id: str
    email: str
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

        tenant_id = payload.get("tenant_id") or payload.get("tid")
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing required claim: tenant_id",
            )

        return AuthUser(
            id=payload["sub"],
            email=payload.get("email", ""),
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


# ── Helpers ──


def _get_generator() -> ReportGenerator:
    if generator is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return generator


def _to_response(record: ReportRecord, download_url: str | None = None) -> ReportResponse:
    return ReportResponse(
        id=record.id,
        engagement_id=record.engagement_id,
        title=record.title,
        report_type=record.report_type,
        format=record.format,
        status=record.status,
        generated_at=record.generated_at,
        file_size_bytes=record.file_size_bytes,
        page_count=record.page_count,
        version=record.version,
        download_url=download_url,
    )


# ── Generate ──


@router.post("", status_code=202)
async def generate_report(
    request: GenerateReportRequest,
    user: AuthUser = Depends(get_current_user),
) -> ReportResponse:
    """Queue and generate a new report.

    Returns 202 with the report metadata. Report is generated synchronously
    in this implementation; in production, use Celery or Kafka for async.
    """
    gen = _get_generator()

    record = await gen.generate(
        request,
        tenant_id=user.tenant_id,
        generated_by=user.id,
    )
    _reports[record.id] = record

    logger.info("report_generated", report_id=record.id, tenant_id=user.tenant_id)
    return _to_response(record)


# ── Get Report ──


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    user: AuthUser = Depends(get_current_user),
) -> ReportResponse:
    """Retrieve report metadata."""
    record = _reports.get(report_id)
    if not record or record.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Report not found")
    return _to_response(record)


# ── Download ──


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    """Generate a pre-signed download URL for an approved report.

    Only reports in APPROVED or DELIVERED status can be downloaded.
    """
    record = _reports.get(report_id)
    if not record or record.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Report not found")

    if record.status not in (ReportStatus.APPROVED, ReportStatus.DELIVERED):
        raise HTTPException(
            status_code=403,
            detail=f"Report must be approved before download. Current status: {record.status}",
        )

    if not record.file_path:
        raise HTTPException(status_code=404, detail="Report file not found")

    gen = _get_generator()
    url = gen.get_download_url(user.tenant_id, record.file_path)

    return {"download_url": url, "expires_in_seconds": 900}


# ── Approve ──


@router.post("/{report_id}/approve")
async def approve_report(
    report_id: str,
    request: ApproveReportRequest,
    user: AuthUser = Depends(get_current_user),
) -> ReportResponse:
    """Approve a generated report for delivery.

    Requires the report to be in GENERATED or UNDER_REVIEW status.
    Implements the four-eyes principle — the approver must differ from the generator.
    """
    record = _reports.get(report_id)
    if not record or record.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Report not found")

    if record.status not in (ReportStatus.GENERATED, ReportStatus.UNDER_REVIEW):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve report in status: {record.status}",
        )

    # Four-eyes principle: approver must differ from generator
    if user.id == record.generated_by:
        raise HTTPException(
            status_code=403,
            detail="Four-eyes principle: approver must be different from generator",
        )

    record.status = ReportStatus.APPROVED
    record.approved_by = user.id
    record.approved_at = datetime.utcnow()
    record.updated_at = datetime.utcnow()

    logger.info("report_approved", report_id=report_id, approved_by=user.id)
    return _to_response(record)


# ── Submit for Review ──


@router.post("/{report_id}/review")
async def submit_for_review(
    report_id: str,
    user: AuthUser = Depends(get_current_user),
) -> ReportResponse:
    """Submit a generated report for peer review."""
    record = _reports.get(report_id)
    if not record or record.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Report not found")

    if record.status != ReportStatus.GENERATED:
        raise HTTPException(
            status_code=400,
            detail=f"Only generated reports can be submitted for review. Current: {record.status}",
        )

    record.status = ReportStatus.UNDER_REVIEW
    record.reviewed_by = user.id
    record.reviewed_at = datetime.utcnow()
    record.updated_at = datetime.utcnow()

    logger.info("report_submitted_for_review", report_id=report_id)
    return _to_response(record)


# ── Deliver ──


@router.post("/{report_id}/deliver")
async def deliver_report(
    report_id: str,
    request: DeliverReportRequest,
    user: AuthUser = Depends(get_current_user),
) -> ReportResponse:
    """Mark a report as delivered to the customer.

    Only approved reports can be delivered.
    """
    record = _reports.get(report_id)
    if not record or record.tenant_id != user.tenant_id:
        raise HTTPException(status_code=404, detail="Report not found")

    if record.status != ReportStatus.APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"Only approved reports can be delivered. Current: {record.status}",
        )

    record.status = ReportStatus.DELIVERED
    record.delivered_at = datetime.utcnow()
    record.delivery_method = request.delivery_method
    record.updated_at = datetime.utcnow()

    logger.info(
        "report_delivered",
        report_id=report_id,
        method=request.delivery_method,
    )
    return _to_response(record)


# ── List Reports ──


@router.get("")
async def list_reports(
    user: AuthUser = Depends(get_current_user),
    engagement_id: str | None = None,
    status: ReportStatus | None = None,
) -> list[ReportResponse]:
    """List reports for a tenant, optionally filtered by engagement or status."""
    results = []
    for record in _reports.values():
        if record.tenant_id != user.tenant_id:
            continue
        if engagement_id and record.engagement_id != engagement_id:
            continue
        if status and record.status != status:
            continue
        results.append(_to_response(record))
    return results
