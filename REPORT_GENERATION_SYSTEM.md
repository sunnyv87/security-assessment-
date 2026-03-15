# Report Generation System

## Overview

The Report Generation System produces professional VAPT engagement reports
across four document types and three export formats. Reports follow a
multi-stage lifecycle from AI-assisted drafting through analyst review to
customer delivery, with strict approval controls and audit trails.

---

## 1. Report Template Structure

### 1.1 Template Hierarchy

Every report is assembled from a **base layout** plus **report-type-specific
sections**. Customer branding (logo, colors, fonts) is injected at render time.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Base Report Layout                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Cover Page                                               │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ [Customer Logo]         [MSSP Logo]                 │  │  │
│  │  │                                                     │  │  │
│  │  │          {{ report.title }}                          │  │  │
│  │  │          {{ report.type | upper }}                   │  │  │
│  │  │                                                     │  │  │
│  │  │ Customer:  {{ engagement.customer_name }}            │  │  │
│  │  │ Date:      {{ report.generated_at | date }}          │  │  │
│  │  │ Version:   {{ report.version }}                      │  │  │
│  │  │ Class:     CONFIDENTIAL                              │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  Document Control                                         │  │
│  │  ┌──────────────┬────────────┬──────────────────┐        │  │
│  │  │ Version      │ Date       │ Author           │        │  │
│  │  │ {{ ver }}    │ {{ date }} │ {{ analyst }}     │        │  │
│  │  └──────────────┴────────────┴──────────────────┘        │  │
│  │  Distribution: {{ distribution_list }}                    │  │
│  │  Classification: CONFIDENTIAL                             │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  Table of Contents (auto-generated)                       │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │                                                           │  │
│  │  {{ report_type_sections }}                               │  │
│  │  (injected per report type — see below)                   │  │
│  │                                                           │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  Appendices                                               │  │
│  │  A. Methodology                                           │  │
│  │  B. Tool Inventory                                        │  │
│  │  C. Glossary                                              │  │
│  │  D. CVSS v4.0 Scoring Guide                               │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  Disclaimer & Legal                                       │  │
│  │  Digital Signature (X.509)                                │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Technical Vulnerability Report Template

