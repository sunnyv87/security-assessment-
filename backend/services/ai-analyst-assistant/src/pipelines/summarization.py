"""Stage 1: Vulnerability Summarization Pipeline."""

from __future__ import annotations

import structlog
from jinja2 import Template

from src.config.settings import settings
from src.models.domain import Finding, VulnSummaryResult
from src.prompts.templates import VULN_SUMMARY_SYSTEM, VULN_SUMMARY_USER
from src.services.llm_gateway import LLMGateway
from src.services.context_builder import ContextBuilder

logger = structlog.get_logger()


class SummarizationPipeline:
    """Generates structured vulnerability summaries grounded in scanner evidence."""

    def __init__(self, llm: LLMGateway, ctx: ContextBuilder) -> None:
        self._llm = llm
        self._ctx = ctx
        self._user_template = Template(VULN_SUMMARY_USER)

    async def run(
        self,
        finding: Finding,
        *,
        tenant_id: str,
        analyst_id: str | None = None,
        force_refresh: bool = False,
    ) -> tuple[VulnSummaryResult, bool]:
        """Execute vulnerability summarization.

        Returns:
            Tuple of (VulnSummaryResult, was_cached).
        """
        logger.info("summarization_start", finding_id=finding.id)

        # Build context
        asset = await self._ctx.get_asset_context(finding.asset)
        similar = await self._ctx.get_similar_findings(finding)
        similar_text = await self._ctx.format_similar_findings(similar)

        max_chars = settings.max_evidence_chars

        # Render prompt
        user_prompt = self._user_template.render(
            finding=finding,
            asset=asset,
            evidence_request=self._ctx.truncate(
                self._format_http_message(finding.evidence.request), max_chars
            ),
            evidence_response=self._ctx.truncate(
                self._format_http_message(finding.evidence.response), max_chars
            ),
            evidence_raw=self._ctx.truncate(finding.evidence.raw_output, max_chars // 2),
            similar_findings_text=similar_text,
        )

        # Call LLM
        result, cached = await self._llm.invoke(
            system_prompt=VULN_SUMMARY_SYSTEM,
            user_prompt=user_prompt,
            max_tokens=settings.claude_max_tokens_summary,
            stage="summary",
            tenant_id=tenant_id,
            analyst_id=analyst_id,
            finding_id=finding.id,
            force_refresh=force_refresh,
            cache_ttl=settings.cache_ttl_summary,
        )

        return VulnSummaryResult(**result), cached

    @staticmethod
    def _format_http_message(msg: object | None) -> str | None:
        if msg is None:
            return None
        # msg is HttpMessage
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
