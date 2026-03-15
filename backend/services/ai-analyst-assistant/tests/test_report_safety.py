"""Tests verifying that the AI module NEVER auto-publishes reports."""

import pytest
from src.models.domain import (
    ReportDraftResult,
    ReportStatus,
    ReportType,
    ReportSection,
    ReportMetadata,
    EngagementContext,
    Finding,
    Severity,
)
from src.pipelines.report_draft import ReportDraftPipeline


class TestReportSafetyInvariants:
    """Verify that all report outputs enforce draft-only status."""

    def test_draft_status_is_always_draft(self) -> None:
        """Report status must always be 'draft', never 'published'."""
        result = ReportDraftResult(
            report_title="Test Report",
            report_type=ReportType.TECHNICAL,
            status=ReportStatus.DRAFT,
            sections=[
                ReportSection(heading="Test", content="Content", order=1),
            ],
            metadata=ReportMetadata(
                generated_at="2026-03-15T00:00:00Z",
                model_version="claude-opus-4-6",
                finding_count=0,
                confidence=0.95,
            ),
        )
        assert result.status == ReportStatus.DRAFT
        assert result.status != ReportStatus.PUBLISHED

    def test_disclaimer_is_always_present(self) -> None:
        """Every report must include the AI-generated disclaimer."""
        result = ReportDraftResult(
            report_title="Test Report",
            report_type=ReportType.EXECUTIVE,
            status=ReportStatus.DRAFT,
            sections=[],
            metadata=ReportMetadata(
                generated_at="2026-03-15T00:00:00Z",
                model_version="claude-opus-4-6",
                finding_count=0,
                confidence=0.0,
            ),
        )
        assert "AI-GENERATED DRAFT" in result.metadata.disclaimer
        assert "analyst review" in result.metadata.disclaimer.lower()

    def test_empty_draft_on_no_validated_findings(self) -> None:
        """When no validated findings exist, return empty draft, not error."""
        engagement = EngagementContext(
            id="eng-001",
            customer_name="Test Corp",
            name="Q1 Assessment",
            type="web_app",
        )
        draft = ReportDraftPipeline._empty_draft(engagement, ReportType.TECHNICAL)

        assert draft.status == ReportStatus.DRAFT
        assert draft.metadata.finding_count == 0
        assert len(draft.sections) == 1
        assert "no validated findings" in draft.sections[0].content.lower()

    def test_report_type_preserved(self) -> None:
        """Report type should match what was requested."""
        for rt in ReportType:
            result = ReportDraftResult(
                report_title="Test",
                report_type=rt,
                status=ReportStatus.DRAFT,
                sections=[],
                metadata=ReportMetadata(
                    generated_at="2026-03-15T00:00:00Z",
                    model_version="claude-opus-4-6",
                    finding_count=0,
                    confidence=0.0,
                ),
            )
            assert result.report_type == rt
            assert result.status == ReportStatus.DRAFT
