# User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Analyst Portal](#analyst-portal)
3. [Engagement Workflow](#engagement-workflow)
4. [Finding Triage & Validation](#finding-triage--validation)
5. [AI-Powered Analysis](#ai-powered-analysis)
6. [Report Generation](#report-generation)
7. [Security Administration](#security-administration)
8. [Customer Portal](#customer-portal)

---

## Getting Started

### Logging In

1. Navigate to `https://analyst.vapt-platform.com` (Analyst Portal) or `https://portal.vapt-platform.com` (Customer Portal)
2. Authenticate via Keycloak SSO (supports SAML, OIDC, LDAP federation)
3. MFA is required for sensitive operations (credential management, emergency overrides, audit log access)

### Role-Based Access

Your dashboard and available features depend on your assigned role:

| Role | Primary Functions |
|---|---|
| **Platform Admin** | Multi-tenant management, audit logs, system configuration |
| **Tenant Admin** | User management, IP allowlists, scan windows, credential management |
| **Engagement Manager** | Create/close engagements, assign analysts, approve reports |
| **Lead Analyst** | Validate findings, approve reports, deliver to customers |
| **Analyst** | Triage findings, run AI analysis, draft reports |
| **Scanner Operator** | Launch scans, manage scanner credentials |
| **Customer Admin** | View engagements, manage IP allowlists, download reports |
| **Customer Viewer** | Read-only access to engagements and reports |

---

## Analyst Portal

### Workbench

The primary analyst workspace at `/workbench` provides:

- **Dashboard** — Scan coverage charts, severity breakdown, scanner-level finding counts, real-time activity feed
- **Triage Queue** — Filterable finding cards with AI suggestion badges and bulk actions
- **Finding Detail** — Deep-dive view with evidence viewer, AI analysis card, validation panel
- **PoC Recorder** — Step-by-step proof-of-concept recording with request/response viewer and export

### Navigation

- **Sidebar** — Navigate between Dashboard, Triage, Findings, Reports, and Settings
- **Real-time Updates** — WebSocket-powered live notifications when findings are ingested or scans complete
- **Keyboard Shortcuts** — Optimized for analyst efficiency during high-volume triage

---

## Engagement Workflow

### Creating an Engagement

1. Go to **Engagements > New Engagement**
2. Fill in engagement details:
   - Client/tenant information
   - Scope definition (target URLs, IP ranges, mobile apps)
   - Assessment type (web app, network, mobile, API, cloud)
   - Timeline (start/end dates)
3. Configure scan windows (allowed days, time ranges, blackout dates)
4. Set up IP allowlists for scanner egress IPs
5. Assign analysts and scanner operators

### Engagement Lifecycle

```
Created → Scoping → Active (Scanning) → Analysis → Reporting → Delivered → Closed
```

### Scan Execution

Integrated scanner connectors:

| Scanner | Type | Connector |
|---|---|---|
| **Burp Suite** | Web application | `burp-connector` |
| **Tenable** | Network/infrastructure | `tenable-connector` |
| **Fortify** | Static analysis (SAST) | `fortify-connector` |
| **Mobile** | Mobile application | `mobile-connector` |

Scans are orchestrated via the scan-orchestrator service and execute within Kubernetes Jobs with resource limits (4 CPU, 8Gi memory per scan job).

### Scan Windows

Scans are restricted to approved time windows:

- Define allowed days (e.g., Monday-Friday) and hours (e.g., 09:00-18:00)
- Set blackout dates for change freezes or production events
- Target scope validation ensures scans only hit approved targets

**Emergency Overrides** require dual-approval from two Tenant Admin or Platform Admin users.

---

## Finding Triage & Validation

### Triage Queue

The triage view shows all incoming findings with:

- **Severity indicators** (Critical, High, Medium, Low, Informational)
- **AI suggestion badges** showing preliminary classification confidence
- **Source scanner** identification
- **Deduplication status** from the findings normalization service

### Bulk Actions

Select multiple findings to:
- Set severity in bulk
- Assign to an analyst
- Mark as false positive
- Tag for review

### Validation Panel

For each finding, the validation panel provides:

- **Verdict Selector** — True Positive, False Positive, Accepted Risk, Not Applicable
- **Validation Checklist** — Customizable per-finding-type verification steps
- **Validation Notes** — Free-text analyst commentary with timestamps
- **Evidence Viewer** — HTTP request/response pairs, screenshots, scanner raw output

### PoC Recording

For confirmed findings, record step-by-step proof of concept:

1. Open the finding and navigate to the **PoC** tab
2. Add steps with descriptions and HTTP request/response captures
3. Define the environment (browser, OS, tools used)
4. Export as standalone HTML or embed in the final report

---

## AI-Powered Analysis

The AI Analyst Assistant (powered by Claude) provides analysis across five pipeline stages. All AI outputs are **recommendations only** — analyst review is always required before action.

### Available Pipelines

#### 1. Vulnerability Summarization
- Generates human-readable summaries of scanner findings
- Contextualizes technical details for report audiences
- Input: Single finding with evidence

#### 2. False Positive Detection
- Analyzes finding evidence to assess likelihood of false positive
- Returns confidence score (0.0-1.0) with reasoning
- Findings with confidence < 0.80 are automatically flagged for mandatory analyst review
- Uses RAG context from historical similar findings

#### 3. Risk Prioritization
- Ranks findings by business risk considering:
  - CVSS score and exploitability
  - Asset criticality and exposure
  - Attack chain analysis (which findings combine for greater impact)
  - Compliance framework impact (PCI-DSS, OWASP, ISO 27001)
  - Threat intelligence (CISA KEV, EPSS scores)

#### 4. Remediation Guidance
- Generates specific remediation steps per finding
- Includes code examples and configuration changes
- References framework-specific best practices

#### 5. Report Drafting
- Generates complete report drafts from validated findings
- Includes executive summary, technical findings, remediation roadmap
- Outputs as DRAFT status — cannot be published without human approval

### AI Safety Controls

- **Prompt injection defense** — All finding data is sanitized and delimited with `[BEGIN/END FINDING DATA]` markers
- **RAG poisoning defense** — Suspiciously high-confidence FP context is filtered
- **Output sanitization** — XSS patterns are stripped from all AI responses
- **Token budgets** — 5M tokens/tenant/day limit prevents abuse
- **Human-in-the-loop** — Low-confidence results require analyst review

### Using AI Analysis

1. Select a finding in the triage view
2. Click **AI Analyze** to run summarization + FP detection
3. Review the AI Analysis Card showing:
   - Summary with confidence score
   - FP probability with reasoning
   - `requires_analyst_review` flag if confidence < 80%
4. Accept, modify, or reject AI recommendations
5. For batch analysis, select multiple findings and choose **Prioritize**

---

## Report Generation

### Supported Formats

| Format | Renderer | Use Case |
|---|---|---|
| **PDF** | WeasyPrint | Customer-facing deliverable |
| **DOCX** | python-docx | Editable working documents |
| **HTML** | Jinja2 | Web-based viewing and archival |

### Report Workflow

```
AI Draft → Generated → Under Review → Approved → Delivered
```

1. **Generate** — Select an engagement and click **Generate Report**
   - Choose report type and format (PDF, DOCX, HTML)
   - AI generates a draft from validated findings
2. **Review** — Submit the report for peer review
3. **Approve** — A different analyst must approve (four-eyes principle)
   - The approver **cannot** be the same person who generated the report
4. **Download** — Pre-signed MinIO URLs (15-minute expiry) for approved reports
5. **Deliver** — Mark as delivered to the customer with delivery method tracking

### Report Storage

- Reports are stored in per-tenant MinIO buckets
- Pre-signed download URLs validate tenant ownership and engagement assignment
- Report retention: 90 days (configurable)
- Maximum report size: 50 MB

---

## Security Administration

### Credential Management

Scanner credentials are managed through HashiCorp Vault:

1. **Store** — Credentials are encrypted in Vault with tenant-scoped paths
2. **Checkout** — Scanner operators check out time-boxed credentials (15-minute TTL)
   - Returns a Vault-wrapped response token (never plaintext)
   - Tracked with audit logging including pod name and source IP
3. **Checkin** — After scan completion, credentials are checked in and Vault lease is revoked
4. **Rotation** — Credentials can be rotated by Tenant Admins

### Scan Window Management

| Action | Required Role |
|---|---|
| Create scan window | Platform Admin, Tenant Admin, Engagement Manager |
| Check scan window | Any authenticated user |
| Emergency override request | Platform Admin, Tenant Admin |
| Emergency override approval | Platform Admin, Tenant Admin (different person) |

### IP Allowlist Management

Three types of IP allowlists per tenant:

| Type | Purpose |
|---|---|
| `platform_access` | Analyst/admin access source IPs |
| `scan_source` | Scanner egress NAT IPs |
| `scan_target` | Customer-approved scan target ranges |

- Rate limited: 10 entries per 60 seconds per tenant
- Maximum 500 entries per tenant
- Entries support expiration dates

### Audit Logs

All security-relevant actions are recorded with:

- Tamper-evident hash chains (each event hash includes the previous hash)
- 7-year retention in Elasticsearch with ILM
- Queryable by category, actor, resource, time range
- Categories: `auth`, `access`, `data`, `scan`, `report`, `credential`, `admin`, `security`

Access to audit logs requires Platform Admin or Tenant Admin role.

---

## Customer Portal

### Dashboard

Customer users see:

- Active engagement status and timeline
- Finding summary by severity
- Scan progress and coverage metrics

### Finding Access

- Read-only view of findings with full technical details
- Export findings in structured formats
- Customer Admin can manage their own IP allowlists

### Report Download

- View reports in all statuses
- Download approved/delivered reports via pre-signed URLs
- Track delivery history

---

## API Access

All platform features are available via REST API at `https://api.vapt-platform.com/api/v1/`.

Authentication: Include `Authorization: Bearer <JWT>` header on all requests.

### Key Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/v1/analyze` | POST | Run AI analysis on a finding |
| `/v1/prioritize` | POST | Batch risk prioritization |
| `/v1/reports/draft` | POST | Generate AI report draft |
| `/api/v1/reports` | POST | Generate final report |
| `/api/v1/reports/{id}/approve` | POST | Approve report (four-eyes) |
| `/api/v1/reports/{id}/download` | GET | Get pre-signed download URL |
| `/api/v1/security/auth/validate` | POST | Validate JWT and get RBAC context |
| `/api/v1/security/credentials/checkout` | POST | Checkout scanner credential |
| `/api/v1/security/scan-windows` | POST | Create scan window |
| `/api/v1/security/ip-allowlists` | POST/GET/DELETE | Manage IP allowlists |
| `/api/v1/security/audit/query` | POST | Query audit logs |
