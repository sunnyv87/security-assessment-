"""Stage 5: Report Drafting Pipeline.

CRITICAL SAFETY CONSTRAINT: This module generates draft reports ONLY.
It sets status='draft' and published=false on every output. The AI module
has no access to the publish endpoint. Only human analysts with the
'report:publish' permission can publish reports through the report service.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

import structlog
from jinja2 import Template

from src.config.settings import settings
from src.models.domain import (
    Finding,
    EngagementContext,
    ReportDraftResult,
    ReportStatus,
    ReportType,
)
from src.prompts.templates import REPORT_DRAFT_SYSTEM, REPORT_DRAFT_USER, sanitize_finding
from src.services.llm_gateway import LLMGateway
from src.services.context_builder import ContextBuilder

logger = structlog.get_logger()


class ReportDraftPipeline:
    """Generates VAPT report drafts from validated findings.

    Safety invariants enforced by this class:
    - Output status is ALWAYS ReportStatus.DRAFT
    - Output ALWAYS includes the AI-generated disclaimer
    - Only findings with validation_verdict set are included
    - This class has NO publish capability
    """

    def __init__(self, llm: LLMGateway, ctx: ContextBuilder) -> None:
        self._llm = llm
        self._ctx = ctx
        self._user_template = Template(REPORT_DRAFT_USER)

    async def run(
        self,
        findings: list[Finding],
        engagement: EngagementContext,
        *,
        report_type: ReportType = ReportType.TECHNICAL,
        tenant_id: str,
        analyst_id: str | None = None,
    ) -> tuple[ReportDraftResult, bool]:
        """Generate a draft report from validated findings.

        NEVER auto-publishes. Output is always status=draft.

        Returns:
            Tuple of (ReportDraftResult, was_cached).
        """
        logger.info(
            "report_draft_start",
            engagement_id=engagement.id,
            report_type=report_type,
            finding_count=len(findings),
        )

        # Filter to validated findings only — SAFETY: never include unvalidated
        validated = [
            f for f in findings
            if f.validation_verdict is not None
        ]

        # Sanitize user-controlled fields before template rendering
        for f in validated:
            sanitize_finding(f)

        if not validated:
            logger.warning("report_draft_no_validated_findings", engagement_id=engagement.id)
            return self._empty_draft(engagement, report_type), False

        # Count severities
        severity_counter = Counter(f.severity.value for f in validated)
        severity_counts = {
            "critical": severity_counter.get("critical", 0),
            "high": severity_counter.get("high", 0),
            "medium": severity_counter.get("medium", 0),
            "low": severity_counter.get("low", 0),
            "info": severity_counter.get("info", 0),
        }

        # Compliance mapping placeholder
        compliance_list = ", ".join(engagement.compliance_frameworks) or "None specified"

        # Render prompt
        user_prompt = self._user_template.render(
            engagement=engagement,
            findings=validated,
            finding_count=len(validated),
            severity_counts=severity_counts,
            report_type=report_type.value,
            compliance_list=compliance_list,
            compliance_mapping_text="See individual finding compliance mappings",
            model_version=settings.claude_model,
        )

        # Call LLM with extended token budget for reports
        result, cached = await self._llm.invoke(
            system_prompt=REPORT_DRAFT_SYSTEM,
            user_prompt=user_prompt,
            max_tokens=settings.claude_max_tokens_report,
            stage="report",
            tenant_id=tenant_id,
            analyst_id=analyst_id,
            cache_ttl=settings.cache_ttl_report,
        )

        draft = ReportDraftResult(**result)

        # SAFETY: Force draft status regardless of what the LLM returns
        draft.status = ReportStatus.DRAFT
        draft.metadata.disclaimer = (
            "AI-GENERATED DRAFT — Requires analyst review before publication"
        )

        return draft, cached

    @staticmethod
    def _empty_draft(
        engagement: EngagementContext,
        report_type: ReportType,
    ) -> ReportDraftResult:
        """Return an empty draft when no validated findings exist."""
        from src.models.domain import ReportSection, ReportMetadata

        return ReportDraftResult(
            report_title=f"{engagement.customer_name} — {engagement.name} ({report_type.value})",
            report_type=report_type,
            status=ReportStatus.DRAFT,
            sections=[
                ReportSection(
                    heading="Notice",
                    content="No validated findings available for report generation. "
                    "Please validate findings before generating a report.",
                    order=1,
                ),
            ],
            metadata=ReportMetadata(
                generated_at=datetime.now(timezone.utc).isoformat(),
                model_version=settings.claude_model,
                finding_count=0,
                confidence=0.0,
                disclaimer="AI-GENERATED DRAFT — Requires analyst review before publication",
            ),
        )
