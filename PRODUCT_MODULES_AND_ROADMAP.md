# Product Modules & Development Roadmap

## AI-Driven VAPT Orchestration Platform — SaaS Product Plan

---

## Module Overview

```
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                              VAPT ORCHESTRATION PLATFORM                             ║
║                                                                                      ║
║  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ║
║  │   MODULE 1   │  │     MODULE 2     │  │     MODULE 3     │  │     MODULE 4     │  ║
║  │   CUSTOMER   │  │   ENGAGEMENT     │  │      SCAN        │  │    ANALYST       │  ║
║  │    PORTAL    │  │   MANAGEMENT     │  │  ORCHESTRATION   │  │   WORKBENCH      │  ║
║  │              │  │                  │  │                  │  │                  │  ║
║  │ • Onboarding │  │ • Intake & scope │  │ • Tool dispatch  │  │ • Triage queue   │  ║
║  │ • Dashboard  │  │ • Asset mgmt    │  │ • Scan windows   │  │ • AI assistant   │  ║
║  │ • Cred submit│  │ • Scheduling    │  │ • Credential mgmt│  │ • Validation     │  ║
║  │ • Reports    │  │ • Approvals     │  │ • Result ingest  │  │ • PoC builder    │  ║
║  │ • Billing    │  │ • SLA tracking  │  │ • IP allowlisting│  │ • Collaboration  │  ║
║  └──────┬───────┘  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  ║
║         │                   │                     │                     │             ║
║         └───────────────────┴──────────┬──────────┴─────────────────────┘             ║
║                                        │                                              ║
║                              ┌─────────▼─────────┐                                   ║
║                              │  SHARED PLATFORM   │                                   ║
║                              │  INFRASTRUCTURE    │                                   ║
║                              │  (IAM, Events,     │                                   ║
║                              │   Data, Security)  │                                   ║
║                              └─────────┬─────────┘                                   ║
║                                        │                                              ║
║         ┌───────────────────┬──────────┴──────────┬─────────────────────┐             ║
║         │                   │                     │                     │             ║
║  ┌──────▼───────┐  ┌───────▼──────────┐  ┌───────▼──────────┐                        ║
║  │   MODULE 5   │  │     MODULE 6     │  │    CROSS-CUT     │                        ║
║  │  REPORTING   │  │   COMPLIANCE     │  │    SERVICES      │                        ║
║  │              │  │    MAPPING       │  │                  │                        ║
║  │ • Generation │  │ • Framework mgmt │  │ • RBAC / IAM     │                        ║
║  │ • Templates  │  │ • Control map    │  │ • Audit logging  │                        ║
║  │ • Approval   │  │ • Gap analysis   │  │ • Tenant isolat. │                        ║
║  │ • Delivery   │  │ • Evidence link  │  │ • Notifications  │                        ║
║  │ • Archive    │  │ • Export / audit  │  │ • API gateway    │                        ║
║  └──────────────┘  └──────────────────┘  └──────────────────┘                        ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝
```

---

## Module 1: Customer Portal

**Purpose:** Self-service interface for MSSP customers to manage engagements, submit credentials, track progress, and download reports.

### Capabilities

| Capability | Description | Priority |
|-----------|-------------|----------|
| Customer onboarding | Self-service registration, org setup, user invites | P0 |
| Engagement dashboard | Live status, scan progress, SLA timers | P0 |
| Credential submission | Encrypted upload via Vault Transit, no plaintext exposure | P0 |
| Report downloads | Access approved reports (PDF/DOCX), download history | P0 |
| Asset inventory view | Read-only view of scoped assets and scan coverage | P1 |
| Billing & subscriptions | Plan management, usage metering, invoice history | P1 |
| Notification preferences | Email/Slack/webhook notification configuration | P2 |
| Compliance dashboard | Posture overview, framework progress, evidence access | P2 |

### Frontend

| Component | Tech | Details |
|-----------|------|---------|
| SPA shell | Next.js 14 App Router | SSR for SEO, CSR for interactive views |
| Auth | Keycloak OIDC | Customer realm, social login (Google, Azure AD) |
| Forms | react-hook-form + zod | Credential submission, engagement requests |
| Real-time | WebSocket | Scan progress, finding count live updates |
| Charts | recharts | Severity breakdown, scan timeline, SLA gauges |

### Backend Services Consumed

```
Customer Portal
  ├── Engagement Service      (CRUD, status, timeline)
  ├── Asset Service            (read-only inventory)
  ├── Credential Vault         (submit/rotate credentials)
  ├── Reporting Service        (download approved reports)
  ├── Compliance Engine        (posture dashboard)
  ├── Security Services        (auth, RBAC)
  └── Notification Service     (preference management)
```

### Data Scope

- Tenant-scoped: all data filtered by `tenant_id` via RLS
- Roles: `CUSTOMER_ADMIN`, `CUSTOMER_VIEWER`
- No access to findings detail until report approved and delivered
- Credential values never returned after submission

---

## Module 2: Engagement Management

**Purpose:** End-to-end lifecycle management for VAPT engagements — from intake through scoping, execution tracking, and closure.

### Capabilities

