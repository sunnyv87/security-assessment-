# AI-Driven VAPT Orchestration Platform — SaaS Architecture

## Production-Grade Design for MSSP Operations at Scale (500+ Customers)

---

## 1. System Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                    EXTERNAL BOUNDARY (WAF / CDN / DDoS Protection)             ║
║                                    Cloudflare / AWS Shield / Azure Front Door                   ║
╚══════════════════════╦═══════════════════════════════════════════════════════╦════════════════════╝
                       ║                                                     ║
                       ▼                                                     ▼
    ┌──────────────────────────────────┐                  ┌──────────────────────────────────────┐
    │      CUSTOMER PORTAL (SPA)       │                  │        ANALYST PORTAL (SPA)          │
    │  ─────────────────────────────   │                  │  ──────────────────────────────────  │
    │  React / Next.js                 │                  │  React / Next.js                    │
    │  • Engagement request forms      │                  │  • Analyst workbench                │
    │  • Dashboard & status tracking   │                  │  • Findings triage & validation     │
    │  • Report downloads              │                  │  • Manual testing workspace         │
    │  • Credential submission         │                  │  • Report authoring                 │
    │  • Compliance view               │                  │  • Collaboration tools              │
    │  • Billing & subscription mgmt   │                  │  • AI assistant interface           │
    └──────────────┬───────────────────┘                  └──────────────────┬───────────────────┘
                   │ HTTPS/TLS 1.3                                          │ HTTPS/TLS 1.3
                   │ + OAuth 2.0 / OIDC                                     │ + SAML 2.0 / OIDC
                   ▼                                                        ▼
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                              API GATEWAY / SERVICE MESH                                        ║
║                     Kong / AWS API Gateway + Istio Service Mesh                                 ║
║  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐   ║
║  │Rate Limiting│ │   mTLS       │ │  JWT Valid.  │ │  Audit Log   │ │  Tenant Routing      │   ║
║  └─────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────────┘   ║
╚══════════════════════════════════╦═══════════════════════════════════════════════════════════════╝
                                   ║
          ┌────────────────────────╬────────────────────────────────────────────┐
          ▼                        ▼                                           ▼
╔═══════════════════╗  ╔═══════════════════════════╗  ╔═════════════════════════════════════════╗
║  IDENTITY & ACCESS║  ║   CORE PLATFORM SERVICES  ║  ║     EVENT BUS / MESSAGE BACKBONE       ║
║  MANAGEMENT (IAM) ║  ║   (Kubernetes Cluster)    ║  ║     Apache Kafka / Amazon EventBridge  ║
║  ─────────────────║  ║   ───────────────────────  ║  ║  ┌─────────────────────────────────┐   ║
║  • Keycloak / Auth0  ║                            ║  ║  │ Topics:                         │   ║
║  • RBAC + ABAC    ║  ║  Microservices (next sect) ║  ║  │  • engagement.created           │   ║
║  • MFA enforcement║  ║                            ║  ║  │  • scan.requested               │   ║
║  • API key mgmt   ║  ║                            ║  ║  │  • scan.completed               │   ║
║  • Session mgmt   ║  ║                            ║  ║  │  • finding.normalized           │   ║
║  • Tenant isolation║  ║                            ║  ║  │  • finding.validated            │   ║
╚═══════════════════╝  ╚═══════════════════════════╝  ║  │  • report.generated             │   ║
                                                       ║  │  • notification.dispatch        │   ║
                                                       ║  └─────────────────────────────────┘   ║
                                                       ╚═══════════════════════════════════════╝
