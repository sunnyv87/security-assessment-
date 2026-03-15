"""Stage 1: Data Collection — assembles ReportDataBundle from microservices."""

from __future__ import annotations

from collections import Counter
from typing import Any

import httpx
import structlog

from src.config.settings import settings
from src.models.domain import (
    ReportDataBundle,
    EngagementData,
    FindingData,
    ReportStatistics,
    ComplianceData,
    RemediationPlan,
    CustomerBranding,
    Severity,
    ReportType,
)

logger = structlog.get_logger()


class DataCollector:
    """Fetches data from internal microservices to build a ReportDataBundle."""

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        await self._http.aclose()

    async def collect(
        self,
        engagement_id: str,
        report_type: ReportType,
        *,
        tenant_id: str,
        severity_filter: list[Severity] | None = None,
        compliance_frameworks: list[str] | None = None,
        auth_token: str = "",
    ) -> ReportDataBundle:
        """Collect all data needed for report generation.

        Calls Findings Service, Engagement Service, and Compliance Engine
        to assemble the complete ReportDataBundle.
        """
        headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}

        # Fetch engagement metadata
        engagement = await self._fetch_engagement(engagement_id, headers)

        # Fetch validated findings
        findings = await self._fetch_findings(engagement_id, severity_filter, headers)

        # Compute statistics
        statistics = self._compute_statistics(findings)

        # Fetch compliance data if needed
        compliance = ComplianceData()
        if report_type in (ReportType.COMPLIANCE, ReportType.FULL_TECHNICAL):
            frameworks = compliance_frameworks or engagement.get("compliance_frameworks", [])
            if frameworks:
                compliance = await self._fetch_compliance(engagement_id, frameworks, headers)

        # Build remediation plan if roadmap
        remediation_plan = RemediationPlan()
        if report_type == ReportType.REMEDIATION_ROADMAP:
            remediation_plan = self._build_remediation_plan(findings)

        # Fetch customer branding
        branding = await self._fetch_branding(tenant_id, headers)

        return ReportDataBundle(
            engagement=EngagementData(**(engagement or {"id": engagement_id, "name": "", "customer_name": "", "engagement_type": ""})),
            findings=[FindingData(**f) for f in findings],
            statistics=statistics,
            compliance=compliance,
            remediation_plan=remediation_plan,
            branding=branding,
        )

    async def _fetch_engagement(self, engagement_id: str, headers: dict) -> dict[str, Any]:
        """Fetch engagement metadata from Engagement Service."""
        try:
            resp = await self._http.get(
                f"{settings.engagement_service_url}/api/v1/engagements/{engagement_id}",
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            logger.warning("engagement_fetch_failed", engagement_id=engagement_id)
            return {"id": engagement_id, "name": "", "customer_name": "", "engagement_type": ""}

    async def _fetch_findings(
        self,
        engagement_id: str,
        severity_filter: list[Severity] | None,
        headers: dict,
    ) -> list[dict[str, Any]]:
        """Fetch validated findings from Findings Service."""
        try:
            params: dict[str, Any] = {
                "engagement_id": engagement_id,
                "validation_status": "validated",
                "page_size": 1000,
            }
            if severity_filter:
                params["severity"] = ",".join(severity_filter)

            resp = await self._http.get(
                f"{settings.findings_service_url}/api/v1/findings",
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", data) if isinstance(data, dict) else data
        except Exception:
            logger.warning("findings_fetch_failed", engagement_id=engagement_id)
            return []

    async def _fetch_compliance(
        self,
        engagement_id: str,
        frameworks: list[str],
        headers: dict,
    ) -> ComplianceData:
        """Fetch compliance mappings from Compliance Engine."""
        try:
            resp = await self._http.get(
                f"{settings.compliance_engine_url}/api/v1/compliance/{engagement_id}",
                params={"frameworks": ",".join(frameworks)},
                headers=headers,
            )
            resp.raise_for_status()
            return ComplianceData(**resp.json())
        except Exception:
            logger.warning("compliance_fetch_failed", engagement_id=engagement_id)
            return ComplianceData(frameworks=frameworks)

    async def _fetch_branding(self, tenant_id: str, headers: dict) -> CustomerBranding:
        """Fetch customer branding configuration."""
        try:
            resp = await self._http.get(
                f"{settings.engagement_service_url}/api/v1/tenants/{tenant_id}/branding",
                headers=headers,
            )
            resp.raise_for_status()
            return CustomerBranding(**resp.json())
        except Exception:
            return CustomerBranding()

    @staticmethod
    def _compute_statistics(findings: list[dict[str, Any]]) -> ReportStatistics:
        """Compute finding statistics from raw finding data."""
        total = len(findings)
        if total == 0:
            return ReportStatistics()

        severity_counter = Counter(f.get("severity", "info") for f in findings)
        category_counter = Counter(f.get("category", f.get("cwe_name", "Unknown")) for f in findings)
        asset_counter = Counter(f.get("asset", "Unknown") for f in findings)
        fp_count = sum(1 for f in findings if f.get("validation_verdict") == "false_positive")
        validated = sum(1 for f in findings if f.get("validation_verdict"))
        with_remed = sum(1 for f in findings if f.get("remediation", {}).get("summary"))

        return ReportStatistics(
            total_findings=total,
            by_severity=dict(severity_counter),
            by_category=dict(category_counter),
            by_asset=dict(asset_counter),
            false_positive_count=fp_count,
            false_positive_rate=fp_count / total if total else 0,
            validated_count=validated,
            validation_coverage=validated / total if total else 0,
            remediation_coverage=with_remed / total if total else 0,
        )

    @staticmethod
    def _build_remediation_plan(findings: list[dict[str, Any]]) -> RemediationPlan:
        """Build a phased remediation plan from findings."""
        from src.models.domain import RemediationPhase

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        sorted_findings = sorted(findings, key=lambda f: severity_order.get(f.get("severity", "info"), 4))

        phases = [
            RemediationPhase(
                name="Phase 1 — Immediate (0-7 days)",
                timeline="0-7 days",
                finding_ids=[f["id"] for f in sorted_findings if f.get("severity") == "critical"],
                effort_estimate="Varies by finding complexity",
            ),
            RemediationPhase(
                name="Phase 2 — Short-Term (1-4 weeks)",
                timeline="1-4 weeks",
                finding_ids=[f["id"] for f in sorted_findings if f.get("severity") == "high"],
                effort_estimate="1-2 weeks engineering effort",
            ),
            RemediationPhase(
                name="Phase 3 — Medium-Term (1-3 months)",
                timeline="1-3 months",
                finding_ids=[f["id"] for f in sorted_findings if f.get("severity") == "medium"],
                effort_estimate="2-4 weeks engineering effort",
            ),
            RemediationPhase(
                name="Phase 4 — Long-Term (3-6 months)",
                timeline="3-6 months",
                finding_ids=[f["id"] for f in sorted_findings if f.get("severity") in ("low", "info")],
                effort_estimate="Ongoing improvement",
            ),
        ]

        return RemediationPlan(
            phases=[p for p in phases if p.finding_ids],
            total_effort_estimate="Estimated 4-12 weeks total",
            retest_recommendation="Retest recommended 30 days after Phase 1 and Phase 2 completion.",
        )