| Capability | Description | Priority |
|-----------|-------------|----------|
| Engagement intake | Create engagement, define type (full VAPT, web-only, infra, mobile, compliance) | P0 |
| Scope definition | Assign assets, scan types, exclusions per engagement | P0 |
| Analyst assignment | Assign primary/secondary analysts, engagement managers | P0 |
| Approval workflows | Customer approval of scope, analyst approval of scan plan | P0 |
| SLA tracking | Configurable SLA timers per engagement type, breach alerts | P0 |
| Asset management | Register web apps, APIs, IPs, mobile apps; track asset metadata | P0 |
| Scheduling | Set engagement dates, scan windows, blackout periods | P1 |
| Timeline & audit | Full event log: who did what, when, status transitions | P1 |
| Templates | Reusable engagement templates for recurring assessments | P2 |
| Bulk operations | Launch/close multiple engagements, bulk asset import (CSV) | P2 |

### Microservices

| Service | Responsibility | Tech |
|---------|---------------|------|
| Engagement Service | Engagement CRUD, lifecycle, SLA, status aggregation | Go 1.22 / Gin / PostgreSQL |
| Asset Discovery Service | Asset registration, DNS/port enumeration, metadata | Python 3.12 / FastAPI |

### API Surface

```
POST   /api/v1/engagements                    Create engagement
GET    /api/v1/engagements                    List (paginated, filtered)
GET    /api/v1/engagements/{id}               Get details
PATCH  /api/v1/engagements/{id}               Update metadata
POST   /api/v1/engagements/{id}/scope         Define scope
POST   /api/v1/engagements/{id}/launch        Launch scans
POST   /api/v1/engagements/{id}/close         Close engagement
GET    /api/v1/engagements/{id}/status        Aggregated status
GET    /api/v1/engagements/{id}/timeline      Audit trail

POST   /api/v1/assets                         Register asset
GET    /api/v1/assets                         List assets
GET    /api/v1/assets/{id}                    Asset details
POST   /api/v1/assets/{id}/discover           Trigger discovery scan
GET    /api/v1/assets/{id}/scan-history       Past scan results
```

### Kafka Events

| Event | Direction | Triggers |
|-------|-----------|----------|
| `engagement.created` | Produces | Notification to assigned team |
| `engagement.launched` | Produces | Scan Orchestration begins dispatch |
| `engagement.closed` | Produces | Reporting finalization, archival |
| `scan.completed` | Consumes | Updates engagement progress counters |
| `finding.validated` | Consumes | Updates finding counts on engagement |

### State Machine

```
  draft ──► scoping ──► approved ──► in_progress ──► review ──► closed
                │                        │               │
                ▼                        ▼               ▼
            cancelled              on_hold          reopened ──► in_progress
```

---

## Module 3: Scan Orchestration

**Purpose:** Automated coordination of multi-tool vulnerability scans with credential management, scheduling constraints, and result normalization.

### Capabilities

| Capability | Description | Priority |
|-----------|-------------|----------|
| Multi-tool dispatch | Orchestrate Burp Suite, Tenable, Fortify, MobSF, Nuclei scans | P0 |
| Credential checkout | Time-boxed Vault leases, auto-revocation post-scan | P0 |
| Scan window enforcement | Timezone-aware scheduling, blackout dates, day/time constraints | P0 |
| IP allowlisting | 3-tier: platform access, scan source IPs, scan target validation | P0 |
| Result ingestion | Parse scanner-native formats, normalize to common finding schema | P0 |
| Scan pipeline DAG | Temporal.io workflows: discovery → DAST → SAST → infra → mobile | P0 |
| Finding deduplication | Cross-scanner dedup by CWE + endpoint + parameter fingerprint | P1 |
| Retry & circuit breaker | Auto-retry failed scans, circuit break on scanner API failures | P1 |
| Emergency override | Dual-approval bypass of scan window restrictions | P1 |
| Scanner health monitoring | Connectivity checks, license tracking, capacity monitoring | P2 |
| Custom scanner plugins | Plugin interface for adding new scanner integrations | P2 |

### Microservices

| Service | Responsibility | Tech |
|---------|---------------|------|
| Scan Orchestration Service | Temporal workflows, pipeline DAG, scheduling | Python 3.12 / Temporal |
| Burp Suite Connector | Burp Enterprise API, DAST dispatch | Python 3.12 / gRPC |
| Tenable Connector | Tenable.io API, infrastructure scanning | Python 3.12 / gRPC |
| Fortify Connector | Fortify on Demand / SSC, SAST/SCA | Python 3.12 / gRPC |
| Mobile Connector | MobSF API, mobile app scanning | Python 3.12 / gRPC |
| Findings Normalization Service | Parser per scanner, common schema, dedup | Python 3.12 / FastAPI |
| Security Services | Scan windows, IP allowlists, credential vault | Python 3.12 / FastAPI |

### Scan Pipeline

```
engagement.launched (Kafka)
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│                 TEMPORAL WORKFLOW ENGINE                       │
│                                                               │
│  Step 1: Validate scope                                       │
│    └─► Check IP allowlists                                    │
│    └─► Verify scan window is open                             │
│    └─► Confirm engagement status = in_progress                │
│                                                               │
│  Step 2: Acquire resources                                    │
│    └─► Checkout credentials from Vault (TTL: 4h)              │
│    └─► Reserve scanner capacity                               │
│    └─► Allocate gVisor sandbox pod                            │
│                                                               │
│  Step 3: Execute scans (parallel where possible)              │
│    ├─► DAST (Burp Suite) ─────────────────────┐               │
│    ├─► Infrastructure (Tenable) ──────────────┤               │
│    ├─► SAST/SCA (Fortify) ───────────────────┤               │
│    └─► Mobile (MobSF) ───────────────────────┤               │
│                                          scan.completed       │
│  Step 4: Normalize & deduplicate              │               │
│    └─► Parse native formats ◄─────────────────┘               │
│    └─► Map to common schema                                   │
│    └─► Cross-scanner deduplication                            │
│    └─► Produce finding.normalized events                      │
│                                                               │
│  Step 5: Cleanup                                              │
│    └─► Checkin credentials                                    │
│    └─► Destroy sandbox pod                                    │
│    └─► Update engagement status                               │
└───────────────────────────────────────────────────────────────┘
```