```

### Core Platform Services — Microservice Decomposition

```
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                           KUBERNETES CLUSTER (Multi-AZ)                                    ║
║                                                                                            ║
║  ┌─────────────────────────────────────────────────────────────────────────────────────┐    ║
║  │                        NAMESPACE: vapt-platform-services                            │    ║
║  │                                                                                     │    ║
║  │  ┌───────────────────┐  ┌────────────────────┐  ┌────────────────────────────────┐  │    ║
║  │  │ 1. ENGAGEMENT     │  │ 2. CREDENTIAL      │  │ 3. MCP ORCHESTRATION           │  │    ║
║  │  │    INTAKE SVC     │  │    VAULT SVC       │  │    LAYER                       │  │    ║
║  │  │ ───────────────── │  │ ────────────────── │  │ ────────────────────────────── │  │    ║
║  │  │ • Engagement CRUD │  │ • HashiCorp Vault  │  │ • Workflow engine (Temporal)   │  │    ║
║  │  │ • Scope definition│  │   integration      │  │ • Scan pipeline DAG builder    │  │    ║
║  │  │ • SLA tracking    │  │ • Secret rotation  │  │ • Tool selection AI agent      │  │    ║
║  │  │ • Asset inventory │  │ • Credential       │  │ • Parallel scan coordination   │  │    ║
║  │  │ • Customer onboard│  │   lifecycle mgmt   │  │ • Retry / circuit breaker      │  │    ║
║  │  │ • Approval flows  │  │ • Access audit log │  │ • Priority queue management    │  │    ║
║  │  │                   │  │ • Zero-knowledge   │  │ • Resource allocation          │  │    ║
║  │  │ [PostgreSQL]      │  │   architecture     │  │                                │  │    ║
║  │  └───────────────────┘  └────────────────────┘  │ [Redis + PostgreSQL]           │  │    ║
║  │                                                  └────────────────────────────────┘  │    ║
║  │  ┌───────────────────┐  ┌────────────────────┐  ┌────────────────────────────────┐  │    ║
║  │  │ 4. SCAN EXECUTION │  │ 5. FINDINGS        │  │ 6. AI VULNERABILITY            │  │    ║
║  │  │    LAYER          │  │    NORMALIZATION    │  │    ANALYSIS ENGINE             │  │    ║
║  │  │ ───────────────── │  │    ENGINE          │  │ ────────────────────────────── │  │    ║
║  │  │ • Scanner adapter │  │ ────────────────── │  │ • LLM-powered analysis         │  │    ║
║  │  │   framework       │  │ • Multi-format     │  │   (Claude API)                 │  │    ║
║  │  │ • Sandboxed exec  │  │   parser (SARIF,   │  │ • CVE correlation              │  │    ║
║  │  │   (gVisor/Kata)   │  │   XML, JSON)       │  │ • Exploitability scoring       │  │    ║
║  │  │ • Resource quotas  │  │ • Deduplication    │  │ • Attack chain modeling        │  │    ║
║  │  │ • Scan scheduling │  │   engine           │  │ • False positive detection     │  │    ║
║  │  │ • Health monitoring│  │ • Severity mapping │  │ • Remediation generation       │  │    ║
║  │  │ • Result streaming│  │   (CVSS 4.0)       │  │ • Business impact assessment   │  │    ║
║  │  │                   │  │ • Finding taxonomy  │  │ • Context-aware risk scoring   │  │    ║
║  │  │ [Object Storage]  │  │                    │  │                                │  │    ║
║  │  └───────────────────┘  │ [Elasticsearch]    │  │ [Vector DB + PostgreSQL]       │  │    ║
║  │                          └────────────────────┘  └────────────────────────────────┘  │    ║
║  │  ┌───────────────────┐  ┌────────────────────┐  ┌────────────────────────────────┐  │    ║
║  │  │ 7. ANALYST        │  │ 8. REPORT          │  │ 9. COMPLIANCE                  │  │    ║
║  │  │    WORKBENCH SVC  │  │    GENERATION      │  │    MAPPING ENGINE              │  │    ║
║  │  │ ───────────────── │  │    ENGINE          │  │ ────────────────────────────── │  │    ║
║  │  │ • Finding triage  │  │ ────────────────── │  │ • OWASP Top 10 mapping         │  │    ║
║  │  │   queue           │  │ • Template engine  │  │ • PCI DSS 4.0 controls         │  │    ║
║  │  │ • Manual test     │  │   (LaTeX + HTML)   │  │ • SOC 2 Type II                │  │    ║
║  │  │   tracking        │  │ • Executive summary│  │ • ISO 27001                    │  │    ║
║  │  │ • Evidence capture│  │   AI generation    │  │ • NIST CSF 2.0                 │  │    ║
║  │  │ • Collaboration   │  │ • Chart/graph      │  │ • HIPAA                        │  │    ║
║  │  │   (real-time)     │  │   rendering        │  │ • Custom framework support     │  │    ║
║  │  │ • Checklist mgmt  │  │ • PDF/DOCX export  │  │ • Gap analysis                 │  │    ║
║  │  │ • PoC builder     │  │ • Version control  │  │ • Audit trail                  │  │    ║
║  │  │                   │  │ • Digital signing   │  │                                │  │    ║
║  │  │ [PostgreSQL+Redis]│  │                    │  │ [PostgreSQL]                   │  │    ║
║  │  └───────────────────┘  │ [Object Storage]   │  └────────────────────────────────┘  │    ║
║  │                          └────────────────────┘                                     │    ║
║  │  ┌───────────────────┐  ┌────────────────────┐                                     │    ║
║  │  │10. COLLABORATION  │  │11. NOTIFICATION    │                                     │    ║
║  │  │    LAYER          │  │    SERVICE         │                                     │    ║
║  │  │ ───────────────── │  │ ────────────────── │                                     │    ║
║  │  │ • MS Teams bot    │  │ • Email (SES/SMTP) │                                     │    ║
║  │  │ • Real-time chat  │  │ • Webhook dispatch │                                     │    ║
║  │  │   (WebSocket)     │  │ • In-app notifs    │                                     │    ║
║  │  │ • @mentions       │  │ • Escalation rules │                                     │    ║
║  │  │ • Activity feeds  │  │ • Digest batching  │                                     │    ║
║  │  │ • Comments/threads│  │                    │                                     │    ║
║  │  │                   │  │ [Redis Pub/Sub]    │                                     │    ║
║  │  │ [Redis + PgSQL]   │  └────────────────────┘                                     │    ║
║  │  └───────────────────┘                                                              │    ║
║  └─────────────────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                            ║
║  ┌─────────────────────────────────────────────────────────────────────────────────────┐    ║
║  │                     NAMESPACE: vapt-scan-workers (ISOLATED)                         │    ║
║  │                                                                                     │    ║
║  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────────┐  │    ║
║  │  │  Burp Suite│ │  Tenable   │ │  Fortify   │ │   MobSF    │ │  Custom Scanner  │  │    ║
║  │  │  Adapter   │ │  Adapter   │ │  Adapter   │ │  Adapter   │ │  Adapters        │  │    ║
║  │  │ ────────── │ │ ────────── │ │ ────────── │ │ ────────── │ │ ──────────────── │  │    ║
║  │  │ Web App    │ │ Infra &    │ │ SAST / SCA │ │ Mobile App │ │ • Nuclei         │  │    ║
║  │  │ DAST scans │ │ Network    │ │ Source code│ │ Android/   │ │ • Nmap            │  │    ║
║  │  │ API testing│ │ vuln scans │ │ review     │ │ iOS testing│ │ • ScoutSuite      │  │    ║
║  │  │            │ │ Cloud sec  │ │ Dependency │ │            │ │ • Trivy           │  │    ║
║  │  │            │ │            │ │ analysis   │ │            │ │ • ZAP             │  │    ║
║  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └──────────────────┘  │    ║
║  │                                                                                     │    ║
║  │  Each adapter runs in sandboxed pods with:                                          │    ║
║  │  • Network policies (egress restricted to target scope only)                        │    ║
║  │  • Resource limits (CPU/memory quotas per scan)                                     │    ║
║  │  • Ephemeral storage (destroyed after scan completion)                              │    ║
║  │  • No inter-pod communication (strict isolation)                                    │    ║
║  └─────────────────────────────────────────────────────────────────────────────────────┘    ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝
```

### External Integrations

```
╔════════════════════════════════════════════════════════════════════════════════╗
║                        EXTERNAL INTEGRATIONS                                 ║
║                                                                              ║
║  ┌──────────────────────────┐      ┌──────────────────────────────────────┐  ║
║  │  TICKETING / ITSM        │      │  COLLABORATION                      │  ║
║  │  ────────────────────    │      │  ──────────────────────────────────  │  ║
║  │  • Jira Cloud (REST API) │◄────►│  • Microsoft Teams (Bot Framework   │  ║
║  │    - Auto-create issues  │      │    + Graph API)                      │  ║
║  │    - Bidirectional sync  │      │    - Channel notifications           │  ║
║  │    - Custom field mapping│      │    - Adaptive cards for findings     │  ║
║  │                          │      │    - Approval workflows              │  ║
║  │  • ServiceNow (REST API) │      │    - Status commands                 │  ║
║  │    - CMDB integration    │      │                                      │  ║
║  │    - Incident creation   │      │  • Slack (optional)                  │  ║
║  │    - Change requests     │      │    - Webhook notifications           │  ║
║  └──────────────────────────┘      └──────────────────────────────────────┘  ║
║                                                                              ║
║  ┌──────────────────────────┐      ┌──────────────────────────────────────┐  ║
║  │  SCANNER APIs             │      │  CLOUD PROVIDERS                    │  ║
║  │  ────────────────────    │      │  ──────────────────────────────────  │  ║
║  │  • Burp Suite Enterprise │      │  • AWS (SecurityHub, Inspector,     │  ║
║  │    REST API              │      │    GuardDuty, Config)               │  ║
║  │  • Tenable.io REST API   │      │  • Azure (Defender, Sentinel,       │  ║
║  │  • Fortify SSC REST API  │      │    Policy)                          │  ║
║  │  • MobSF REST API        │      │  • GCP (Security Command Center,    │  ║
║  │                          │      │    Cloud Armor)                      │  ║
║  └──────────────────────────┘      └──────────────────────────────────────┘  ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

