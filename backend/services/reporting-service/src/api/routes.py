"""FastAPI routes for report generation, approval, and delivery."""

from __future__ import annotations

from datetime import datetime

import structlog
from fastapi import APIRouter, HTTPException, Header

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
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_user_id: str = Header("", alias="X-User-ID"),
) -> ReportResponse:
    """Queue and generate a new report.

    Returns 202 with the report metadata. Report is generated synchronously
    in this implementation; in production, use Celery or Kafka for async.
    """
    gen = _get_generator()

    record = await gen.generate(
        request,
        tenant_id=x_tenant_id,
        generated_by=x_user_id,
    )
    _reports[record.id] = record

    logger.info("report_generated", report_id=record.id, tenant_id=x_tenant_id)
    return _to_response(record)


# ── Get Report ──


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
) -> ReportResponse:
    """Retrieve report metadata."""
    record = _reports.get(report_id)
    if not record or record.tenant_id != x_tenant_id:
        raise HTTPException(status_code=404, detail="Report not found")
    return _to_response(record)


# ── Download ──


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
) -> dict:
    """Generate a pre-signed download URL for an approved report.

    Only reports in APPROVED or DELIVERED status can be downloaded.
    """
    record = _reports.get(report_id)
    if not record or record.tenant_id != x_tenant_id:
        raise HTTPException(status_code=404, detail="Report not found")

    if record.status not in (ReportStatus.APPROVED, ReportStatus.DELIVERED):
        raise HTTPException(
            status_code=403,
            detail=f"Report must be approved before download. Current status: {record.status}",
        )

    if not record.file_path:
        raise HTTPException(status_code=404, detail="Report file not found")

    gen = _get_generator()
    url = gen.get_download_url(x_tenant_id, record.file_path)

    return {"download_url": url, "expires_in_seconds": 900}


# ── Approve ──


@router.post("/{report_id}/approve")
async def approve_report(
    report_id: str,
    request: ApproveReportRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_user_id: str = Header("", alias="X-User-ID"),
) -> ReportResponse:
    """Approve a generated report for delivery.

    Requires the report to be in GENERATED or UNDER_REVIEW status.
    Implements the four-eyes principle — the approver must differ from the generator.
    """
    record = _reports.get(report_id)
    if not record or record.tenant_id != x_tenant_id:
        raise HTTPException(status_code=404, detail="Report not found")

    if record.status not in (ReportStatus.GENERATED, ReportStatus.UNDER_REVIEW):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve report in status: {record.status}",
        )

    # Four-eyes principle: approver must differ from generator
    if x_user_id and x_user_id == record.generated_by:
        raise HTTPException(
            status_code=403,
            detail="Four-eyes principle: approver must be different from generator",
        )

    record.status = ReportStatus.APPROVED
    record.approved_by = x_user_id
    record.approved_at = datetime.utcnow()
    record.updated_at = datetime.utcnow()

    logger.info("report_approved", report_id=report_id, approved_by=x_user_id)
    return _to_response(record)


# ── Submit for Review ──


@router.post("/{report_id}/review")
async def submit_for_review(
    report_id: str,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_user_id: str = Header("", alias="X-User-ID"),
) -> ReportResponse:
    """Submit a generated report for peer review."""
    record = _reports.get(report_id)
    if not record or record.tenant_id != x_tenant_id:
        raise HTTPException(status_code=404, detail="Report not found")

    if record.status != ReportStatus.GENERATED:
        raise HTTPException(
            status_code=400,
            detail=f"Only generated reports can be submitted for review. Current: {record.status}",
        )

    record.status = ReportStatus.UNDER_REVIEW
    record.reviewed_by = x_user_id
    record.reviewed_at = datetime.utcnow()
    record.updated_at = datetime.utcnow()

    logger.info("report_submitted_for_review", report_id=report_id)
    return _to_response(record)


# ── Deliver ──


@router.post("/{report_id}/deliver")
async def deliver_report(
    report_id: str,
    request: DeliverReportRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_user_id: str = Header("", alias="X-User-ID"),
) -> ReportResponse:
    """Mark a report as delivered to the customer.

    Only approved reports can be delivered.
    """
    record = _reports.get(report_id)
    if not record or record.tenant_id != x_tenant_id:
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
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    engagement_id: str | None = None,
    status: ReportStatus | None = None,
) -> list[ReportResponse]:
    """List reports for a tenant, optionally filtered by engagement or status."""
    results = []
    for record in _reports.values():
        if record.tenant_id != x_tenant_id:
            continue
        if engagement_id and record.engagement_id != engagement_id:
            continue
        if status and record.status != status:
            continue
        results.append(_to_response(record))
    return results