### Execution Isolation

| Control | Implementation |
|---------|---------------|
| Kernel isolation | gVisor (runsc) RuntimeClass on scanner pods |
| Network restriction | NetworkPolicy: egress only to approved scan targets |
| Time limit | 4-hour hard deadline per scan job |
| Storage | Ephemeral: emptyDir destroyed on pod termination |
| Credential scope | Vault lease per engagement, auto-revoke on expiry |

---

## Module 4: Analyst Workbench

**Purpose:** Primary workspace for security analysts to triage, validate, enrich, and remediate vulnerability findings with AI assistance.

### Capabilities

| Capability | Description | Priority |
|-----------|-------------|----------|
| Triage queue | Drag-and-drop finding triage, bulk status updates, AI suggestions | P0 |
| Finding detail view | Full vulnerability details, request/response, evidence | P0 |
| AI analysis | Claude-powered summarization, FP detection, risk prioritization | P0 |
| Validation workflow | Structured checklist, verdict selection, evidence attachment | P0 |
| Remediation editor | Rich-text editor, code examples, severity adjustment | P0 |
| PoC builder | Step-by-step reproduction recorder, request/response capture | P1 |
| Collaboration | Real-time co-editing (Yjs CRDT), @mentions, comments | P1 |
| Engagement overview | Per-engagement dashboard: progress bars, SLA countdown, coverage | P1 |
| Keyboard shortcuts | Full keyboard navigation for high-throughput triage | P2 |
| Custom workflows | Configurable triage stages per engagement template | P2 |

### Frontend Components

```
/workbench
├── WorkbenchLayout.tsx          Shell: sidebar + content area
├── /dashboard
│   ├── SeverityBreakdown.tsx    Donut chart by severity
│   ├── ScanCoverageChart.tsx    Coverage heatmap
│   ├── FindingsByScanner.tsx    Bar chart per tool
│   └── ActivityFeed.tsx         Real-time event stream
├── /triage
│   ├── FindingTriage.tsx        Main triage view
│   ├── FindingCard.tsx          Draggable finding card
│   ├── TriageFilters.tsx        Multi-facet filter panel
│   ├── BulkActions.tsx          Bulk status/assign
│   └── AiSuggestionBadge.tsx    AI confidence indicator
├── /findings
│   ├── FindingDetailPanel.tsx   Split-pane detail view
│   ├── DetailsTab.tsx           Vuln details, parameters, endpoints
│   ├── EvidenceViewer.tsx       Screenshot, request/response viewer
│   ├── AiAnalysisCard.tsx       AI summary, FP probability, remediation
│   └── FindingTabs.tsx          Tab navigation
├── /validation
│   ├── ValidationPanel.tsx      Structured validation workflow
│   ├── ValidationChecklist.tsx  Checklist per finding type
│   ├── VerdictSelector.tsx      True positive / FP / accepted risk
│   └── ValidationNotes.tsx      Rich-text analyst notes
├── /remediation
│   ├── RemediationGuidance.tsx  AI + manual remediation text
│   ├── RemediationEditor.tsx    TipTap rich-text editor
│   ├── CodeExample.tsx          Syntax-highlighted fix snippets
│   ├── SeverityUpdater.tsx      Adjust severity with justification
│   └── ReferenceLinks.tsx       CWE, OWASP, CVE links
└── /poc
    ├── PocRecorder.tsx          Step recorder
    ├── PocStep.tsx              Individual reproduction step
    ├── PocEnvironment.tsx       Environment details capture
    ├── RequestResponseViewer.tsx HTTP request/response viewer
    └── PocExport.tsx            Export PoC as Markdown/HTML
```

### Backend Services

| Service | Role |
|---------|------|
| Analyst Workflow Service | Finding assignment, triage state, validation state |
| Findings Service | Finding CRUD, search, filtering, dedup merge |
| AI Analyst Assistant | Summarization, FP detection, prioritization, remediation |
| Engagement Service | Engagement context, SLA tracking |

### AI Assistant Integration

```
Analyst clicks "Analyze" on a finding
        │
        ▼
POST /v1/analyze  ──►  AI Analyst Assistant
                         │
                         ├── Stage 1: Summarization
                         │     Structured summary, affected components, attack vector
                         │
                         ├── Stage 2: False Positive Detection
                         │     Confidence score (0–1), reasoning, evidence assessment
                         │
                         ├── Stage 3: Risk Prioritization
                         │     Business impact, exploitability, threat intel correlation
                         │
                         └── Stage 4: Remediation Generation
                               Framework-specific fix, code examples, effort estimate
                         │
                         ▼
              AiAnalysisCard.tsx renders results
              Analyst reviews, accepts/modifies, proceeds
```

### Guardrails