### Data Layer

```
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║                                  DATA LAYER                                            ║
║                                                                                        ║
║  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐  ║
║  │  PostgreSQL 16    │  │  Elasticsearch   │  │  Redis Cluster   │  │  Object Store  │  ║
║  │  (Multi-tenant)   │  │  (Findings Index)│  │  (Cache/Queue)   │  │  (S3-compat.)  │  ║
║  │ ──────────────── │  │ ──────────────── │  │ ──────────────── │  │ ────────────── │  ║
║  │ • Row-level sec.  │  │ • Full-text      │  │ • Session store  │  │ • Scan results │  ║
║  │ • Tenant isolation│  │   search on      │  │ • Rate limiting  │  │ • Reports      │  ║
║  │   via RLS         │  │   findings       │  │ • Pub/Sub for    │  │ • Evidence     │  ║
║  │ • Engagement data │  │ • Aggregation    │  │   real-time      │  │ • APK/IPA      │  ║
║  │ • User data       │  │   dashboards     │  │ • Scan job queue │  │ • Source code   │  ║
║  │ • Compliance data │  │ • Tenant-scoped  │  │ • Temporal state │  │   snapshots    │  ║
║  │ • Audit trails    │  │   indices        │  │                  │  │ • AES-256-GCM  │  ║
║  │ • Encrypted at    │  │ • ILM policies   │  │                  │  │   encrypted    │  ║
║  │   rest (AES-256)  │  │                  │  │                  │  │                │  ║
║  └──────────────────┘  └──────────────────┘  └──────────────────┘  └────────────────┘  ║
║                                                                                        ║
║  ┌──────────────────┐  ┌──────────────────┐                                            ║
║  │  HashiCorp Vault  │  │  Vector DB       │                                            ║
║  │  (Secrets)        │  │  (Pgvector/      │                                            ║
║  │ ──────────────── │  │   Pinecone)      │                                            ║
║  │ • Customer creds  │  │ ──────────────── │                                            ║
║  │ • API keys        │  │ • Finding        │                                            ║
║  │ • Scanner tokens  │  │   embeddings     │                                            ║
║  │ • TLS certs       │  │ • Similarity     │                                            ║
║  │ • Encryption keys │  │   search for     │                                            ║
║  │ • Auto-rotation   │  │   deduplication  │                                            ║
║  │ • Audit logging   │  │ • Historical     │                                            ║
║  │ • Seal/Unseal     │  │   pattern match  │                                            ║
║  └──────────────────┘  └──────────────────┘                                            ║
╚══════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. Component Responsibilities

### 2.1 Customer Portal

| Aspect | Detail |
|--------|--------|
| **Purpose** | Self-service interface for MSSP customers to submit engagements, track progress, and retrieve reports |
| **Technology** | Next.js (React) SPA with server-side rendering |
| **Key Functions** | Engagement submission wizard, real-time status dashboard, report download center, credential submission (encrypted client-side before transit), billing and subscription management, asset inventory management |
| **Multi-tenancy** | Tenant-scoped JWT tokens; every API call passes through tenant context middleware; UI components dynamically render per-tenant branding |
| **Auth** | OAuth 2.0 / OIDC via Keycloak; supports customer SSO federation (SAML 2.0, OIDC) |

### 2.2 Engagement Intake System

| Aspect | Detail |
|--------|--------|
| **Purpose** | Structured capture of engagement scope, rules of engagement, target assets, and scheduling |
| **Technology** | Go microservice; PostgreSQL for persistence; Kafka for event publishing |
| **Key Functions** | Multi-step engagement wizard (scope type selection, target enumeration, schedule configuration, credential linking, compliance framework selection), SLA timer initialization, automatic engagement ID generation, approval workflow (customer → MSSP manager → analyst assignment) |
| **Outputs** | `engagement.created` event on Kafka → triggers MCP orchestration |
| **Data Model** | Engagement → has_many Targets → has_many Scans → has_many Findings |

### 2.3 Credential Vault

| Aspect | Detail |
|--------|--------|
| **Purpose** | Secure storage and lifecycle management of customer-supplied credentials needed for authenticated testing |
| **Technology** | Thin Go service wrapping HashiCorp Vault (Enterprise) with Transit secrets engine |
| **Key Functions** | Client-side encryption before submission (libsodium in browser), Vault transit encryption at rest, time-boxed credential access (auto-expiry tied to engagement window), credential checkout/checkin with audit trail, zero-knowledge architecture (platform operators cannot access plaintext credentials), automatic rotation reminders post-engagement |
| **Access Pattern** | Only scan worker pods can request credential checkout; requires valid engagement ID + scan job ID + mTLS certificate |

### 2.4 MCP Orchestration Layer

| Aspect | Detail |
|--------|--------|
| **Purpose** | Central workflow engine that translates engagement scope into executable scan pipelines |
| **Technology** | Temporal.io workflow engine; Python orchestration logic; Redis for state caching |
| **Key Functions** | **Scan Plan Generation**: AI agent (Claude API) analyzes engagement scope and recommends optimal tool chain and scan sequence. **DAG Construction**: Builds a directed acyclic graph of scan tasks with dependencies (e.g., Nmap discovery → Tenable vuln scan → Burp authenticated scan). **Resource Allocation**: Assigns scan workers based on current cluster capacity and scan priority. **Retry & Circuit Breaker**: Automatic retry with exponential backoff; circuit breaker for unresponsive scanner APIs. **Progress Tracking**: Real-time scan pipeline progress streamed to customer and analyst portals via WebSocket |
| **Workflow Example** | Web App VAPT: `[Asset Discovery] → [Port Scan] → [Web Crawl] → [DAST Scan (Burp)] → [SAST (Fortify)] → [SCA (Fortify)] → [Normalize] → [AI Analysis] → [Analyst Review Queue]` |

### 2.5 Scan Execution Layer

| Aspect | Detail |
|--------|--------|
| **Purpose** | Isolated, sandboxed execution environment for all automated scanning tools |
| **Technology** | Kubernetes Jobs with gVisor/Kata Containers runtime; dedicated node pools |
| **Architecture** | **Scanner Adapter Pattern**: Each tool has a standardized adapter (Go/Python) implementing a common interface: `Configure()`, `Execute()`, `StreamResults()`, `Cleanup()`. This decouples the orchestration layer from tool-specific APIs. |
| **Supported Scanners** | |

| Scanner | Scope | Adapter Details |
|---------|-------|-----------------|
| **Burp Suite Enterprise** | Web App DAST, API Testing | REST API integration; scan configuration via YAML; result export in XML/JSON |
| **Tenable.io** | Infrastructure, Network, Cloud | REST API v3; agent-based and agentless scanning; compliance auditing |
| **Fortify (SSC + SCA)** | SAST, SCA | SSC REST API; CloudScan for distributed analysis; source code upload via API |
| **MobSF** | Mobile App (Android/iOS) | REST API; APK/IPA upload; static + dynamic analysis; API hooking |
| **Nuclei** | Web, Network, Cloud | Template-based scanning; custom template library; YAML config |
| **Nmap** | Network Discovery | XML output parsing; service/version detection; script scanning |
| **ScoutSuite** | Cloud Security (AWS/Azure/GCP) | Multi-cloud config review; JSON rule output |
| **Trivy** | Container/IaC Scanning | Image scanning; Kubernetes manifest analysis; SBOM generation |

| Aspect | Detail |
|--------|--------|
| **Isolation** | Each scan job runs in an isolated pod with: network policies restricting egress to target scope only, CPU/memory resource quotas, ephemeral storage (destroyed on completion), no inter-pod communication, seccomp profiles |
| **Outputs** | Raw scan results pushed to Object Storage (S3); `scan.completed` event published to Kafka |

### 2.6 Findings Normalization Engine

| Aspect | Detail |
|--------|--------|
| **Purpose** | Ingest heterogeneous scan outputs and produce a unified, deduplicated finding schema |
| **Technology** | Python microservice; Elasticsearch for indexing; pgvector for embedding-based deduplication |
| **Key Functions** | **Multi-format Parsing**: SARIF, Burp XML, Tenable JSON, Fortify FPR, MobSF JSON, Nuclei JSON, Nmap XML. **Unified Schema**: Every finding mapped to a canonical structure (see below). **Deduplication**: Vector embedding similarity (cosine similarity > 0.92 threshold) + deterministic hash matching on (CWE + location + parameter). **Severity Mapping**: All findings scored using CVSS 4.0; EPSS scores fetched from FIRST.org API. **Taxonomy**: Mapped to CWE, CAPEC, ATT&CK where applicable. |

**Canonical Finding Schema:**
```json
{
  "finding_id": "uuid-v7",
  "engagement_id": "uuid-v7",
  "tenant_id": "uuid-v7",
  "source_scanner": "burp_suite",
  "title": "SQL Injection in Login Form",
  "description": "...",
  "location": {
    "type": "url",
    "value": "https://target.com/api/login",
    "parameter": "username",
    "method": "POST"
  },
  "severity": {
    "cvss_v4_score": 9.1,
    "cvss_v4_vector": "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:N/SC:N/SI:N/SA:N",
    "epss_score": 0.87,
    "qualitative": "critical"
  },
  "classification": {
    "cwe_id": "CWE-89",
    "capec_id": "CAPEC-66",
    "owasp_category": "A03:2021-Injection",
    "mitre_attack": "T1190"
  },
  "evidence": {
    "request": "...",
    "response": "...",
    "screenshot_ref": "s3://evidence/...",
    "proof_of_concept": "..."
  },
  "ai_analysis": {
    "exploitability_assessment": "...",
    "business_impact": "...",
    "remediation_guidance": "...",
    "false_positive_confidence": 0.05,
    "attack_chain_context": "..."
  },
  "status": "confirmed",
  "analyst_notes": "...",
  "compliance_mappings": [...],
  "created_at": "2026-03-12T...",
  "updated_at": "2026-03-12T..."
}
```

### 2.7 Analyst Workbench

| Aspect | Detail |
|--------|--------|
| **Purpose** | Primary workspace for security analysts to triage automated findings, conduct manual testing, and validate results |
| **Technology** | React SPA with real-time collaboration (CRDT-based via Yjs); Go backend service |
| **Key Functions** | **Triage Queue**: AI-prioritized finding queue with bulk actions (confirm, false positive, needs investigation). **Manual Testing Workspace**: Checklist-driven manual testing (OWASP WSTG, MASTG, ASVS); evidence capture with screenshot annotation; PoC builder with request/response replay. **AI Assistant**: Claude-powered assistant that answers analyst questions about findings, suggests exploitation vectors, and drafts remediation text. **Real-time Collaboration**: Multiple analysts can work on the same engagement simultaneously with conflict-free editing. **Review Workflow**: Senior analyst review gate before findings are finalized. |
| **Outputs** | Validated findings → `finding.validated` Kafka event → triggers report generation |

### 2.8 AI Vulnerability Analysis Engine

| Aspect | Detail |
|--------|--------|
| **Purpose** | LLM-powered analysis layer that enriches raw findings with contextual intelligence |
| **Technology** | Python service; Claude API (claude-opus-4-6); pgvector for RAG; Redis for caching |
| **Key Functions** | **Exploitability Assessment**: Analyzes each finding against known exploitation techniques and environmental factors to produce a realistic exploitability rating. **Attack Chain Modeling**: Identifies how individual findings can be chained together for greater impact (e.g., IDOR + privilege escalation = full account takeover). **False Positive Detection**: Uses historical finding data and contextual clues to flag likely false positives (target: <5% FP rate in confirmed findings). **Remediation Generation**: Produces specific, actionable remediation guidance tailored to the detected technology stack. **Executive Summary Generation**: Synthesizes all findings into a business-language risk narrative. **Business Impact Assessment**: Maps technical findings to business risk categories (data breach, service disruption, regulatory non-compliance). |
| **RAG Pipeline** | Finding embeddings stored in pgvector; similarity search against historical findings database to leverage past analyst decisions for improved accuracy |
| **Guardrails** | All AI outputs marked as "AI-generated, pending analyst review"; confidence scores attached to every AI judgment; analyst override always takes precedence |

### 2.9 Report Generation Engine

| Aspect | Detail |
|--------|--------|
| **Purpose** | Automated generation of professional VAPT reports in multiple formats |
| **Technology** | Python service; LaTeX for PDF rendering; Jinja2 for HTML templates; Puppeteer for chart rendering |
| **Report Types** | **Executive Report**: High-level risk overview, trend analysis, strategic recommendations (2-5 pages). **Technical Report**: Detailed findings with evidence, reproduction steps, remediation guidance (full detail). **Compliance Report**: Findings mapped to selected compliance frameworks with gap analysis. **Retest Report**: Comparison of current vs. previous engagement showing remediation progress. **Attestation Letter**: Formal letter suitable for third-party sharing. |
| **Features** | Customer-branded templates (logo, colors, fonts), digital signature (X.509), version control on all generated reports, diff view between report versions, scheduled auto-generation on engagement completion |
| **Output Formats** | PDF, DOCX, HTML, JSON (machine-readable) |

### 2.10 Compliance Mapping Engine

| Aspect | Detail |
|--------|--------|
| **Purpose** | Automated mapping of findings to regulatory and industry compliance frameworks |
| **Technology** | Go microservice; PostgreSQL for framework definitions; rule engine for mapping logic |
| **Supported Frameworks** | OWASP Top 10 (2021), OWASP ASVS 4.0, OWASP MASTG, PCI DSS 4.0, SOC 2 Type II, ISO 27001:2022, NIST CSF 2.0, NIST SP 800-53 Rev 5, HIPAA Security Rule, GDPR (Article 32), CIS Benchmarks, Custom frameworks (configurable per tenant) |
| **Key Functions** | Automatic CWE → control mapping, gap analysis (tested controls vs. framework requirements), compliance posture scoring, trend tracking across engagements, export compliance evidence packages |

### 2.11 Teams Collaboration Layer

| Aspect | Detail |
|--------|--------|
| **Purpose** | Bridge between the platform and customer/analyst collaboration tools |
| **Technology** | Node.js service; Microsoft Bot Framework SDK; WebSocket server |
| **MS Teams Integration** | Adaptive cards for finding notifications (with approve/acknowledge actions), channel-per-engagement auto-provisioning, slash commands for status queries (`/vapt status ENG-12345`), scheduled summary digests, approval workflow cards (engagement scope sign-off) |
| **Platform Collaboration** | Real-time activity feeds, @mention notifications, threaded comments on findings, analyst-to-customer secure messaging, engagement status change broadcasts |

---

## 3. Data Flow

### 3.1 End-to-End Engagement Flow

```
 Customer                Platform                        Scanners            Analyst
 ───────                ────────                        ────────            ───────
    │                      │                               │                  │
    │  1. Submit           │                               │                  │
    │  engagement ────────►│                               │                  │
    │  (scope, targets,    │  2. Validate &                │                  │
    │   credentials)       │     create engagement         │                  │
    │                      │     ──────────────►           │                  │
    │                      │     Store creds in Vault      │                  │
    │                      │                               │                  │
    │                      │  3. MCP Orchestrator           │                  │
    │                      │     builds scan pipeline      │                  │
    │                      │     (AI-assisted tool          │                  │
    │                      │      selection)               │                  │
    │                      │          │                     │                  │
    │                      │          │  4. Dispatch        │                  │
    │                      │          │     scan jobs ─────►│                  │
    │                      │          │     (parallel       │                  │
    │                      │          │      execution)     │                  │
    │                      │          │                     │                  │
    │                      │          │  5. Stream results ◄┤                  │
    │                      │          │     (raw findings)  │                  │
    │                      │          │                     │                  │
    │                      │  6. Normalize & deduplicate    │                  │
    │                      │     findings                  │                  │
    │                      │          │                     │                  │
    │                      │  7. AI analysis               │                  │
    │                      │     (exploitability,           │                  │
    │                      │      attack chains,           │                  │
    │                      │      remediation)             │                  │
    │                      │          │                     │                  │
    │                      │  8. Queue for ───────────────────────────────────►│
    │                      │     analyst review            │                  │
    │                      │                               │                  │  9. Triage,
    │                      │                               │                  │     validate,
    │                      │                               │                  │     manual test
    │                      │                               │                  │     │
    │                      │  10. Generate report ◄────────────────────────────┤
    │                      │      (AI + analyst input)     │                  │
    │                      │          │                     │                  │
    │  11. Report          │          │                     │                  │
    │  delivered ◄─────────┤          │                     │                  │
    │  (portal + email     │          │                     │                  │
    │   + Teams)           │          │                     │                  │
    │                      │                               │                  │
    │                      │  12. Sync to Jira /           │                  │
    │                      │      ServiceNow              │                  │
    │                      │      (per finding)            │                  │
    │                      │                               │                  │
