"""Domain models for report generation."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ──


class ReportType(StrEnum):
    EXECUTIVE_SUMMARY = "executive_summary"
    FULL_TECHNICAL = "full_technical"
    COMPLIANCE = "compliance"
    REMEDIATION_ROADMAP = "remediation_roadmap"


class ReportFormat(StrEnum):
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"


class ReportStatus(StrEnum):
    QUEUED = "queued"
    GENERATING = "generating"
    GENERATED = "generated"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DELIVERED = "delivered"
    FAILED = "failed"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# ── Report Data Bundle (Stage 1 output) ──


class CustomerBranding(BaseModel):
    logo_url: str = ""
    company_name: str = ""
    primary_color: str = "#1e40af"
    secondary_color: str = "#3b82f6"
    custom_css: str | None = None


class PageSetup(BaseModel):
    size: str = "A4"
    orientation: str = "portrait"
    margin_top: str = "25mm"
    margin_right: str = "20mm"
    margin_bottom: str = "25mm"
    margin_left: str = "20mm"


class EngagementData(BaseModel):
    id: str
    name: str
    customer_name: str
    customer_industry: str = ""
    engagement_type: str
    scope_description: str = ""
    in_scope_assets: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    start_date: str = ""
    end_date: str = ""
    duration_days: int = 0
    lead_analyst: str = ""
    analysts: list[str] = Field(default_factory=list)
    methodology: str = "OWASP WSTG v4.2"
    tools_used: list[str] = Field(default_factory=list)


class HttpEvidence(BaseModel):
    method: str = ""
    url: str = ""
    status_code: int | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    body: str = ""


class FindingEvidence(BaseModel):
    request: HttpEvidence | None = None
    response: HttpEvidence | None = None
    screenshots: list[str] = Field(default_factory=list)
    raw_output: str | None = None


class RemediationData(BaseModel):
    summary: str = ""
    steps: list[str] = Field(default_factory=list)
    code_examples: list[CodeExampleData] = Field(default_factory=list)
    references: list[ReferenceData] = Field(default_factory=list)
    estimated_effort: str = ""


class CodeExampleData(BaseModel):
    language: str = ""
    label: str = ""
    before: str = ""
    after: str = ""


class ReferenceData(BaseModel):
    title: str
    url: str
    source: str = ""


class FindingData(BaseModel):
    id: str
    title: str
    description: str
    severity: Severity
    cvss_score: float = 0.0
    cvss_vector: str = ""
    cwe_id: str = ""
    cwe_name: str = ""
    category: str = ""
    asset: str = ""
    endpoint: str = ""
    http_method: str = ""
    evidence: FindingEvidence = Field(default_factory=FindingEvidence)
    validation_verdict: str = ""
    validated_by: str = ""
    validated_at: str = ""
    remediation: RemediationData = Field(default_factory=RemediationData)
    compliance_controls: list[str] = Field(default_factory=list)
    reproduction_steps: list[str] = Field(default_factory=list)
    business_impact: str = ""


class ReportStatistics(BaseModel):
    total_findings: int = 0
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    by_asset: dict[str, int] = Field(default_factory=dict)
    false_positive_count: int = 0
    false_positive_rate: float = 0.0
    validated_count: int = 0
    validation_coverage: float = 0.0
    remediation_coverage: float = 0.0


class ControlMapping(BaseModel):
    control_id: str
    control_name: str
    framework: str
    status: str  # pass, fail, partial, na
    finding_ids: list[str] = Field(default_factory=list)
    evidence: str = ""
    remediation_required: str = ""


class ComplianceData(BaseModel):
    frameworks: list[str] = Field(default_factory=list)
    scores_by_framework: dict[str, float] = Field(default_factory=dict)
    control_mappings: list[ControlMapping] = Field(default_factory=list)
    gaps: list[ControlMapping] = Field(default_factory=list)


class RemediationPhase(BaseModel):
    name: str
    timeline: str
    finding_ids: list[str] = Field(default_factory=list)
    effort_estimate: str = ""


class RemediationPlan(BaseModel):
    phases: list[RemediationPhase] = Field(default_factory=list)
    total_effort_estimate: str = ""
    retest_recommendation: str = ""


class ReportDataBundle(BaseModel):
    """Complete data package for report generation (Stage 1 output)."""

    engagement: EngagementData
    findings: list[FindingData] = Field(default_factory=list)
    statistics: ReportStatistics = Field(default_factory=ReportStatistics)
    compliance: ComplianceData = Field(default_factory=ComplianceData)
    remediation_plan: RemediationPlan = Field(default_factory=RemediationPlan)
    branding: CustomerBranding = Field(default_factory=CustomerBranding)
    page_setup: PageSetup = Field(default_factory=PageSetup)


# ── Report Record (database) ──


class ReportRecord(BaseModel):
    """Report metadata stored in PostgreSQL."""

    id: str
    tenant_id: str
    engagement_id: str
    title: str
    report_type: ReportType
    format: ReportFormat
    status: ReportStatus = ReportStatus.QUEUED
    template_id: str | None = None
    generated_at: datetime | None = None
    generation_duration_ms: int | None = None
    file_path: str | None = None
    file_size_bytes: int | None = None
    page_count: int | None = None
    file_hash: str | None = None
    generated_by: str = ""
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    delivered_at: datetime | None = None
    delivery_method: str | None = None
    version: int = 1
    parent_report_id: str | None = None
    finding_snapshot: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ── API Models ──


class GenerateReportRequest(BaseModel):
    engagement_id: str
    report_type: ReportType = ReportType.FULL_TECHNICAL
    format: ReportFormat = ReportFormat.PDF
    title: str | None = None
    compliance_frameworks: list[str] = Field(default_factory=list)
    severity_filter: list[Severity] | None = None
    include_ai_content: bool = True


class ReportResponse(BaseModel):
    id: str
    engagement_id: str
    title: str
    report_type: ReportType
    format: ReportFormat
    status: ReportStatus
    generated_at: datetime | None = None
    file_size_bytes: int | None = None
    page_count: int | None = None
    version: int = 1
    download_url: str | None = None


class ApproveReportRequest(BaseModel):
    approval_notes: str = ""


class DeliverReportRequest(BaseModel):
    delivery_method: str = "portal_download"
    recipient_emails: list[str] = Field(default_factory=list)
    notify_customer: bool = True
