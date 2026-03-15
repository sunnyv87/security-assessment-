"""Stage 2: False Positive Detection Pipeline."""

from __future__ import annotations

import structlog
from jinja2 import Template

from src.config.settings import settings
from src.models.domain import Finding, FalsePositiveResult
from src.prompts.templates import FP_DETECTION_SYSTEM, FP_DETECTION_USER, sanitize_finding
from src.services.llm_gateway import LLMGateway
from src.services.context_builder import ContextBuilder

logger = structlog.get_logger()


class FPDetectionPipeline:
    """Assesses whether a scanner finding is a true positive or false positive.

    Conservative by design: when uncertain, leans toward true positive
    to avoid missing real vulnerabilities.
    """

    def __init__(self, llm: LLMGateway, ctx: ContextBuilder) -> None:
        self._llm = llm
        self._ctx = ctx
        self._user_template = Template(FP_DETECTION_USER)

    async def run(
        self,
        finding: Finding,
        *,
        tenant_id: str,
        analyst_id: str | None = None,
        force_refresh: bool = False,
    ) -> tuple[FalsePositiveResult, bool]:
        """Execute false positive detection.

        Returns:
            Tuple of (FalsePositiveResult, was_cached).
        """
        logger.info("fp_detection_start", finding_id=finding.id)

        # Sanitize user-controlled fields before template rendering
        sanitize_finding(finding)

        # Build context
        asset = await self._ctx.get_asset_context(finding.asset)
        scanner_rule = await self._ctx.get_scanner_rule_context(
            finding.scanner, finding.cwe_id
        )
        similar = await self._ctx.get_similar_findings(finding)
        verified_text, total, tp_count, fp_count, dup_count = (
            await self._ctx.format_verified_findings(similar)
        )

        max_chars = settings.max_evidence_chars

        # Render prompt
        user_prompt = self._user_template.render(
            finding=finding,
            asset=asset,
            scanner_rule=scanner_rule,
            evidence_request=self._ctx.truncate(
                self._format_evidence(finding.evidence.request), max_chars
            ),
            evidence_response=self._ctx.truncate(
                self._format_evidence(finding.evidence.response), max_chars
            ),
            verified_findings_text=verified_text,
            similar_count=total,
            tp_count=tp_count,
            fp_count=fp_count,
            dup_count=dup_count,
        )

        # Call LLM
        result, cached = await self._llm.invoke(
            system_prompt=FP_DETECTION_SYSTEM,
            user_prompt=user_prompt,
            max_tokens=settings.claude_max_tokens_fp,
            stage="fp_detection",
            tenant_id=tenant_id,
            analyst_id=analyst_id,
            finding_id=finding.id,
            force_refresh=force_refresh,
            cache_ttl=settings.cache_ttl_fp_detection,
        )

        return FalsePositiveResult(**result), cached

    @staticmethod
    def _format_evidence(msg: object | None) -> str | None:
        if msg is None:
            return None
        parts = []
        if hasattr(msg, "method") and msg.method:
            parts.append(f"{msg.method} {msg.url} HTTP/1.1")
        elif hasattr(msg, "status_code") and msg.status_code:
            parts.append(f"HTTP/1.1 {msg.status_code}")
        if hasattr(msg, "headers"):
            for k, v in msg.headers.items():
                parts.append(f"{k}: {v}")
        if hasattr(msg, "body") and msg.body:
            parts.append("")
            parts.append(msg.body)
        return "\n".join(parts) if parts else None