```

### 3.2 Kafka Event Flow

```
engagement.created ─────► MCP Orchestrator ─────► scan.requested
                                                        │
                                                        ▼
                                                  Scan Workers
                                                        │
                                                  scan.completed
                                                        │
                                                        ▼
                                              Normalization Engine
                                                        │
                                              finding.normalized
                                                        │
                                                        ▼
                                              AI Analysis Engine
                                                        │
                                              finding.analyzed
                                                        │
                                                        ▼
                                              Analyst Workbench
                                                        │
                                              finding.validated
                                                        │
                                      ┌─────────────────┼─────────────────┐
                                      ▼                 ▼                 ▼
                              Report Engine     Compliance Engine   Integration Sync
                                      │                 │                 │
                              report.generated  compliance.mapped  ticket.created
                                      │
                                      ▼
                              Notification Svc
                                      │
                              notification.dispatch
```

### 3.3 Data Classification

| Classification | Examples | Storage | Encryption | Retention |
|---------------|----------|---------|------------|-----------|
| **Critical** | Customer credentials, API keys, encryption keys | HashiCorp Vault only | Vault transit + Vault seal | Engagement duration + 24h |
| **Confidential** | Findings, evidence, PoC data, reports, source code | PostgreSQL + S3 (tenant-isolated) | AES-256-GCM at rest; TLS 1.3 in transit | Per customer contract (default: 1 year) |
| **Internal** | Engagement metadata, scan configs, analyst notes | PostgreSQL | AES-256 at rest; TLS 1.3 in transit | 3 years |
| **Audit** | Access logs, credential checkout logs, API audit | Immutable append-only log (S3 + Elasticsearch) | AES-256 at rest | 7 years |

---

## 4. Security Boundaries

### 4.1 Trust Zones

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║  ZONE 0: UNTRUSTED (Internet)                                                  ║
║  ┌────────────────────────────────────────────────────────────────────────────┐ ║
║  │  Customer browsers, external API consumers                                │ ║
║  └────────────────────────┬───────────────────────────────────────────────────┘ ║
║                           │ WAF + DDoS protection + TLS termination            ║
║                           ▼                                                    ║
║  ZONE 1: DMZ (API Gateway)                                                     ║
║  ┌────────────────────────────────────────────────────────────────────────────┐ ║
║  │  API Gateway: rate limiting, JWT validation, request sanitization,         │ ║
║  │  tenant routing, audit logging                                            │ ║
║  └────────────────────────┬───────────────────────────────────────────────────┘ ║
║                           │ mTLS + service mesh (Istio)                        ║
║                           ▼                                                    ║
║  ZONE 2: APPLICATION (Platform Services)                                       ║
║  ┌────────────────────────────────────────────────────────────────────────────┐ ║
║  │  Core microservices: engagement, workbench, reporting, AI, compliance      │ ║
║  │  • All inter-service communication via mTLS (Istio sidecar)               │ ║
║  │  • Service-to-service auth via SPIFFE/SPIRE                               │ ║
║  │  • Network policies: explicit allow-list between services                  │ ║
║  └────────────────────────┬───────────────────────────────────────────────────┘ ║
║                           │ mTLS + credential checkout                         ║
║                           ▼                                                    ║
║  ZONE 3: SCAN EXECUTION (Isolated Worker Pool)                                 ║
║  ┌────────────────────────────────────────────────────────────────────────────┐ ║
║  │  Scanner pods: sandboxed (gVisor), ephemeral, network-restricted           │ ║
║  │  • Egress: ONLY to approved scan targets (per-engagement network policy)  │ ║
║  │  • No ingress from other pods                                              │ ║
║  │  • No access to platform data stores (results pushed via API only)        │ ║
║  │  • Credential access: time-boxed checkout from Vault                      │ ║
║  └────────────────────────────────────────────────────────────────────────────┘ ║
║                                                                                ║
║  ZONE 4: DATA (Persistence Layer)                                              ║
║  ┌────────────────────────────────────────────────────────────────────────────┐ ║
║  │  Databases, object storage, message queues                                 │ ║
║  │  • Accessible only from Zone 2 services                                   │ ║
║  │  • Encryption at rest (AES-256-GCM, cloud KMS managed)                    │ ║
║  │  • Row-level security for tenant isolation (PostgreSQL RLS)               │ ║
║  │  • No direct internet access                                              │ ║
║  └────────────────────────────────────────────────────────────────────────────┘ ║
║                                                                                ║
║  ZONE 5: SECRETS (Vault Cluster)                                               ║
║  ┌────────────────────────────────────────────────────────────────────────────┐ ║
║  │  HashiCorp Vault (HA cluster)                                              │ ║
║  │  • Dedicated, hardened infrastructure                                      │ ║
║  │  • Shamir seal with MFA-protected unseal keys                             │ ║
║  │  • Access only via authenticated Vault agent sidecars                     │ ║
║  │  • Full audit logging to immutable store                                  │ ║
║  └────────────────────────────────────────────────────────────────────────────┘ ║
║                                                                                ║
╚══════════════════════════════════════════════════════════════════════════════════╝
```

