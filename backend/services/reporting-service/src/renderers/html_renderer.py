"""HTML template renderer using Jinja2."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.config.settings import settings
from src.models.domain import (
    ReportDataBundle,
    ReportType,
)
from src.services.chart_generator import (
    generate_severity_bar_chart,
    generate_severity_pie_chart,
)

logger = structlog.get_logger()

# Map report type to section templates to include
REPORT_SECTIONS: dict[ReportType, list[dict]] = {
    ReportType.EXECUTIVE_SUMMARY: [
        {"template": "sections/executive_summary.html", "heading": "Executive Summary", "number": "1", "level": 1},
        {"template": "sections/scope_methodology.html", "heading": "Scope & Methodology", "number": "2", "level": 1},
        {"template": "sections/findings_summary.html", "heading": "Findings Summary", "number": "3", "level": 1},
    ],
    ReportType.FULL_TECHNICAL: [
        {"template": "sections/executive_summary.html", "heading": "Executive Summary", "number": "1", "level": 1},
        {"template": "sections/scope_methodology.html", "heading": "Scope & Methodology", "number": "2", "level": 1},
        {"template": "sections/findings_summary.html", "heading": "Findings Summary", "number": "3", "level": 1},
        {"template": "sections/finding_detail.html", "heading": "Detailed Findings", "number": "4", "level": 1},
        {"template": "sections/remediation_roadmap.html", "heading": "Remediation Roadmap", "number": "5", "level": 1},
        {"template": "sections/compliance_mapping.html", "heading": "Compliance Mapping", "number": "6", "level": 1},
    ],
    ReportType.REMEDIATION_ROADMAP: [
        {"template": "sections/executive_summary.html", "heading": "Executive Summary", "number": "1", "level": 1},
        {"template": "sections/findings_summary.html", "heading": "Findings Summary", "number": "2", "level": 1},
        {"template": "sections/remediation_roadmap.html", "heading": "Remediation Roadmap", "number": "3", "level": 1},
    ],
    ReportType.COMPLIANCE: [
        {"template": "sections/executive_summary.html", "heading": "Executive Summary", "number": "1", "level": 1},
        {"template": "sections/scope_methodology.html", "heading": "Scope & Methodology", "number": "2", "level": 1},
        {"template": "sections/compliance_mapping.html", "heading": "Compliance Mapping", "number": "3", "level": 1},
    ],
}


class HTMLRenderer:
    """Renders report data into a complete HTML document via Jinja2 templates."""

    def __init__(self) -> None:
        template_path = Path(settings.template_dir)
        self._env = Environment(
            loader=FileSystemLoader(str(template_path)),
            autoescape=select_autoescape(["html"]),
        )

    def render(
        self,
        bundle: ReportDataBundle,
        report_type: ReportType,
        *,
        report_title: str,
        report_version: int = 1,
        is_draft: bool = False,
    ) -> str:
        """Render the full HTML report from templates and data bundle."""
        # Load CSS
        css_path = Path(settings.template_dir) / "styles" / "report.css"
        base_css = css_path.read_text() if css_path.exists() else ""

        # Generate charts
        severity_pie_chart = generate_severity_pie_chart(bundle.statistics)
        severity_bar_chart = generate_severity_bar_chart(bundle.statistics)

        # Build template context
        context = {
            "report_title": report_title,
            "report_type_label": report_type.value.replace("_", " ").title(),
            "report_version": report_version,
            "generated_date": date.today().isoformat(),
            "is_draft": is_draft,
            "base_css": base_css,
            "mssp_logo_url": "",
            # Data
            "engagement": bundle.engagement,
            "findings": bundle.findings,
            "statistics": bundle.statistics,
            "compliance": bundle.compliance,
            "remediation_plan": bundle.remediation_plan,
            "branding": bundle.branding,
            # Charts
            "severity_pie_chart": severity_pie_chart,
            "severity_bar_chart": severity_bar_chart,
        }

        # Render section templates
        section_defs = REPORT_SECTIONS.get(report_type, REPORT_SECTIONS[ReportType.FULL_TECHNICAL])
        sections = []
        for sec_def in section_defs:
            template = self._env.get_template(sec_def["template"])
            rendered = template.render(**context)
            sections.append({
                "heading": sec_def["heading"],
                "number": sec_def["number"],
                "level": sec_def["level"],
                "rendered_content": rendered,
            })

        context["sections"] = sections
        context["appendices"] = []

        # Render base layout
        base_template = self._env.get_template("layouts/base.html")
        html_output = base_template.render(**context)

        logger.info("html_render_complete", report_type=report_type, length=len(html_output))
        return html_output
