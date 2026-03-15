"""Pipeline Orchestrator — coordinates multi-stage AI analysis."""

from __future__ import annotations

import time
from typing import Any

import structlog

from src.config.settings import settings
from src.models.domain import (
    Finding,
    EngagementContext,
    ThreatIntelContext,
    AiAnalysisResponse,
    ReportType,
    ReportDraftResult,
    RiskPriorityResult,
)
from src.pipelines.summarization import SummarizationPipeline
from src.pipelines.fp_detection import FPDetectionPipeline
from src.pipelines.risk_priority import RiskPriorityPipeline
from src.pipelines.remediation import RemediationPipeline
from src.pipelines.report_draft import ReportDraftPipeline
from src.services.llm_gateway import LLMGateway
from src.services.context_builder import ContextBuilder
from src.services.cache import CacheService

logger = structlog.get_logger()


class PipelineOrchestrator:
    """Coordinates execution of AI pipeline stages.

    Supports running individual stages or the full enrichment pipeline.
    All stages produce recommendations — never authoritative decisions.
    """

    def __init__(self, db_pool: Any = None) -> None:
        self._cache = CacheService()
        self._llm = LLMGateway(self._cache)
        self._ctx = ContextBuilder(db_pool)

        # Initialize pipelines
        self._summarization = SummarizationPipeline(self._llm, self._ctx)
        self._fp_detection = FPDetectionPipeline(self._llm, self._ctx)
        self._risk_priority = RiskPriorityPipeline(self._llm, self._ctx)
        self._remediation = RemediationPipeline(self._llm, self._ctx)
        self._report_draft = ReportDraftPipeline(self._llm, self._ctx)

    async def startup(self) -> None:
        """Initialize connections."""
        await self._cache.connect()

    async def shutdown(self) -> None:
        """Cleanup connections."""
        await self._cache.disconnect()

    async def analyze_finding(
        self,
        finding: Finding,
        *,
        stages: list[str],
        tenant_id: str,
        analyst_id: str | None = None,
        force_refresh: bool = False,
    ) -> AiAnalysisResponse:
        """Run one or more pipeline stages on a single finding.

        Args:
            finding: The finding to analyze.
            stages: List of stage names to run (summary, fp_detection, remediation).
            tenant_id: Tenant ID for multi-tenancy isolation.
            analyst_id: Optional analyst ID for audit trail.
            force_refresh: If True, bypass cache.

        Returns:
            AiAnalysisResponse with results from completed stages.
        """
        start = time.monotonic()
        completed: list[str] = []
        any_cached = False
        total_tokens: dict[str, int] = {"input": 0, "output": 0}

        response = AiAnalysisResponse(
            finding_id=finding.id,
            stages_completed=[],
            model_version=settings.claude_model,
        )

        # Stage 1: Vulnerability Summarization
        if "summary" in stages:
            try:
                summary, cached = await self._summarization.run(
                    finding,
                    tenant_id=tenant_id,
                    analyst_id=analyst_id,
                    force_refresh=force_refresh,
                )
                response.summary = summary
                completed.append("summary")
                any_cached = any_cached or cached
            except Exception:
                logger.exception("summarization_failed", finding_id=finding.id)

        # Stage 2: False Positive Detection
        if "fp_detection" in stages:
            try:
                fp_result, cached = await self._fp_detection.run(
                    finding,
                    tenant_id=tenant_id,
                    analyst_id=analyst_id,
                    force_refresh=force_refresh,
                )
                response.false_positive = fp_result
                completed.append("fp_detection")
                any_cached = any_cached or cached
            except Exception:
                logger.exception("fp_detection_failed", finding_id=finding.id)

        # Stage 4: Remediation Suggestions
        if "remediation" in stages:
            try:
                remed_result, cached = await self._remediation.run(
                    finding,
                    tenant_id=tenant_id,
                    analyst_id=analyst_id,
                    force_refresh=force_refresh,
                )
                response.remediation = remed_result
                completed.append("remediation")
                any_cached = any_cached or cached
            except Exception:
                logger.exception("remediation_failed", finding_id=finding.id)

        response.stages_completed = completed
        response.cached = any_cached
        response.processing_time_ms = int((time.monotonic() - start) * 1000)
        response.token_usage = total_tokens

        logger.info(
            "analysis_complete",
            finding_id=finding.id,
            stages=completed,
            duration_ms=response.processing_time_ms,
        )

        return response

    async def prioritize_findings(
        self,
        findings: list[Finding],
        engagement: EngagementContext,
        *,
        threat_intel: ThreatIntelContext | None = None,
        tenant_id: str,
        analyst_id: str | None = None,
        force_refresh: bool = False,
    ) -> RiskPriorityResult:
        """Run risk prioritization across a batch of findings.

        Args:
            findings: List of findings to prioritize.
            engagement: Engagement context.
            threat_intel: Optional threat intelligence data.
            tenant_id: Tenant ID for multi-tenancy isolation.
            analyst_id: Optional analyst ID for audit trail.
            force_refresh: If True, bypass cache.

        Returns:
            RiskPriorityResult with prioritized finding list.
        """
        result, _ = await self._risk_priority.run(
            findings,
            engagement,
            threat_intel=threat_intel,
            tenant_id=tenant_id,
            analyst_id=analyst_id,
            force_refresh=force_refresh,
        )
        return result

    async def draft_report(
        self,
        findings: list[Finding],
        engagement: EngagementContext,
        *,
        report_type: ReportType = ReportType.TECHNICAL,
        tenant_id: str,
        analyst_id: str | None = None,
    ) -> ReportDraftResult:
        """Generate a DRAFT report. NEVER auto-publishes.

        The output always has:
        - status = "draft"
        - published = false
        - disclaimer = "AI-GENERATED DRAFT..."

        Only an analyst with 'report:publish' permission can publish
        the report through the Report Service API (a separate service).

        Args:
            findings: List of validated findings to include.
            engagement: Engagement context.
            report_type: Executive, technical, or compliance.
            tenant_id: Tenant ID for multi-tenancy isolation.
            analyst_id: Optional analyst ID for audit trail.

        Returns:
            ReportDraftResult with draft status enforced.
        """
        result, _ = await self._report_draft.run(
            findings,
            engagement,
            report_type=report_type,
            tenant_id=tenant_id,
            analyst_id=analyst_id,
        )

        # SAFETY: Double-enforce draft status at orchestrator level
        from src.models.domain import ReportStatus
        assert result.status == ReportStatus.DRAFT, "Report must be draft status"

        return result