```
┌─────────────────────────────────────────────────────────────────┐
│  SECTION STRUCTURE — Technical Vulnerability Report              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Executive Summary (1 page)                                   │
│     ├─ Engagement overview                                       │
│     ├─ Key statistics (total findings, by severity)              │
│     ├─ Risk rating (Critical / High / Medium / Low)              │
│     └─ Top 3 critical findings                                   │
│                                                                  │
│  2. Scope & Methodology                                          │
│     ├─ 2.1 Scope definition (in-scope assets/endpoints)         │
│     ├─ 2.2 Out-of-scope items                                   │
│     ├─ 2.3 Testing methodology (OWASP WSTG / PTES / NIST)      │
│     ├─ 2.4 Testing timeline                                     │
│     └─ 2.5 Tools used                                            │
│                                                                  │
│  3. Findings Summary                                             │
│     ├─ 3.1 Severity distribution chart                           │
│     │      ┌──────────────────────────┐                          │
│     │      │ [PIE CHART]              │                          │
│     │      │ Critical: 5  High: 12    │                          │
│     │      │ Medium: 23   Low: 15     │                          │
│     │      └──────────────────────────┘                          │
│     ├─ 3.2 Findings by category (CWE)                            │
│     ├─ 3.3 Findings by asset                                     │
│     └─ 3.4 Risk heat map                                         │
│                                                                  │
│  4. Detailed Findings (per finding)                              │
│     ├─ 4.N.1 Title & severity badge                              │
│     ├─ 4.N.2 Description                                        │
│     ├─ 4.N.3 CVSS score & vector                                │
│     ├─ 4.N.4 CWE classification                                 │
│     ├─ 4.N.5 Affected asset & endpoint                          │
│     ├─ 4.N.6 Evidence                                            │
│     │        ├─ HTTP request/response                            │
│     │        └─ Screenshots                                      │
│     ├─ 4.N.7 Reproduction steps                                 │
│     ├─ 4.N.8 Business impact                                    │
│     ├─ 4.N.9 Remediation guidance                                │
│     │        ├─ Summary                                          │
│     │        ├─ Detailed steps                                   │
│     │        ├─ Code examples (before/after)                     │
│     │        └─ References                                       │
│     └─ 4.N.10 Compliance mapping                                │
│                                                                  │
│  5. Remediation Roadmap (summary table)                          │
│     ├─ Priority order                                            │
│     ├─ Effort estimates                                          │
│     └─ Suggested timeline                                        │
│                                                                  │
│  6. Conclusion & Next Steps                                      │
│                                                                  │
│  Appendices A–D                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Executive Summary Report Template

```
┌─────────────────────────────────────────────────────────────────┐
│  SECTION STRUCTURE — Executive Summary Report (2-5 pages)       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Assessment Overview                                          │
│     ├─ Engagement purpose and scope                              │
│     ├─ Testing period                                            │
│     └─ Assessment type                                           │
│                                                                  │
│  2. Overall Risk Rating                                          │
│     ├─ Risk gauge visual (Critical/High/Medium/Low)              │
│     │   ┌────────────────────────────────────┐                   │
│     │   │         ╱ ▲ ╲                      │                   │
│     │   │    CRIT │   │ HIGH                 │                   │
│     │   │   ─────│ ● │─────                 │                   │
│     │   │    LOW  │   │ MED                  │                   │
│     │   │         ╲   ╱                      │                   │
│     │   │    Overall: HIGH RISK              │                   │
│     │   └────────────────────────────────────┘                   │
│     └─ Risk score trend (if retest available)                    │
│                                                                  │
│  3. Key Statistics                                               │
│     ├─ Total findings by severity (bar chart)                    │
│     ├─ Top vulnerability categories                              │
│     └─ Comparison to industry benchmarks                         │
│                                                                  │
│  4. Critical Findings Highlight                                  │
│     ├─ Finding title + severity + one-line impact                │
│     └─ (Critical and High findings only, max 10)                │
│                                                                  │
│  5. Strategic Recommendations                                    │
│     ├─ Immediate actions (0-30 days)                            │
│     ├─ Short-term improvements (30-90 days)                     │
│     └─ Long-term security program enhancements                  │
│                                                                  │
│  6. Conclusion                                                   │
│     └─ Overall security posture assessment                       │
└─────────────────────────────────────────────────────────────────┘
```

### 1.4 Remediation Roadmap Template

```
┌─────────────────────────────────────────────────────────────────┐
│  SECTION STRUCTURE — Remediation Roadmap                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Roadmap Overview                                             │
│     ├─ Total findings requiring remediation                      │
│     ├─ Estimated total effort                                    │
│     └─ Recommended timeline                                     │
│                                                                  │
│  2. Priority Matrix                                              │
│     ┌──────┬────────────┬─────────┬──────────┬────────────────┐ │
│     │ Rank │ Finding    │Severity │ Effort   │ Timeline       │ │
│     ├──────┼────────────┼─────────┼──────────┼────────────────┤ │
│     │ 1    │ SQLi Login │Critical │ 2 days   │ Immediate      │ │
│     │ 2    │ XSS Search │High     │ 1 day    │ Week 1         │ │
│     │ 3    │ IDOR API   │High     │ 3 days   │ Week 1-2       │ │
│     │ 4    │ CSRF Token │Medium   │ 4 hours  │ Week 2         │ │
│     │ ...  │ ...        │ ...     │ ...      │ ...            │ │
│     └──────┴────────────┴─────────┴──────────┴────────────────┘ │
│                                                                  │
│  3. Phase 1 — Immediate (0-7 days)                              │
│     ├─ Critical findings: fix details                            │
│     └─ Quick wins: low-effort high-impact fixes                 │
│                                                                  │
│  4. Phase 2 — Short-Term (1-4 weeks)                            │
│     ├─ High-severity findings                                    │
│     └─ Architecture-level changes                                │
│                                                                  │
│  5. Phase 3 — Medium-Term (1-3 months)                          │
│     ├─ Medium-severity findings                                  │
│     └─ Security program improvements                             │
│                                                                  │
│  6. Phase 4 — Long-Term (3-6 months)                            │
│     ├─ Low-severity findings                                     │
│     ├─ Defense-in-depth hardening                                │
│     └─ Security culture / training                               │
│                                                                  │
│  7. Verification & Retest Plan                                   │
│     ├─ Recommended retest date                                   │
│     ├─ Retest scope                                              │
│     └─ Success criteria                                          │
└─────────────────────────────────────────────────────────────────┘
```

### 1.5 Compliance Mapping Report Template

```
┌─────────────────────────────────────────────────────────────────┐
│  SECTION STRUCTURE — Compliance Mapping Report                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Compliance Overview                                          │
│     ├─ Frameworks assessed                                       │
│     ├─ Overall compliance posture                                │
│     └─ Compliance score per framework                            │
│                                                                  │
│  2. Framework Compliance Summary                                 │
│     ┌────────────────┬────────┬───────┬──────┬────────────────┐ │
│     │ Framework      │ Pass   │ Fail  │ N/A  │ Score          │ │
│     ├────────────────┼────────┼───────┼──────┼────────────────┤ │
│     │ OWASP Top 10   │ 7/10   │ 3/10  │ 0    │ 70%            │ │
│     │ PCI DSS 4.0    │ 18/24  │ 4/24  │ 2    │ 82%            │ │
│     │ SOC 2 Type II  │ 22/30  │ 5/30  │ 3    │ 81%            │ │
│     │ ISO 27001      │ 40/50  │ 7/50  │ 3    │ 85%            │ │
│     └────────────────┴────────┴───────┴──────┴────────────────┘ │
│                                                                  │
│  3. Detailed Control Mapping (per framework)                    │
│     ├─ 3.N.1 Control ID & description                           │
│     ├─ 3.N.2 Status (Pass / Fail / Partial / N/A)              │
│     ├─ 3.N.3 Related findings (linked by CWE)                  │
│     ├─ 3.N.4 Evidence of compliance or non-compliance           │
│     └─ 3.N.5 Remediation required for compliance               │
│                                                                  │
│  4. Gap Analysis                                                 │
│     ├─ Critical gaps (findings that cause compliance failure)   │
│     ├─ Gap severity vs. compliance impact matrix                │
│     └─ Remediation requirements for compliance                  │
│                                                                  │
│  5. Compliance Roadmap                                           │
│     ├─ Steps to achieve compliance                               │
│     ├─ Estimated effort                                          │
│     └─ Recommended reassessment date                             │
│                                                                  │
│  6. Attestation (if applicable)                                  │
│     └─ Compliance status statement                               │
└─────────────────────────────────────────────────────────────────┘
```

### 1.6 Template Data Model

```
Report Template
├── template_id: UUID
├── name: string
├── report_type: executive | technical | compliance | remediation_roadmap
├── version: int
├── base_layout: "layouts/base.html"
├── sections: Section[]
│   ├── section_id: string
│   ├── heading: string
│   ├── template_file: string          (Jinja2 HTML partial)
│   ├── order: int
│   ├── required: boolean
│   ├── data_source: string            (which data loader to call)
│   └── conditional: string | null     (render condition expression)
├── styles: ReportStyles
│   ├── primary_color: string
│   ├── heading_font: string
│   ├── body_font: string
│   ├── code_font: string
│   └── severity_colors: map
├── branding: CustomerBranding
│   ├── logo_url: string
│   ├── company_name: string
│   └── custom_css: string | null
├── page_setup: PageSetup
│   ├── size: "A4" | "letter"
│   ├── orientation: "portrait" | "landscape"
│   ├── margins: { top, right, bottom, left }
│   ├── header_template: string
│   └── footer_template: string
└── metadata: TemplateMetadata
    ├── created_by: string
    ├── created_at: datetime
    └── description: string