- AI outputs are **recommendations only** — marked "AI-GENERATED"
- AI cannot change finding status, approve reports, or publish anything
- All AI results require explicit analyst action before taking effect
- Confidence scores displayed: analyst decides threshold for trust

---

## Module 5: Reporting

**Purpose:** Generate, review, approve, and deliver professional VAPT reports in multiple formats with four-eyes approval workflow.

### Capabilities

| Capability | Description | Priority |
|-----------|-------------|----------|
| Multi-format generation | PDF (WeasyPrint), DOCX (python-docx), HTML | P0 |
| Report types | Executive Summary, Full Technical, Remediation Roadmap, Compliance | P0 |
| Four-eyes approval | Generator ≠ approver, review → approve → deliver workflow | P0 |
| Template engine | Jinja2 templates with section composition per report type | P0 |
| Pre-signed downloads | MinIO pre-signed URLs, tenant-scoped buckets | P0 |
| AI draft generation | AI-generated initial draft for analyst editing | P1 |
| Chart generation | Severity breakdown, scan coverage, remediation timeline SVGs | P1 |
| Custom branding | Per-tenant logo, color scheme, disclaimer text | P1 |
| Version history | Track report revisions, diff between versions | P2 |
| Batch generation | Generate reports for multiple engagements in parallel | P2 |

### Report Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    5-STAGE REPORT PIPELINE                          │
│                                                                     │
│  ┌──────────────┐    ┌─────────────────┐    ┌──────────────────┐   │
│  │ 1. DATA      │    │ 2. CONTENT      │    │ 3. TEMPLATE      │   │
│  │ COLLECTION   │───►│ GENERATION      │───►│ RENDERING        │   │
│  │              │    │                 │    │                  │   │
│  │ • Findings   │    │ • Statistics    │    │ • Jinja2 → HTML  │   │
│  │ • Engagement │    │ • Charts (SVG)  │    │ • Section        │   │
│  │ • Compliance │    │ • Risk scores   │    │   composition    │   │
│  │ • Assets     │    │ • Exec summary  │    │ • CSS styling    │   │
│  └──────────────┘    └─────────────────┘    └────────┬─────────┘   │
│                                                       │             │
│  ┌──────────────────────────────────────┐    ┌───────▼──────────┐  │
│  │ 5. STORAGE & DELIVERY               │◄───│ 4. FORMAT        │  │
│  │                                      │    │ EXPORT           │  │
│  │ • MinIO upload (tenant bucket)       │    │                  │  │
│  │ • Pre-signed download URL            │    │ • HTML → PDF     │  │
│  │ • Kafka: report.generated            │    │ • HTML → DOCX    │  │
│  │ • Audit log entry                    │    │ • Raw HTML       │  │
│  └──────────────────────────────────────┘    └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Approval Workflow

```
  DRAFT ──► IN_REVIEW ──► APPROVED ──► DELIVERED
    │           │              │
    ▼           ▼              ▼
 CANCELLED  REVISION_REQ   (immutable)

Rules:
  • Generator cannot approve their own report (four-eyes)
  • Approval requires REPORT_APPROVE permission + MFA
  • Delivery requires REPORT_DELIVER permission + MFA
  • Delivered reports are immutable — new version for changes
  • Download endpoint returns 403 until status = APPROVED | DELIVERED
```

### API Surface

```
POST   /api/v1/reports                        Generate report (202 Accepted)
GET    /api/v1/reports/{id}                   Report metadata & status
GET    /api/v1/reports/{id}/download          Pre-signed download URL
POST   /api/v1/reports/{id}/review            Submit for peer review
POST   /api/v1/reports/{id}/approve           Approve (four-eyes enforced)
POST   /api/v1/reports/{id}/deliver           Mark as delivered to customer
GET    /api/v1/reports                        List reports (filtered)
```

---

## Module 6: Compliance Mapping

**Purpose:** Map vulnerability findings to regulatory and security frameworks, track compliance posture, and generate compliance-specific reports.

### Capabilities

| Capability | Description | Priority |
|-----------|-------------|----------|
| Framework management | CRUD for compliance frameworks (SOC 2, ISO 27001, PCI DSS 4.0, NIST CSF, OWASP ASVS, GDPR) | P0 |
| Control catalog | Hierarchical control library per framework with descriptions | P0 |
| Finding → control mapping | Link findings to violated controls (CWE-based auto-mapping + manual override) | P0 |
| Gap analysis | Per-engagement compliance gap report: passing/failing/not-tested controls | P0 |
| Evidence linking | Attach scan evidence, finding screenshots, remediation proof to controls | P1 |
| Posture dashboard | Cross-engagement compliance posture per tenant | P1 |
| Export | Compliance matrix export (Excel, PDF), auditor-ready format | P1 |
| Custom frameworks | Tenant-defined control frameworks for internal policies | P2 |
| Trend analysis | Compliance posture over time, improvement tracking | P2 |
| Control inheritance | Map parent controls to child controls across frameworks | P2 |

### Data Model

