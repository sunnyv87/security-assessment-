"""Stage 4: Remediation Suggestion Pipeline."""

from __future__ import annotations

import structlog
from jinja2 import Template

from src.config.settings import settings
from src.models.domain import Finding, RemediationResult
from src.prompts.templates import REMEDIATION_SYSTEM, REMEDIATION_USER
from src.services.llm_gateway import LLMGateway
from src.services.context_builder import ContextBuilder

logger = structlog.get_logger()


class RemediationPipeline:
    """Generates actionable, technology-specific remediation guidance.

    Produces code-level fixes for SAST findings, configuration fixes for
    infrastructure findings, and general guidance for DAST findings.
    All suggestions are defensive — never offensive.
    """

    def __init__(self, llm: LLMGateway, ctx: ContextBuilder) -> None:
        self._llm = llm
        self._ctx = ctx
        self._user_template = Template(REMEDIATION_USER)

    async def run(
        self,
        finding: Finding,
        *,
        tenant_id: str,
        analyst_id: str | None = None,
        force_refresh: bool = False,
    ) -> tuple[RemediationResult, bool]:
        """Execute remediation suggestion generation.

        Returns:
            Tuple of (RemediationResult, was_cached).
        """
        logger.info("remediation_start", finding_id=finding.id)

        # Build context
        asset = await self._ctx.get_asset_context(finding.asset)
        max_chars = settings.max_evidence_chars

        # Format security controls
        controls_text = "\n".join(
            f"- {c}" for c in asset.security_controls
        ) if asset.security_controls else "No security controls documented"

        # Render prompt
        user_prompt = self._user_template.render(
            finding=finding,
            asset=asset,
            evidence_request=self._ctx.truncate(
                self._format_evidence(finding.evidence.request), max_chars
            ),
            evidence_response=self._ctx.truncate(
                self._format_evidence(finding.evidence.response), max_chars
            ),
            source_code_context=self._ctx.truncate(
                finding.source_code_context, max_chars
            ) if finding.source_code_context else "Not available — DAST finding",
            security_controls_text=controls_text,
        )

        # Call LLM
        result, cached = await self._llm.invoke(
            system_prompt=REMEDIATION_SYSTEM,
            user_prompt=user_prompt,
            max_tokens=settings.claude_max_tokens_remediation,
            stage="remediation",
            tenant_id=tenant_id,
            analyst_id=analyst_id,
            finding_id=finding.id,
            force_refresh=force_refresh,
            cache_ttl=settings.cache_ttl_remediation,
        )

        return RemediationResult(**result), cached

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