```

---

## 2. Report Generation Pipeline

### 2.1 Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Report Generation Pipeline                         │
│                                                                     │
│  Trigger                                                            │
│  ├── Analyst clicks "Generate Report" (sync API)                   │
│  ├── All findings validated (async Kafka event)                    │
│  └── Scheduled engagement completion (cron)                        │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Stage 1: DATA COLLECTION                                    │  │
│  │                                                               │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │  │
│  │  │ Findings     │  │ Engagement   │  │ Compliance       │   │  │
│  │  │ Service      │  │ Service      │  │ Engine           │   │  │
│  │  │              │  │              │  │                  │   │  │
│  │  │ • Validated  │  │ • Scope      │  │ • Control maps  │   │  │
│  │  │   findings   │  │ • Assets     │  │ • Gap analysis  │   │  │
│  │  │ • Evidence   │  │ • Timeline   │  │ • Scores        │   │  │
│  │  │ • PoCs       │  │ • Team       │  │                  │   │  │
│  │  │ • Remeds     │  │ • Customer   │  │                  │   │  │
│  │  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │  │
│  │         └─────────────────┼───────────────────┘              │  │
│  │                           ▼                                   │  │
│  │                   ReportDataBundle                             │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────▼──────────────────────────────────┐  │
│  │  Stage 2: CONTENT GENERATION                                  │  │
│  │                                                               │  │
│  │  ┌──────────────────┐     ┌─────────────────────────────┐   │  │
│  │  │ Static Sections  │     │ AI-Assisted Sections        │   │  │
│  │  │ (deterministic)  │     │ (Claude API)                │   │  │
│  │  │                  │     │                             │   │  │
│  │  │ • Cover page     │     │ • Executive summary         │   │  │
│  │  │ • Doc control    │     │ • Risk narrative             │   │  │
│  │  │ • Scope table    │     │ • Strategic recommendations │   │  │
│  │  │ • Finding data   │     │ • Conclusion                │   │  │
│  │  │ • Evidence       │     │                             │   │  │
│  │  │ • Charts/graphs  │     │ (AI content marked as       │   │  │
│  │  │ • Compliance     │     │  AI-generated for analyst   │   │  │
│  │  │   control tables │     │  to review/edit)            │   │  │
│  │  └──────┬───────────┘     └──────────┬──────────────────┘   │  │
│  │         └─────────────────┬──────────┘                       │  │
│  │                           ▼                                   │  │
│  │                  SectionContent[]                              │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────▼──────────────────────────────────┐  │
│  │  Stage 3: TEMPLATE RENDERING                                  │  │
│  │                                                               │  │
│  │  ┌────────────────────────────────────────────────────────┐  │  │
│  │  │  Jinja2 Engine                                         │  │  │
│  │  │                                                        │  │  │
│  │  │  base_layout.html                                      │  │  │
│  │  │    ├── cover_page.html                                 │  │  │
│  │  │    ├── document_control.html                           │  │  │
│  │  │    ├── table_of_contents.html (auto)                   │  │  │
│  │  │    ├── {{ report_type_sections }}                      │  │  │
│  │  │    │    ├── section_executive_summary.html             │  │  │
│  │  │    │    ├── section_scope.html                         │  │  │
│  │  │    │    ├── section_findings_summary.html              │  │  │
│  │  │    │    ├── section_finding_detail.html (per finding)  │  │  │
│  │  │    │    ├── section_remediation_roadmap.html           │  │  │
│  │  │    │    └── section_compliance_mapping.html            │  │  │
│  │  │    ├── appendix_methodology.html                       │  │  │
│  │  │    ├── appendix_tools.html                             │  │  │
│  │  │    └── appendix_glossary.html                          │  │  │
│  │  │                                                        │  │  │
│  │  │  + customer_branding.css                               │  │  │
│  │  │  + chart_images (pre-rendered SVGs)                    │  │  │
│  │  └────────────────────────────────────────────────────────┘  │  │
│  │                           │                                   │  │
│  │                    Rendered HTML                               │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                              │                                      │
│  ┌───────────────────────────▼──────────────────────────────────┐  │
│  │  Stage 4: FORMAT EXPORT                                       │  │
│  │                                                               │  │
│  │  ┌──────────┐   ┌───────────┐   ┌──────────────────────┐   │  │
│  │  │ PDF      │   │ DOCX      │   │ HTML                 │   │  │
│  │  │ Renderer │   │ Renderer  │   │ Packager             │   │  │
│  │  │          │   │           │   │                      │   │  │
│  │  │ WeasyPrint│   │ python-  │   │ Single-file HTML     │   │  │
│  │  │ CSS Paged│   │ docx     │   │ with embedded        │   │  │
│  │  │ Media    │   │ template │   │ images (base64)      │   │  │
│  │  └────┬─────┘   └────┬─────┘   └──────────┬───────────┘   │  │
│  │       └───────────────┼────────────────────┘               │  │
│  │                       ▼                                     │  │
│  │               Generated file(s)                             │  │
│  └───────────────────────┬──────────────────────────────────────┘  │
│                          │                                          │
│  ┌───────────────────────▼──────────────────────────────────────┐  │
│  │  Stage 5: STORAGE & DELIVERY                                  │  │
│  │                                                               │  │
│  │  ┌───────────┐   ┌────────────┐   ┌──────────────────────┐  │  │
│  │  │ MinIO     │   │ PostgreSQL │   │ Kafka Event          │  │  │
│  │  │ Upload    │   │ Record     │   │                      │  │  │
│  │  │           │   │            │   │ report.generated     │  │  │
│  │  │ Tenant-   │   │ file_path  │   │ → Notification Svc  │  │  │
│  │  │ isolated  │   │ file_hash  │   │ → WebSocket push    │  │  │
│  │  │ bucket    │   │ page_count │   │ → Email (optional)  │  │  │
│  │  └───────────┘   └────────────┘   └──────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  APPROVAL & DELIVERY WORKFLOW (post-generation)              │  │
│  │                                                               │  │
│  │  Generated ──▶ Under Review ──▶ Approved ──▶ Delivered       │  │
│  │     │              │                │              │          │  │
│  │     │         Analyst edits    Lead analyst    Customer       │  │
│  │     │         content in UI    approves        downloads      │  │
│  │     │                          (four-eyes)     from portal    │  │
│  │     │                                                         │  │
│  │     └── Failed (retry or manual intervention)                │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Collection Stage Detail

```
ReportDataBundle
├── engagement: EngagementData
│   ├── id, name, type, status
│   ├── customer (name, industry, logo_url)
│   ├── scope (description, in_scope_assets[], exclusions[])
│   ├── timeline (start_date, end_date, duration_days)
│   ├── team (lead_analyst, analysts[])
│   └── methodology (standard, version, reference_url)
│
├── findings: FindingData[]
│   ├── id, title, description
│   ├── severity, cvss_score, cvss_vector
│   ├── cwe_id, cwe_name, category
│   ├── asset, endpoint, http_method
│   ├── evidence (request, response, screenshots[])
│   ├── validation_verdict, validated_by, validated_at
│   ├── remediation (summary, steps[], code_examples[], references[])
│   ├── poc_steps[] (if PoC recorded)
│   └── compliance_controls[] (mapped controls)
│
├── statistics: ReportStatistics
│   ├── total_findings, by_severity{}, by_category{}, by_asset{}
│   ├── false_positive_count, false_positive_rate
│   ├── validated_count, validation_coverage
│   └── remediation_coverage (findings with remediation / total)
│
├── compliance: ComplianceData (if compliance report)
│   ├── frameworks[] (name, version, controls[])
│   ├── control_mappings[] (control_id → finding_ids[])
│   ├── scores_by_framework{}
│   └── gaps[] (control_id, severity, remediation_required)
│
├── remediation_plan: RemediationPlan (if roadmap)
│   ├── phases[] (name, timeline, findings[])
│   ├── total_effort_estimate
│   └── retest_recommendation
│
└── branding: CustomerBranding
    ├── logo_url, company_name
    ├── primary_color, secondary_color
    └── custom_css