```
┌──────────────────────┐     ┌──────────────────────┐
│ compliance_frameworks │     │ compliance_controls   │
│ ──────────────────── │     │ ──────────────────── │
│ id (PK)              │────►│ id (PK)              │
│ name                 │  1:N│ framework_id (FK)     │
│ version              │     │ control_id (string)   │
│ description          │     │ title                 │
│ category             │     │ description           │
│ is_custom            │     │ parent_control_id     │
│ tenant_id (nullable) │     │ category              │
└──────────────────────┘     │ testing_guidance      │
                              └──────────┬───────────┘
                                         │
                                         │ N:M
                                         ▼
                              ┌──────────────────────┐
                              │ finding_control_maps  │
                              │ ──────────────────── │
                              │ finding_id (FK)       │
                              │ control_id (FK)       │
                              │ mapping_source        │
                              │   (auto | manual)     │
                              │ confidence            │
                              │ status                │
                              │   (violated|passing|  │
                              │    not_tested)        │
                              └──────────┬───────────┘
                                         │
                                         │ 1:N
                                         ▼
                              ┌──────────────────────┐
                              │ compliance_evidence   │
                              │ ──────────────────── │
                              │ id (PK)              │
                              │ control_map_id (FK)  │
                              │ evidence_type         │
                              │ evidence_url          │
                              │ notes                 │
                              │ uploaded_by           │
                              └──────────────────────┘
```

### Auto-Mapping Logic

```
Finding ingested with CWE-79 (XSS)
        │
        ▼
CWE → Control Mapping Table
        │
        ├── PCI DSS 4.0 → 6.2.4 (Software engineering techniques prevent attacks)
        ├── OWASP ASVS → V5.3.3 (Output encoding)
        ├── ISO 27001 → A.8.26 (Application security requirements)
        ├── SOC 2 → CC6.1 (Logical access security)
        └── NIST CSF → PR.DS-5 (Data leak protections)
        │
        ▼
Auto-created finding_control_maps (mapping_source = 'auto', status = 'violated')
Analyst can override or add manual mappings
```

### API Surface

```
GET    /api/v1/compliance/frameworks                     List frameworks
POST   /api/v1/compliance/frameworks                     Create custom framework
GET    /api/v1/compliance/frameworks/{id}/controls       List controls in framework
POST   /api/v1/compliance/mappings                       Create finding→control mapping
GET    /api/v1/compliance/mappings?engagement_id=X       Get mappings for engagement
PATCH  /api/v1/compliance/mappings/{id}                  Update mapping status
GET    /api/v1/compliance/gap-analysis/{engagement_id}   Gap analysis report
GET    /api/v1/compliance/posture/{tenant_id}            Tenant compliance posture
POST   /api/v1/compliance/evidence                       Upload evidence
GET    /api/v1/compliance/export/{engagement_id}         Export compliance matrix
```

---

## Cross-Cutting Services

These services are shared across all modules and are not module-specific:

| Service | Purpose | Used By |
|---------|---------|---------|
| Security Services | RBAC enforcement, JWT validation, MFA gates | All modules |
| Credential Vault | Secret storage, Transit encryption, time-boxed leases | Engagement, Scan, Customer Portal |
| Audit Logger | Tamper-evident event logging (SHA-256 hash chain) | All modules |
| Tenant Isolation | PostgreSQL RLS, middleware enforcement | All modules |
| Notification Service (Teams Bot) | Slack/Teams/email alerts, approval notifications | All modules |
| API Gateway (Kong) | Rate limiting, JWT validation, tenant routing, mTLS | All modules |
| Kafka Event Bus | Async event backbone, 8 topics | Engagement, Scan, Findings, Reporting |

---

## Module Dependency Matrix

```
                  Customer  Engagement   Scan     Analyst   Reporting  Compliance
                  Portal    Management   Orch.    Workbench
Customer Portal     —         READ        —        —         READ        READ
Engagement Mgmt   NOTIFY       —        TRIGGER    —          —           —
Scan Orch.          —        CONSUMES     —        —          —           —
Analyst Workbench   —         READ       READ       —        TRIGGER     READ
Reporting           —         READ        —        READ        —         READ
Compliance          —         READ        —        READ       READ        —
```

Legend: READ = reads data from, TRIGGER = initiates action in, CONSUMES = event-driven consumer, NOTIFY = sends notifications to

---

# Development Roadmap

## Phase Overview

```
                            2026
    Q2 (Apr-Jun)        Q3 (Jul-Sep)        Q4 (Oct-Dec)        Q1 2027 (Jan-Mar)
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │   PHASE 1   │     │   PHASE 2   │     │   PHASE 3   │     │   PHASE 4   │
  │  FOUNDATION │────►│  CORE VAPT  │────►│  SCALE &    │────►│  ENTERPRISE │
  │             │     │  PIPELINE   │     │  AUTOMATE   │     │  FEATURES   │
  │  10 weeks   │     │  12 weeks   │     │  10 weeks   │     │  10 weeks   │
  └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘

  • Platform infra    • Scan orchestration • AI analyst         • Custom frameworks
  • IAM & security    • Finding pipeline   • Compliance mapping  • Multi-region
  • Engagement CRUD   • Analyst workbench  • Customer portal     • White-labeling
  • Data layer        • Basic reporting    • Advanced reporting  • Marketplace
```

---

## Phase 1: Foundation (Weeks 1–10)

**Goal:** Deployable platform with identity, data layer, engagement management, and security controls. Internal users can create and manage engagements.

### Sprint Breakdown

#### Sprint 1–2 (Weeks 1–4): Infrastructure & Identity

