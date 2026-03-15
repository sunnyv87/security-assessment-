"""API routes for the AI Analyst Assistant service.

All endpoints require authentication. The AI module assists analysts
but NEVER publishes reports or changes finding statuses autonomously.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.models.domain import (
    AnalyzeRequest,
    PriorityRequest,
    ReportDraftRequest,
    AiAnalysisResponse,
    RiskPriorityResult,
    ReportDraftResult,
    Finding,
    EngagementContext,
    ThreatIntelContext,
    ReportType,
)
from src.pipelines.orchestrator import PipelineOrchestrator
from src.api.dependencies import get_orchestrator, get_current_user, AuthUser

router = APIRouter(prefix="/v1", tags=["ai-analyst"])


# ── Finding Analysis (single finding, multiple stages) ──


@router.post("/analyze", response_model=AiAnalysisResponse)
async def analyze_finding(
    request: AnalyzeRequest,
    user: AuthUser = Depends(get_current_user),
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator),
) -> AiAnalysisResponse:
    """Run AI analysis pipeline stages on a single finding.

    Available stages: summary, fp_detection, remediation.
    Results are recommendations — analyst must review before action.
    """
    valid_stages = {"summary", "fp_detection", "remediation"}
    invalid = set(request.stages) - valid_stages
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stages: {invalid}. Valid: {valid_stages}",
        )

    # In production, load finding from DB using request.finding_id
    # For now, we accept the finding_id and return a structured response
    finding = await _load_finding(request.finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")

    return await orchestrator.analyze_finding(
        finding,
        stages=request.stages,
        tenant_id=user.tenant_id,
        analyst_id=user.id,
        force_refresh=request.force_refresh,
    )


# ── Risk Prioritization (batch of findings) ──


@router.post("/prioritize", response_model=RiskPriorityResult)
async def prioritize_findings(
    request: PriorityRequest,
    user: AuthUser = Depends(get_current_user),
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator),
) -> RiskPriorityResult:
    """Prioritize findings by risk for analyst investigation order.

    Returns ranked findings with risk scores, attack chains,
    and compliance impact analysis.
    """
    findings = await _load_findings_for_engagement(
        request.engagement_id, request.finding_ids
    )
    if not findings:
        raise HTTPException(status_code=404, detail="No findings found")

    engagement = await _load_engagement(request.engagement_id)
    if engagement is None:
        raise HTTPException(status_code=404, detail="Engagement not found")

    threat_intel = None
    if request.include_threat_intel:
        threat_intel = await _load_threat_intel(findings)

    return await orchestrator.prioritize_findings(
        findings,
        engagement,
        threat_intel=threat_intel,
        tenant_id=user.tenant_id,
        analyst_id=user.id,
        force_refresh=request.force_refresh,
    )


# ── Report Drafting ──


@router.post("/reports/draft", response_model=ReportDraftResult)
async def draft_report(
    request: ReportDraftRequest,
    user: AuthUser = Depends(get_current_user),
    orchestrator: PipelineOrchestrator = Depends(get_orchestrator),
) -> ReportDraftResult:
    """Generate a DRAFT report from validated findings.

    IMPORTANT: This endpoint generates drafts ONLY. The AI module
    cannot publish reports. Only authorized analysts can publish
    through the Report Service API.

    The response always has:
    - status: "draft"
    - metadata.disclaimer: "AI-GENERATED DRAFT..."
    """
    engagement = await _load_engagement(request.engagement_id)
    if engagement is None:
        raise HTTPException(status_code=404, detail="Engagement not found")

    findings = await _load_validated_findings(request.engagement_id)

    return await orchestrator.draft_report(
        findings,
        engagement,
        report_type=request.report_type,
        tenant_id=user.tenant_id,
        analyst_id=user.id,
    )


# ── Health ──


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "ai-analyst-assistant"}


# ── Data Loading Stubs ──
# In production, these query PostgreSQL. Shown as stubs to illustrate
# the interface between the API layer and the data layer.


async def _load_finding(finding_id: str) -> Finding | None:
    """Load a finding from the database by ID."""
    # Production: SELECT * FROM findings WHERE id = $1 AND tenant_id = $2
    return None  # Stub — returns None, triggering 404


async def _load_findings_for_engagement(
    engagement_id: str, finding_ids: list[str] | None = None
) -> list[Finding]:
    """Load findings for an engagement, optionally filtered by IDs."""
    # Production: SELECT * FROM findings WHERE engagement_id = $1
    return []


async def _load_validated_findings(engagement_id: str) -> list[Finding]:
    """Load only analyst-validated findings for report generation."""
    # Production: SELECT * FROM findings
    #   WHERE engagement_id = $1 AND validation_verdict IS NOT NULL
    return []


async def _load_engagement(engagement_id: str) -> EngagementContext | None:
    """Load engagement context from the database."""
    return None


async def _load_threat_intel(findings: list[Finding]) -> ThreatIntelContext:
    """Load threat intelligence data for the given findings."""
    # Production: Query CISA KEV, EPSS API, internal threat feeds
    return ThreatIntelContext()
