"""Report generation pipeline orchestrator — coordinates all 5 stages."""

from __future__ import annotations

import time
import uuid
from datetime import datetime

import structlog

from src.config.settings import settings
from src.models.domain import (
    GenerateReportRequest,
    ReportDataBundle,
    ReportFormat,
    ReportRecord,
    ReportStatus,
    ReportType,
)
from src.renderers.docx_renderer import DOCXRenderer
from src.renderers.html_renderer import HTMLRenderer
from src.renderers.pdf_renderer import PDFRenderer
from src.services.data_collector import DataCollector
from src.services.storage import StorageService

logger = structlog.get_logger()


class ReportGenerator:
    """Orchestrates the 5-stage report generation pipeline.

    Stage 1: Data Collection (DataCollector)
    Stage 2: Content Generation (charts, statistics — done during render)
    Stage 3: Template Rendering (HTMLRenderer)
    Stage 4: Format Export (PDFRenderer / DOCXRenderer)
    Stage 5: Storage & Delivery (StorageService)
    """

    def __init__(self) -> None:
        self._data_collector = DataCollector()
        self._html_renderer = HTMLRenderer()
        self._pdf_renderer = PDFRenderer()
        self._docx_renderer = DOCXRenderer()
        self._storage = StorageService()

    async def close(self) -> None:
        await self._data_collector.close()

    async def generate(
        self,
        request: GenerateReportRequest,
        *,
        tenant_id: str,
        generated_by: str = "",
        auth_token: str = "",
    ) -> ReportRecord:
        """Execute the full report generation pipeline.

        Returns:
            A ReportRecord with status GENERATED and file metadata.
        """
        report_id = str(uuid.uuid4())
        start_time = time.monotonic()

        logger.info(
            "pipeline_start",
            report_id=report_id,
            engagement_id=request.engagement_id,
            report_type=request.report_type,
            format=request.format,
        )

        # Build report title
        report_title = request.title or self._default_title(request.report_type)

        # ── Stage 1: Data Collection ──
        logger.info("stage_1_data_collection", report_id=report_id)
        bundle = await self._data_collector.collect(
            engagement_id=request.engagement_id,
            report_type=request.report_type,
            tenant_id=tenant_id,
            severity_filter=request.severity_filter,
            compliance_frameworks=request.compliance_frameworks or None,
            auth_token=auth_token,
        )

        # ── Stage 2 + 3: Content Generation & Template Rendering ──
        logger.info("stage_2_3_render", report_id=report_id)
        is_draft = request.include_ai_content
        html_content = self._html_renderer.render(
            bundle,
            request.report_type,
            report_title=report_title,
            is_draft=is_draft,
        )

        # ── Stage 4: Format Export ──
        logger.info("stage_4_export", report_id=report_id, format=request.format)
        if request.format == ReportFormat.PDF:
            file_bytes = self._pdf_renderer.render(html_content)
            content_type = "application/pdf"
            filename = f"{self._safe_filename(report_title)}.pdf"
        elif request.format == ReportFormat.DOCX:
            file_bytes = self._docx_renderer.render(
                bundle,
                request.report_type,
                report_title=report_title,
                generated_date=datetime.utcnow().strftime("%Y-%m-%d"),
                is_draft=is_draft,
            )
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"{self._safe_filename(report_title)}.docx"
        else:
            file_bytes = html_content.encode("utf-8")
            content_type = "text/html"
            filename = f"{self._safe_filename(report_title)}.html"

        # ── Stage 5: Storage ──
        logger.info("stage_5_storage", report_id=report_id)
        file_path, file_hash, file_size = self._storage.upload_report(
            tenant_id=tenant_id,
            report_id=report_id,
            file_data=file_bytes,
            content_type=content_type,
            filename=filename,
        )

        duration_ms = int((time.monotonic() - start_time) * 1000)

        record = ReportRecord(
            id=report_id,
            tenant_id=tenant_id,
            engagement_id=request.engagement_id,
            title=report_title,
            report_type=request.report_type,
            format=request.format,
            status=ReportStatus.GENERATED,
            generated_at=datetime.utcnow(),
            generation_duration_ms=duration_ms,
            file_path=file_path,
            file_size_bytes=file_size,
            file_hash=file_hash,
            generated_by=generated_by,
            finding_snapshot={
                "total": bundle.statistics.total_findings,
                "by_severity": bundle.statistics.by_severity,
            },
        )

        logger.info(
            "pipeline_complete",
            report_id=report_id,
            duration_ms=duration_ms,
            file_size=file_size,
        )

        return record

    def get_download_url(self, tenant_id: str, file_path: str) -> str:
        """Generate a pre-signed download URL for a report."""
        return self._storage.get_presigned_url(tenant_id, file_path)

    def delete_report_file(self, tenant_id: str, file_path: str) -> None:
        """Delete a report file from storage."""
        self._storage.delete_report(tenant_id, file_path)

    @staticmethod
    def _default_title(report_type: ReportType) -> str:
        titles = {
            ReportType.EXECUTIVE_SUMMARY: "Executive Summary Report",
            ReportType.FULL_TECHNICAL: "Technical Vulnerability Assessment Report",
            ReportType.COMPLIANCE: "Compliance Assessment Report",
            ReportType.REMEDIATION_ROADMAP: "Remediation Roadmap",
        }
        return titles.get(report_type, "Security Assessment Report")

    @staticmethod
    def _safe_filename(title: str) -> str:
        """Convert a title to a safe filename."""
        import re
        safe = re.sub(r"[^\w\s-]", "", title).strip()
        return re.sub(r"[\s]+", "_", safe)[:80]