| Task | Module | Deliverable |
|------|--------|-------------|
| Provision Kubernetes cluster | Infra | EKS/AKS cluster, 4 node pools, namespaces |
| Deploy data stores | Infra | PostgreSQL 16 (CloudNativePG), Redis, Kafka (Strimzi) |
| Deploy Vault | Infra | HA Vault with Raft, KMS auto-unseal, Transit engine |
| Configure Kong Gateway | Infra | Ingress routes, rate limiting, TLS termination |
| Deploy Keycloak | Cross-cut | OIDC/SAML realm, MFA policy, role mappings |
| Implement RBAC service | Cross-cut | JWT validation, 8 roles, 35 permissions, tenant isolation |
| Set up audit logging | Cross-cut | Kafka producer, hash chain, Elasticsearch sink |
| PostgreSQL RLS policies | Cross-cut | Row-level security on all tables, tenant isolation |
| Deploy monitoring stack | Infra | Prometheus, Grafana, Loki, Tempo, Alertmanager |
| CI/CD pipeline | Infra | GitOps (ArgoCD), image build, security scanning |

**Exit Criteria:**
- [ ] Authenticated user can obtain JWT and access API gateway
- [ ] RBAC enforces tenant isolation (cross-tenant request returns 403)
- [ ] Audit events flow through Kafka → Elasticsearch
- [ ] Monitoring dashboards show cluster and service health
- [ ] All pods pass security context enforcement (non-root, read-only rootfs)

#### Sprint 3–5 (Weeks 5–10): Engagement Management

| Task | Module | Deliverable |
|------|--------|-------------|
| Engagement Service | Module 2 | Full CRUD, state machine, SLA tracking |
| Asset Service | Module 2 | Asset registration, metadata, DNS enumeration |
| Engagement API routes | Module 2 | 9 REST endpoints with validation |
| Kafka event producers | Module 2 | engagement.created, engagement.launched events |
| Credential Vault integration | Cross-cut | Store/checkout/checkin workflow, TTL enforcement |
| Scan window service | Module 3 | Window CRUD, timezone-aware enforcement |
| IP allowlist service | Module 3 | 3-tier allowlisting, CIDR validation |
| Network policies | Infra | Default-deny, service-to-service rules |
| Integration tests | All | End-to-end engagement creation → credential submission |
| API documentation | All | OpenAPI specs for all Phase 1 endpoints |

**Exit Criteria:**
- [ ] Create engagement → define scope → assign analyst → launch (produces Kafka event)
- [ ] Credentials stored in Vault with Transit encryption, checkout returns decrypted value
- [ ] Scan window blocks scan launch outside allowed times
- [ ] IP allowlist rejects scan targets not in approved CIDRs
- [ ] All endpoints return appropriate 4xx errors for unauthorized access

### Phase 1 Architecture

```
┌──────────────┐     ┌───────────────┐     ┌──────────────────┐
│ Keycloak     │     │ Kong Gateway  │     │ Prometheus/      │
│ (Identity)   │     │ (API GW)      │     │ Grafana          │
└──────┬───────┘     └───────┬───────┘     └──────────────────┘
       │                     │
       │    ┌────────────────┼────────────────┐
       │    │                │                │
       ▼    ▼                ▼                ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ Engagement     │  │ Asset          │  │ Security       │
│ Service        │  │ Service        │  │ Services       │
└───────┬────────┘  └────────────────┘  └────────────────┘
        │
        ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ PostgreSQL     │  │ Kafka          │  │ Vault          │
│ (CloudNativePG)│  │ (Strimzi)      │  │ (HA Raft)      │
└────────────────┘  └────────────────┘  └────────────────┘
```

---

## Phase 2: Core VAPT Pipeline (Weeks 11–22)

**Goal:** End-to-end scan → findings → triage → report pipeline. Analysts can run scans, triage findings, and generate reports.

### Sprint Breakdown

#### Sprint 6–8 (Weeks 11–16): Scan Orchestration & Findings

| Task | Module | Deliverable |
|------|--------|-------------|
| Scan Orchestration Service | Module 3 | Temporal workflows, pipeline DAG |
| Burp Suite Connector | Module 3 | Burp Enterprise API integration, DAST dispatch |
| Tenable Connector | Module 3 | Tenable.io API, infrastructure scan dispatch |
| gVisor sandbox setup | Module 3 | RuntimeClass, scanner pod template |
| Findings Normalization Service | Module 3 | Parser per scanner, common schema, dedup |
| Credential checkout integration | Module 3 | Vault lease per scan, auto-revocation |
| Scan window enforcement | Module 3 | Pre-launch validation, emergency override |
| MinIO deployment | Infra | Distributed mode, tenant-isolated buckets |
| scan.requested → scan.completed flow | Module 3 | Full Kafka event pipeline |
| finding.normalized events | Module 3 | Normalized findings published to Kafka |

**Exit Criteria:**
- [ ] Launch engagement → Burp + Tenable scans execute in gVisor sandbox
- [ ] Scan results parsed and normalized to common finding schema
- [ ] Findings deduplicated across scanners
- [ ] Credentials auto-revoked after scan completion
- [ ] Scanner pod destroyed after scan, no persistent state

#### Sprint 9–11 (Weeks 17–22): Analyst Workbench & Reporting