```

### 2.3 Chart Generation

```
Charts rendered server-side as SVG for reliable PDF/DOCX embedding:

┌────────────────────────────────────────────────────────────┐
│  Chart Type               │ Used In                        │
├───────────────────────────┼────────────────────────────────┤
│ Severity pie chart        │ Technical, Executive           │
│ Severity bar chart        │ Executive                      │
│ Findings by category      │ Technical                      │
│ Findings by asset         │ Technical                      │
│ Risk heat map             │ Technical, Executive           │
│ Compliance score gauge    │ Compliance                     │
│ Compliance framework bars │ Compliance                     │
│ Remediation timeline      │ Roadmap                        │
│ Trend line (retest)       │ Executive (if retest data)     │
└───────────────────────────┴────────────────────────────────┘
```

### 2.4 Export Format Details

```
┌─────────┬──────────────────────────────────────────────────────┐
│ Format  │ Implementation                                       │
├─────────┼──────────────────────────────────────────────────────┤
│ PDF     │ WeasyPrint renders HTML+CSS to PDF                   │
│         │ • CSS Paged Media for headers/footers/page numbers   │
│         │ • @page rules for margins, size                      │
│         │ • SVG charts embedded inline                         │
│         │ • Screenshots as optimized PNGs                      │
│         │ • Table of contents with page numbers                │
│         │ • Watermark: "CONFIDENTIAL" or "DRAFT"               │
│         │ • Digital signature block on final page              │
├─────────┼──────────────────────────────────────────────────────┤
│ DOCX    │ python-docx builds Word document from template       │
│         │ • Pre-built .docx template with styles               │
│         │ • Heading styles mapped from HTML sections            │
│         │ • Tables for findings and compliance mapping          │
│         │ • Images embedded (charts, screenshots)              │
│         │ • Table of contents field (updates on open)          │
│         │ • Editable by customer for their own use             │
├─────────┼──────────────────────────────────────────────────────┤
│ HTML    │ Self-contained single-file HTML                      │
│         │ • All CSS inlined                                    │
│         │ • Images as base64 data URIs                         │
│         │ • Interactive table of contents                      │
│         │ • Customer portal preview mode                       │
│         │ • Print-friendly @media print styles                 │
└─────────┴──────────────────────────────────────────────────────┘
```

### 2.5 Customer Portal Download Flow

```
Customer logs into portal
        │
        ▼
