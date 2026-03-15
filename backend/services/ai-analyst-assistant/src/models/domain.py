"""Domain models for AI Analyst Assistant pipeline."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ──


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ValidationVerdict(StrEnum):
    TRUE_POSITIVE = "true_positive"
    LIKELY_TRUE_POSITIVE = "likely_true_positive"
    UNCERTAIN = "uncertain"
    LIKELY_FALSE_POSITIVE = "likely_false_positive"
    FALSE_POSITIVE = "false_positive"


class EvidenceQuality(StrEnum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    INSUFFICIENT = "insufficient"


class ReportType(StrEnum):
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    COMPLIANCE = "compliance"


class ReportStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"


# ── Input Models ──


class HttpMessage(BaseModel):
    method: str | None = None
    url: str | None = None
    status_code: int | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    body: str = ""


class FindingEvidence(BaseModel):
    request: HttpMessage | None = None
    response: HttpMessage | None = None
    raw_output: str | None = None
    screenshots: list[str] = Field(default_factory=list)


class AssetContext(BaseModel):
    environment: str = "production"
    internet_facing: bool = True
    data_classification: str = "confidential"
    tech_stack: str = ""
    language: str = ""
    framework: str = ""
    framework_version: str = ""
    runtime: str = ""
    database: str = ""
    deployment_type: str = ""
    server_tech: str = ""
    security_layers: str = ""
    security_controls: list[str] = Field(default_factory=list)
    asset_criticality: str = "high"


class ScannerRuleContext(BaseModel):
    id: str = ""
    description: str = ""
    fp_rate: float = 0.0
    historical_fp_rate: float = 0.0


class Finding(BaseModel):
    id: str
    engagement_id: str
    title: str
    description: str
    severity: Severity
    cwe_id: str = ""
    cwe_name: str = ""
    scanner: str
    scanner_confidence: float = 0.0
    cvss_score: float = 0.0
    cvss_vector: str = ""
    asset: str
    endpoint: str = ""
    http_method: str = ""
    evidence: FindingEvidence = Field(default_factory=FindingEvidence)
    source_code_context: str | None = None
    validation_verdict: str | None = None
    evidence_summary: str | None = None
    remediation_guidance: str | None = None
    internet_facing: bool = True
    auth_required: bool = False
    ai_false_positive_prob: float | None = None


class EngagementContext(BaseModel):
    id: str
    customer_name: str
    name: str
    type: str
    industry: str = ""
    scope_description: str = ""
    start_date: str = ""
    end_date: str = ""
    lead_analyst: str = ""
    compliance_frameworks: list[str] = Field(default_factory=list)


class ThreatIntelContext(BaseModel):
    active_exploits: list[str] = Field(default_factory=list)
    kev_matches: list[str] = Field(default_factory=list)
    epss_scores: dict[str, float] = Field(default_factory=dict)


# ── Output Models ──


class VulnSummaryResult(BaseModel):
    """Output from the vulnerability summarization stage."""

    executive_summary: str
    technical_summary: str
    attack_scenario: str
    affected_component: str
    data_at_risk: str
    prerequisites: str
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_reasoning: str


class FPIndicator(BaseModel):
    indicator: str
    supports: str  # "tp" or "fp"


class FalsePositiveResult(BaseModel):
    """Output from the false positive detection stage."""

    verdict: ValidationVerdict
    probability_fp: float = Field(ge=0.0, le=1.0)
    reasoning: list[str]
    evidence_quality: EvidenceQuality
    key_indicators: list[FPIndicator]
    recommended_action: str
    manual_verification_steps: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    requires_analyst_review: bool = False


class RiskFactors(BaseModel):
    exploitability: str
    business_impact: str
    exposure: str
    data_sensitivity: str
    active_threat: bool = False


class PrioritizedFinding(BaseModel):
    finding_id: str
    priority_rank: int
    risk_score: float = Field(ge=0.0, le=10.0)
    risk_factors: RiskFactors
    justification: str
    attack_chains: list[str] = Field(default_factory=list)
    compliance_impact: list[str] = Field(default_factory=list)


class RiskPriorityResult(BaseModel):
    """Output from the risk prioritization stage."""

    prioritized_findings: list[PrioritizedFinding]
    executive_risk_summary: str
    recommended_investigation_order: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    requires_analyst_review: bool = False


class RemediationStep(BaseModel):
    step: int
    action: str
    description: str
    effort: str = "hours"


class CodeExample(BaseModel):
    language: str
    label: str
    before: str
    after: str
    explanation: str = ""


class Reference(BaseModel):
    title: str
    url: str
    source: str


class RemediationResult(BaseModel):
    """Output from the remediation suggestion stage."""

    summary: str
    priority: str = "short_term"
    detailed_steps: list[RemediationStep]
    code_examples: list[CodeExample] = Field(default_factory=list)
    defense_in_depth: list[str] = Field(default_factory=list)
    testing_verification: list[str] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    estimated_effort: str = "days"
    confidence: float = Field(ge=0.0, le=1.0)


class ReportSection(BaseModel):
    heading: str
    content: str
    order: int


class ReportMetadata(BaseModel):
    generated_at: str
    model_version: str
    finding_count: int
    confidence: float = Field(ge=0.0, le=1.0)
    disclaimer: str = "AI-GENERATED DRAFT — Requires analyst review before publication"


class ReportDraftResult(BaseModel):
    """Output from the report drafting stage."""

    report_title: str
    report_type: ReportType
    status: ReportStatus = ReportStatus.DRAFT
    sections: list[ReportSection]
    metadata: ReportMetadata


# ── API Request/Response Models ──


class AnalyzeRequest(BaseModel):
    """Request to run one or more AI pipeline stages on a finding."""

    finding_id: str
    stages: list[str] = Field(
        default=["summary", "fp_detection", "remediation"],
        description="Pipeline stages to run: summary, fp_detection, priority, remediation, report",
    )
    force_refresh: bool = False


class PriorityRequest(BaseModel):
    """Request to prioritize a batch of findings."""

    engagement_id: str
    finding_ids: list[str] = Field(default_factory=list)
    include_threat_intel: bool = True
    force_refresh: bool = False


class ReportDraftRequest(BaseModel):
    """Request to generate a report draft."""

    engagement_id: str
    report_type: ReportType = ReportType.TECHNICAL
    include_only_validated: bool = True


class AiAnalysisResponse(BaseModel):
    """Unified response from AI analysis pipeline."""

    finding_id: str
    stages_completed: list[str]
    summary: VulnSummaryResult | None = None
    false_positive: FalsePositiveResult | None = None
    remediation: RemediationResult | None = None
    cached: bool = False
    processing_time_ms: int = 0
    model_version: str = ""
    token_usage: dict[str, int] = Field(default_factory=dict)


class AuditLogEntry(BaseModel):
    """Immutable audit record for every AI invocation."""

    id: str
    tenant_id: str
    analyst_id: str | None
    finding_id: str | None
    stage: str
    input_hash: str
    model_version: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    confidence: float
    cached: bool
    created_at: datetime = Field(default_factory=datetime.utcnow)