| Task | Module | Deliverable |
|------|--------|-------------|
| Analyst Portal shell | Module 4 | Next.js app, auth, sidebar, routing |
| Triage queue UI | Module 4 | Finding cards, drag-and-drop, bulk actions |
| Finding detail panel | Module 4 | Split-pane, evidence viewer, tabs |
| Validation workflow | Module 4 | Checklist, verdict selector, notes |
| AI Analyst Assistant | Module 4 | Summarization, FP detection, remediation |
| Reporting Service | Module 5 | PDF/DOCX generation, template engine |
| Report approval workflow | Module 5 | Four-eyes, review → approve → deliver |
| Dashboard components | Module 4 | Severity breakdown, coverage chart, activity feed |
| WebSocket real-time updates | Module 4 | Live finding count, scan progress |
| Analyst Workflow Service | Module 4 | Finding assignment, triage state management |

**Exit Criteria:**
- [ ] Analyst logs in → sees triage queue → clicks finding → views AI analysis
- [ ] Analyst validates finding → sets verdict → adds remediation notes
- [ ] Report generated in PDF + DOCX → different analyst approves → customer can download
- [ ] AI analysis returns summarization + FP score + remediation in <15 seconds
- [ ] Real-time updates: new findings appear in triage queue without page refresh

### Phase 2 Architecture

```
Phase 1 services +

┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ Scan           │  │ Burp Suite     │  │ Tenable        │
│ Orchestration  │──│ Connector      │  │ Connector      │
│ (Temporal)     │  │ (gVisor pod)   │  │ (gVisor pod)   │
└───────┬────────┘  └────────────────┘  └────────────────┘
        │
        ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ Findings       │  │ AI Analyst     │  │ Reporting      │
│ Normalization  │  │ Assistant      │  │ Service        │
└────────────────┘  └────────────────┘  └────────────────┘
        │
        ▼
┌────────────────┐  ┌────────────────┐
│ Analyst Portal │  │ MinIO          │
│ (Next.js)      │  │ (Object Store) │
└────────────────┘  └────────────────┘
```

---

## Phase 3: Scale & Automate (Weeks 23–32)

**Goal:** Customer self-service portal, compliance mapping, advanced AI features, and production scaling for 100+ concurrent tenants.

### Sprint Breakdown

#### Sprint 12–14 (Weeks 23–28): Customer Portal & Compliance

| Task | Module | Deliverable |
|------|--------|-------------|
| Customer Portal SPA | Module 1 | Next.js app, customer auth realm |
| Engagement dashboard | Module 1 | Status tracking, SLA timers, progress bars |
| Credential submission UI | Module 1 | Encrypted upload, Vault Transit integration |
| Report download page | Module 1 | Pre-signed URLs, download history |
| Compliance Engine Service | Module 6 | Framework CRUD, control catalog |
| CWE → control auto-mapping | Module 6 | Mapping table, confidence scoring |
| Gap analysis API | Module 6 | Per-engagement compliance gap report |
| Compliance report section | Module 5 | Compliance mapping in generated reports |
| Evidence management | Module 6 | Upload, link to controls, version tracking |
| Fortify Connector | Module 3 | SAST/SCA scanning capability |

**Exit Criteria:**
- [ ] Customer logs in → views engagement status → downloads approved report
- [ ] Customer submits credentials → encrypted at rest in Vault → never exposed in UI
- [ ] Finding auto-mapped to PCI DSS + OWASP ASVS controls on ingestion
- [ ] Gap analysis shows passing/failing/not-tested controls per framework
- [ ] Compliance section appears in generated reports

#### Sprint 15–16 (Weeks 29–32): Scale & Harden

| Task | Module | Deliverable |
|------|--------|-------------|
| HPA tuning | Infra | Custom metrics: Kafka lag, queue depth, active scans |
| Load testing | All | k6 scripts: 100 concurrent engagements, 10K findings |
| PDB deployment | Infra | Pod disruption budgets for all critical services |
| Elasticsearch deployment | Infra | ECK cluster for audit logs and finding search |
| Advanced AI features | Module 4 | Risk prioritization with threat intel, batch analysis |
| Notification service | Cross-cut | Teams bot, email alerts, webhook integrations |
| Mobile Connector | Module 3 | MobSF integration for mobile app scanning |
| Kyverno policies | Infra | Enforce: non-root, resource limits, image registries |
| Falco deployment | Infra | Runtime security monitoring, anomaly detection |
| Disaster recovery | Infra | WAL-G backup verification, cross-region replication |

**Exit Criteria:**
- [ ] Platform handles 100 concurrent engagements with p99 latency < 500ms
- [ ] HPA scales scan workers 2→30 based on pending scan queue
- [ ] Zero-downtime deployment: PDBs maintain service availability during rolling updates
- [ ] DR: database recoverable to any point in last 30 days
- [ ] Falco alerts on suspicious container behavior (shell exec, network anomaly)

---

## Phase 4: Enterprise Features (Weeks 33–42)

**Goal:** Enterprise-ready with white-labeling, multi-region, marketplace, and advanced analytics. Platform supports 500+ customers.

### Sprint Breakdown

#### Sprint 17–19 (Weeks 33–38): Enterprise Capabilities

| Task | Module | Deliverable |
|------|--------|-------------|
| Custom compliance frameworks | Module 6 | Tenant-defined frameworks with custom controls |
| White-label branding | Module 1/5 | Per-tenant logos, colors, report templates, custom domains |
| Advanced reporting | Module 5 | Trend analysis, multi-engagement comparison, executive KPIs |
| Customer self-service scheduling | Module 1 | Recurring assessments, auto-engagement creation |
| Bulk operations | Module 2 | CSV import, bulk engagement create, batch asset registration |
| Collaboration features | Module 4 | Real-time co-editing (Yjs), @mentions, threaded comments |
| PoC builder | Module 4 | Step-by-step reproduction, export as Markdown/HTML |
| Compliance posture dashboard | Module 6 | Cross-engagement trend, improvement tracking |
| Custom scanner plugins | Module 3 | Plugin SDK, custom scanner registration |
| API key management | Cross-cut | Customer API keys for programmatic access |

