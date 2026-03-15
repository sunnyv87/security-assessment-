"""Stage 3: Risk Prioritization Pipeline."""

from __future__ import annotations

import structlog
from jinja2 import Template

from src.config.settings import settings
from src.models.domain import (
    Finding,
    EngagementContext,
    ThreatIntelContext,
    RiskPriorityResult,
)
from src.prompts.templates import RISK_PRIORITY_SYSTEM, RISK_PRIORITY_USER, sanitize_finding
from src.services.llm_gateway import LLMGateway
from src.services.context_builder import ContextBuilder

logger = structlog.get_logger()


class RiskPriorityPipeline:
    """Prioritizes findings by real-world exploitability and business impact.

    Combines CVSS base scores with environmental context, threat intelligence,
    and compliance requirements to produce actionable investigation order.
    """

    def __init__(self, llm: LLMGateway, ctx: ContextBuilder) -> None:
        self._llm = llm
        self._ctx = ctx
        self._user_template = Template(RISK_PRIORITY_USER)

    async def run(
        self,
        findings: list[Finding],
        engagement: EngagementContext,
        *,
        threat_intel: ThreatIntelContext | None = None,
        tenant_id: str,
        analyst_id: str | None = None,
        force_refresh: bool = False,
    ) -> tuple[RiskPriorityResult, bool]:
        """Execute risk prioritization across a batch of findings.

        Returns:
            Tuple of (RiskPriorityResult, was_cached).
        """
        logger.info(
            "risk_priority_start",
            engagement_id=engagement.id,
            finding_count=len(findings),
        )

        # Sanitize user-controlled fields before template rendering
        for f in findings:
            sanitize_finding(f)

        if threat_intel is None:
            threat_intel = ThreatIntelContext()

        # Format threat intel
        epss_lines = [
            f"  {fid}: {score:.1%}" for fid, score in threat_intel.epss_scores.items()
        ]
        epss_text = "\n".join(epss_lines) if epss_lines else "No EPSS data available"

        # Render prompt
        user_prompt = self._user_template.render(
            engagement=engagement,
            findings=findings,
            finding_count=len(findings),
            compliance_list=", ".join(engagement.compliance_frameworks) or "None specified",
            active_exploits=", ".join(threat_intel.active_exploits) or "None known",
            kev_matches=", ".join(threat_intel.kev_matches) or "None",
            epss_text=epss_text,
        )

        # Call LLM
        result, cached = await self._llm.invoke(
            system_prompt=RISK_PRIORITY_SYSTEM,
            user_prompt=user_prompt,
            max_tokens=settings.claude_max_tokens_priority,
            stage="priority",
            tenant_id=tenant_id,
            analyst_id=analyst_id,
            force_refresh=force_refresh,
            cache_ttl=settings.cache_ttl_priority,
        )

        return RiskPriorityResult(**result), cached