┌──────────────────┐
│ Reports page     │
│                  │
│ Shows list of    │
│ delivered reports│
│ for their tenant │
└────────┬─────────┘
         │
    Click download
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│ API Gateway      │────▶│ Report Service   │
│ (JWT tenant      │     │                  │
│  validation)     │     │ 1. Verify report │
│                  │     │    belongs to    │
│                  │     │    customer's    │
│                  │     │    tenant        │
│                  │     │ 2. Verify report │
│                  │     │    status =      │
│                  │     │    'delivered'   │
│                  │     │ 3. Generate      │
│                  │     │    pre-signed    │
│                  │     │    MinIO URL     │
│                  │     │    (15 min TTL)  │
│                  │     │ 4. Log download  │
│                  │     │    in audit      │
│                  │     └──────┬───────────┘
│                  │            │
│                  │◀───────────┘
│                  │   302 Redirect to
│                  │   pre-signed URL
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ MinIO / S3       │
│ Direct download  │
│ (encrypted at    │
│  rest, per-      │
│  tenant bucket)  │
└──────────────────┘
```

### 2.6 Report Lifecycle State Machine

```
                    ┌──────────┐
     generate ─────▶│  QUEUED  │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │GENERATING│──────────────┐
                    └────┬─────┘              │
                         │               ┌────▼────┐
                    ┌────▼─────┐         │ FAILED  │
                    │GENERATED │         └─────────┘
                    └────┬─────┘
                         │
                  analyst reviews
                         │
                    ┌────▼────────┐
                    │UNDER_REVIEW │◀──── analyst edits
                    └────┬────────┘      (loops back)
                         │
                  lead analyst approves
                  (four-eyes principle)
                         │
                    ┌────▼─────┐
                    │ APPROVED │
                    └────┬─────┘
                         │
                  analyst publishes
                  (requires report:publish)
                         │
                    ┌────▼─────┐
                    │DELIVERED │
                    └──────────┘
```