#### Sprint 20–21 (Weeks 39–42): Multi-Region & Marketplace

| Task | Module | Deliverable |
|------|--------|-------------|
| Multi-region deployment | Infra | Active-passive across 2 regions, CockroachDB evaluation |
| Data residency controls | Cross-cut | Per-tenant region pinning (EU, US, APAC) |
| Scanner marketplace | Module 3 | Third-party scanner integrations, community connectors |
| Billing integration | Module 1 | Stripe/usage-based billing, plan management |
| SSO federation | Cross-cut | Customer Azure AD/Okta federation via SAML |
| Advanced analytics | All | Cross-tenant benchmarking (anonymized), industry comparison |
| Audit export | Cross-cut | SOC 2 audit export, hash chain verification UI |
| Performance optimization | All | Query optimization, caching strategy, CDN for static assets |
| Penetration testing | All | Third-party pentest of platform, fix findings |
| SOC 2 Type II preparation | All | Evidence collection, control documentation |

**Exit Criteria:**
- [ ] Platform supports 500+ tenants across 2 regions
- [ ] Per-tenant data residency enforced at database and object storage level
- [ ] White-labeled portal deployed for 3 pilot MSSP customers
- [ ] SOC 2 Type II audit initiated with evidence package

---

## Milestone Summary

| Milestone | Week | Deliverable | Business Value |
|-----------|------|-------------|----------------|
| **M1: Platform Live** | 4 | Infra + IAM + security controls deployed | Engineering team can develop on platform |
| **M2: Engagement MVP** | 10 | Engagement lifecycle, credential vault | Internal teams can create/manage engagements |
| **M3: First Scan** | 16 | Scan pipeline end-to-end | Automated DAST + infra scanning operational |
| **M4: Analyst Beta** | 22 | Workbench + reporting | Analysts can triage, validate, generate reports |
| **M5: Customer Portal** | 28 | Self-service portal + compliance | Customers can track engagements, download reports |
| **M6: Production Scale** | 32 | 100+ tenant capacity, monitoring | Production launch for initial customer cohort |
| **M7: Enterprise GA** | 38 | White-label, advanced features | Full enterprise feature set for MSSP operations |
| **M8: Multi-Region** | 42 | 500+ tenant capacity, data residency | Global availability, regulatory compliance |

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|------------|------------|
| Scanner API instability (Burp/Tenable) | Scans fail mid-execution | Medium | Circuit breaker, retry logic, fallback to queued retry |
| AI hallucination in reports | Incorrect vulnerability descriptions | Medium | AI outputs are drafts only, analyst review mandatory |
| Multi-tenant data leak | Catastrophic compliance breach | Low | RLS, middleware enforcement, integration tests per sprint |
| Vault unsealing after restart | Credential access blocked | Low | AWS KMS auto-unseal, HA Raft with 3 nodes |
| Kafka consumer lag spike | Findings delayed, SLA breach | Medium | HPA on consumer lag metric, dead-letter queue |
| gVisor compatibility issues | Scanner tools may not work in sandbox | Medium | Compatibility testing in Phase 2, fallback to seccomp profiles |

---

## Team Structure Recommendation

| Role | Count | Phase | Focus |
|------|-------|-------|-------|
| Platform Engineer | 2 | 1–4 | K8s, Terraform, CI/CD, monitoring |
| Backend Engineer (Go) | 2 | 1–4 | Engagement, Asset, Scan Orchestration services |
| Backend Engineer (Python) | 3 | 1–4 | AI, Reporting, Security, Findings, Compliance |
| Frontend Engineer | 2 | 2–4 | Analyst Workbench, Customer Portal |
| Security Engineer | 1 | 1–4 | RBAC, Vault, RLS, pen testing, compliance |
| QA / SDET | 1 | 2–4 | Integration tests, load testing, security testing |
| Product Manager | 1 | 1–4 | Requirements, customer feedback, roadmap |
| **Total** | **12** | | |

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind | SPA + SSR portals |
| Backend | Go 1.22 (Gin), Python 3.12 (FastAPI) | Microservices |
| Workflow | Temporal.io | Scan pipeline orchestration |
| AI | Claude API (Anthropic) | Vulnerability analysis assistant |
| Database | PostgreSQL 16 (CloudNativePG) | Primary data store |
| Cache | Redis 7 (Sentinel) | Session, caching, pub/sub |
| Queue | Apache Kafka (Strimzi) | Event backbone |
| Search | Elasticsearch 8 (ECK) | Audit logs, finding search |
| Object Store | MinIO | Reports, scan artifacts |
| Secrets | HashiCorp Vault | Credential management |
| Identity | Keycloak | OIDC/SAML, MFA, RBAC |
| Gateway | Kong | Rate limiting, JWT, routing |
| Orchestration | Kubernetes (EKS/AKS/GKE) | Container orchestration |
| Service Mesh | Istio | mTLS, circuit breakers |
| Monitoring | Prometheus, Grafana, Loki, Tempo | Observability |
| CI/CD | ArgoCD, GitHub Actions | GitOps deployment |