### 4.2 Tenant Isolation Model

```
                    ┌───────────────────────────────────────────────┐
                    │            TENANT ISOLATION LAYERS            │
                    │                                               │
                    │  Layer 1: API Gateway                         │
                    │  ├─ Tenant ID extracted from JWT              │
                    │  ├─ Request tagged with tenant context        │
                    │  └─ Rate limits applied per-tenant            │
                    │                                               │
                    │  Layer 2: Service Mesh                        │
                    │  ├─ Tenant context propagated via headers     │
                    │  ├─ All services enforce tenant context       │
                    │  └─ Cross-tenant requests rejected            │
                    │                                               │
                    │  Layer 3: Application                         │
                    │  ├─ Tenant middleware on every service        │
                    │  ├─ Repository pattern with tenant filter     │
                    │  └─ All queries scoped to tenant_id           │
                    │                                               │
                    │  Layer 4: Database                            │
                    │  ├─ PostgreSQL Row-Level Security (RLS)       │
                    │  ├─ Connection role set to tenant context     │
                    │  ├─ RLS policy: tenant_id = current_tenant()  │
                    │  └─ Elasticsearch: tenant-prefixed indices    │
                    │                                               │
                    │  Layer 5: Object Storage                      │
                    │  ├─ Bucket-per-tenant or prefix-per-tenant    │
                    │  ├─ IAM policies enforce tenant boundary      │
                    │  └─ Presigned URLs scoped to tenant prefix    │
                    │                                               │
                    │  Layer 6: Encryption                          │
                    │  ├─ Per-tenant encryption keys (KMS)          │
                    │  ├─ Key rotation on configurable schedule     │
                    │  └─ Tenant key deletion on offboarding        │
                    │                                               │
                    └───────────────────────────────────────────────┘
```

### 4.3 Security Controls Summary

| Control | Implementation |
|---------|---------------|
| **Authentication** | OIDC/SAML 2.0 via Keycloak; MFA enforced for all users; API keys with scoped permissions |
| **Authorization** | RBAC + ABAC; roles: Customer Admin, Customer Viewer, MSSP Admin, Analyst, Senior Analyst, Platform Admin |
| **Network Security** | WAF (OWASP CRS), DDoS protection, mTLS everywhere, Kubernetes Network Policies, scanner egress restricted to engagement targets |
| **Data Protection** | AES-256-GCM at rest, TLS 1.3 in transit, per-tenant encryption keys, field-level encryption for PII |
| **Secrets Management** | HashiCorp Vault with transit engine, auto-rotation, time-boxed access, audit logging |
| **Audit & Compliance** | Immutable audit logs, SIEM integration, SOC 2 Type II compliant operations, data residency controls |
| **Vulnerability Management** | Platform self-scanning via Trivy/Snyk, dependency updates via Dependabot/Renovate, container image signing (Sigstore) |
| **Incident Response** | Automated alerting on anomalous access patterns, credential leak detection, breach notification workflow |

---

## 5. Scalability Considerations

### 5.1 Capacity Model (500+ Customers)

```
┌────────────────────────────────────────────────────────────────────────────┐
│                     CAPACITY PLANNING (500+ Customers)                    │
│                                                                          │
│  Assumptions:                                                            │
│  • 500 active customers                                                  │
│  • Avg 4 engagements/customer/year = 2,000 engagements/year             │
│  • Peak: 40 concurrent engagements                                      │
│  • Avg 5 scan jobs per engagement = 200 concurrent scan pods (peak)     │
│  • Avg 150 findings per engagement = 300,000 findings/year              │
│  • 50 analysts on platform                                              │
│                                                                          │
│  Compute:                                                                │
│  ┌──────────────────────┬───────────────────────────────────────┐        │
│  │ Component            │ Sizing                                │        │
│  ├──────────────────────┼───────────────────────────────────────┤        │
│  │ Platform services    │ 3-5 replicas per service (HPA)       │        │
│  │                      │ 12 services × 4 avg = 48 pods        │        │
│  │ Scan workers         │ 0-200 pods (burst, KEDA autoscaler)  │        │
│  │ Kafka                │ 6-node cluster (3 brokers, 3 ZK)     │        │
│  │ PostgreSQL           │ db.r6g.2xlarge (HA, read replicas)   │        │
│  │ Elasticsearch        │ 6-node cluster (3 data, 3 master)    │        │
│  │ Redis                │ 6-node cluster (3 primary, 3 replica)│        │
│  │ Vault                │ 3-node HA cluster                    │        │
│  │ Kubernetes           │ 20-30 nodes (mixed instance types)   │        │
│  └──────────────────────┴───────────────────────────────────────┘        │
│                                                                          │
│  Storage (Annual):                                                       │
│  • Scan results: ~2 TB/year                                              │
│  • Reports: ~100 GB/year                                                 │
│  • Elasticsearch indices: ~500 GB/year (with ILM)                       │
│  • PostgreSQL: ~200 GB/year                                              │
│  • Audit logs: ~300 GB/year                                              │
│                                                                          │
└────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Horizontal Scaling Strategy

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                        SCALING ARCHITECTURE                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  TIER 1: STATELESS SERVICES (Easy horizontal scaling)                   │ │
│  │                                                                         │ │
│  │  All platform microservices are stateless:                              │ │
│  │  • HPA (Horizontal Pod Autoscaler) on CPU/memory + custom metrics      │ │
│  │  • Scale from 3 → 20 replicas based on request rate                    │ │
│  │  • Rolling deployments with zero downtime                              │ │
│  │  • Pod Disruption Budgets ensure availability during scaling           │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  TIER 2: SCAN WORKERS (Burst scaling with KEDA)                        │ │
│  │                                                                         │ │
│  │  • KEDA (Kubernetes Event-Driven Autoscaling) scales workers           │ │
│  │    based on Kafka consumer lag (pending scan jobs)                      │ │
│  │  • Scale-to-zero when no scans queued (cost optimization)              │ │
│  │  • Cluster Autoscaler provisions new nodes for burst capacity          │ │
│  │  • Spot/Preemptible instances for scan workers (70% cost reduction)    │ │
│  │  • Priority classes ensure critical scans get resources first          │ │
│  │  • Node affinity: scan workers on dedicated node pools                 │ │
│  │    (prevents noisy-neighbor on platform services)                      │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  TIER 3: DATA LAYER (Vertical + read replicas)                         │ │
│  │                                                                         │ │
│  │  PostgreSQL:                                                            │ │
│  │  • Primary + 2 read replicas (CQRS: writes → primary, reads → replica)│ │
│  │  • Connection pooling via PgBouncer (6,000 effective connections)      │ │
│  │  • Table partitioning by tenant_id + created_at                       │ │
│  │  • Automated vacuuming and index maintenance                          │ │
│  │                                                                         │ │
│  │  Elasticsearch:                                                         │ │
│  │  • Tenant-based index routing (shard-per-tenant for large tenants)    │ │
│  │  • ILM: hot → warm → cold → delete lifecycle                          │ │
│  │  • Cross-cluster replication for DR                                    │ │
│  │                                                                         │ │
│  │  Kafka:                                                                 │ │
│  │  • Topic partitioning by tenant_id (ordered processing per tenant)    │ │
│  │  • Consumer groups per service (independent scaling)                   │ │
│  │  • Log compaction for state topics                                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  TIER 4: AI INFERENCE (Queue-based with backpressure)                   │ │
│  │                                                                         │ │
│  │  • AI analysis requests queued in Kafka (finding.normalized topic)     │ │
│  │  • Worker pool processes findings in batches                           │ │
│  │  • Rate limiting per Claude API tier                                    │ │
│  │  • Caching: identical finding patterns use cached analysis             │ │
│  │  • Fallback: degrade gracefully if AI service unavailable             │ │
│  │    (findings proceed to analyst queue without AI enrichment)           │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Multi-Region & Disaster Recovery

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-REGION DEPLOYMENT                                    │
│                                                                              │
│   Region A (Primary)              Region B (DR / Geo)                       │
│   ┌─────────────────────┐         ┌─────────────────────┐                   │
│   │  Full platform      │ ──────► │  Full platform      │                   │
│   │  deployment         │  async  │  deployment         │                   │
│   │                     │  repl.  │  (warm standby)     │                   │
│   │  • All services     │         │  • All services     │                   │
│   │  • Primary DB       │         │  • DB replica       │                   │
│   │  • Vault cluster    │         │  • Vault cluster    │                   │
│   │  • Scan workers     │         │  • Scan workers     │                   │
│   └─────────────────────┘         └─────────────────────┘                   │
│                                                                              │
│   RPO: < 1 minute (async replication)                                       │
│   RTO: < 15 minutes (automated failover via Route 53 health checks)        │
│                                                                              │
│   Data Residency:                                                            │
│   • Tenant data pinned to region based on contract                          │
│   • Metadata replicated globally; findings/reports stay in-region           │
│   • EU tenants: data never leaves EU region                                 │
│                                                                              │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 5.4 Performance Targets

| Metric | Target | Mechanism |
|--------|--------|-----------|
| API response time (p99) | < 200ms | Caching, connection pooling, read replicas |
| Scan pipeline startup | < 30 seconds | Pre-warmed worker pools, Vault agent caching |
| Finding normalization throughput | 1,000 findings/minute | Kafka consumer parallelism, batch processing |
| AI analysis per finding | < 15 seconds | Batch API calls, prompt caching, result caching |
| Report generation | < 2 minutes | Pre-compiled LaTeX templates, async generation |
| Portal page load | < 1.5 seconds | CDN, SSR, code splitting, API response caching |
| System availability | 99.9% (8.7h downtime/year) | Multi-AZ, automated failover, self-healing pods |
| Concurrent scan capacity | 200 parallel scans | KEDA autoscaling, spot instances, resource quotas |

---

## 6. Technology Stack Summary

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **Frontend** | Next.js (React), TypeScript | SSR for performance, strong type safety, mature ecosystem |
| **API Gateway** | Kong / AWS API Gateway | Rate limiting, auth, tenant routing, plugin ecosystem |
| **Service Mesh** | Istio | mTLS, traffic management, observability |
| **Backend Services** | Go (performance-critical), Python (AI/ML, scanner adapters) | Go for low-latency services; Python for AI integration and rapid adapter development |
| **Workflow Engine** | Temporal.io | Durable execution, visibility, retry policies, versioning |
| **Message Broker** | Apache Kafka | Event streaming, ordering guarantees, consumer groups |
| **Primary Database** | PostgreSQL 16 | RLS for tenant isolation, JSONB for flexible schemas, mature tooling |
| **Search/Analytics** | Elasticsearch 8 | Full-text search on findings, aggregation dashboards |
| **Cache/Realtime** | Redis 7 Cluster | Session store, rate limiting, pub/sub for real-time features |
| **Object Storage** | S3-compatible (AWS S3 / MinIO) | Scan results, reports, evidence, source code |
| **Secrets** | HashiCorp Vault Enterprise | Transit encryption, dynamic secrets, audit logging |
| **Vector DB** | pgvector (PostgreSQL extension) | Finding embeddings for deduplication and similarity search |
| **AI/LLM** | Claude API (claude-opus-4-6) | Vulnerability analysis, remediation generation, executive summaries |
| **Container Runtime** | Kubernetes (EKS/GKE) + gVisor | Orchestration + sandbox isolation for scan workers |
| **Autoscaling** | KEDA + Cluster Autoscaler | Event-driven scaling for scan workers |
| **CI/CD** | GitLab CI / GitHub Actions | Pipeline automation, container image builds, deployment |
| **Observability** | Prometheus + Grafana + Loki + Jaeger | Metrics, dashboards, log aggregation, distributed tracing |
| **IaC** | Terraform + Helm | Infrastructure provisioning, Kubernetes deployments |

---

## 7. Deployment Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        CI/CD PIPELINE                                        │
│                                                                              │
│  ┌──────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌───────────┐ │
│  │ Code │───►│ Build &  │───►│ Security │───►│ Staging  │───►│Production │ │
│  │ Push │    │ Test     │    │ Gate     │    │ Deploy   │    │ Deploy    │ │
│  └──────┘    │          │    │          │    │          │    │           │ │
│              │• Unit    │    │• SAST    │    │• Canary  │    │• Blue/    │ │
│              │  tests   │    │• SCA     │    │  deploy  │    │  Green    │ │
│              │• Integ.  │    │• Container│   │• Smoke   │    │• Auto     │ │
│              │  tests   │    │  scan    │    │  tests   │    │  rollback │ │
│              │• Build   │    │• License │    │• Load    │    │• Feature  │ │
│              │  images  │    │  check   │    │  test    │    │  flags    │ │
│              │• Sign    │    │• Policy  │    │          │    │           │ │
│              │  images  │    │  check   │    │          │    │           │ │
│              └──────────┘    └──────────┘    └──────────┘    └───────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Jira / ServiceNow Integration Detail

### Bidirectional Sync Architecture

```
┌─────────────────┐                              ┌──────────────────┐
│  VAPT Platform   │                              │  Jira / SNOW     │
│                  │     finding.validated         │                  │
│  Findings ──────►│────► Create Issue ───────────►│  Issue/Incident  │
│                  │     (severity → priority      │                  │
│                  │      mapping, CWE → labels)   │                  │
│                  │                               │                  │
│  Status Update ◄─│◄──── Webhook ────────────────│  Status Change   │
│  (remediated)    │     (resolved/closed)         │  (by dev team)   │
│                  │                               │                  │
│  Retest Trigger ─│────► Triggered by status ────►│  Comment: retest │
│                  │     change to "remediated"     │  results added   │
└─────────────────┘                              └──────────────────┘

Field Mapping:
  Finding Severity Critical  →  Jira Priority P1 / SNOW Impact 1
  Finding Severity High      →  Jira Priority P2 / SNOW Impact 2
  Finding Severity Medium    →  Jira Priority P3 / SNOW Impact 3
  Finding Severity Low/Info  →  Jira Priority P4 / SNOW Impact 4
  CWE ID                     →  Jira Label / SNOW Category
  Remediation Guidance       →  Issue Description
  Evidence                   →  Attachment
```

---

*This architecture is designed to be deployed on AWS (primary), Azure, or GCP with Terraform IaC. All components are containerized and Kubernetes-native, enabling portability across cloud providers.*
