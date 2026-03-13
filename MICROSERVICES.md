# Microservices Specification — AI-Driven VAPT Orchestration Platform

## Complete Service Definitions for SaaS Architecture

---

## Microservices Interaction Diagram

```
╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                 API GATEWAY (Kong / Istio Ingress)                                ║
║                       JWT Validation │ Rate Limiting │ Tenant Routing │ mTLS                       ║
╚═══════════╦══════════════╦══════════════╦═══════════════╦════════════════╦═════════════════════════╝
            ║              ║              ║               ║                ║
            ▼              ▼              ▼               ▼                ▼
 ┌───────────────┐ ┌────────────┐ ┌──────────────┐ ┌───────────────┐ ┌──────────────┐
 │ 1.ENGAGEMENT  │ │ 2.ASSET    │ │ 3.CREDENTIAL │ │10.ANALYST     │ │11.REPORTING  │
 │   SERVICE     │ │   SERVICE  │ │   VAULT SVC  │ │  WORKFLOW SVC │ │   SERVICE    │
 └──────┬────────┘ └─────┬──────┘ └──────┬───────┘ └──────┬────────┘ └──────┬───────┘
        │                │               │                 │                  │
        │ engagement     │ asset         │                 │ finding          │ report
        │ .created       │ .registered   │                 │ .validated       │ .generated
        ▼                ▼               │                 │                  ▼
╔═══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                               KAFKA EVENT BUS (Message Backbone)                                ║
║                                                                                                 ║
║  Topics: engagement.created │ asset.registered │ scan.requested │ scan.completed                 ║
║          finding.normalized │ finding.validated │ report.generated │ notification.dispatch        ║
╚════════╦═══════════╦════════════════╦════════════════╦═══════════════════╦════════════════════════╝
         ║           ║                ║                ║                   ║
         ▼           ▼                ▼                ▼                   ▼
┌────────────────┐ ┌────────────────────────────────────────┐  ┌──────────────────┐
│ 4.SCAN         │ │      SCANNER CONNECTORS (Zone 3)       │  │ 9.FINDINGS       │
│ ORCHESTRATION  │ │                                        │  │   SERVICE        │
│ SERVICE        │ │ ┌────────┐ ┌────────┐ ┌────────┐      │  └────────┬─────────┘
│                │ │ │ 5.BURP │ │6.TENBL │ │7.FORFY │      │           │
│ (Temporal.io)  ├─┤ │ CONN.  │ │ CONN.  │ │ CONN.  │      │           │ finding
│                │ │ └────────┘ └────────┘ └────────┘      │           │ .normalized
│ scan.requested │ │ ┌────────┐                             │           ▼
│ ──────────────►│ │ │8.MOBILE│                             │  ┌──────────────────┐
│                │ │ │ CONN.  │        scan.completed       │  │12.COMPLIANCE     │
└────────────────┘ │ └────────┘ ───────────────────────────►│  │   ENGINE         │
                   └────────────────────────────────────────┘  └──────────────────┘
                                                                        │
                                      ┌─────────────────────────────────┘
                                      ▼
                             ┌──────────────────┐
                             │13.TEAMS BOT      │
                             │   SERVICE        │
                             └──────────────────┘
```

### Synchronous (REST/gRPC) Call Graph

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                     SYNCHRONOUS SERVICE DEPENDENCIES                                 │
│                                                                                      │
│  Engagement ──REST──► Asset Service        (register/query assets)                   │
│  Service     ──REST──► Credential Vault    (link credentials)                        │
│               ──REST──► Scan Orchestration (trigger scan pipeline)                   │
│                                                                                      │
│  Scan         ──REST──► Credential Vault   (checkout credentials)                    │
│  Orchestration──gRPC──► Burp Connector     (dispatch DAST scan)                      │
│               ──gRPC──► Tenable Connector  (dispatch infra scan)                     │
│               ──gRPC──► Fortify Connector  (dispatch SAST/SCA scan)                  │
│               ──gRPC──► Mobile Connector   (dispatch mobile scan)                    │
│               ──REST──► Asset Service      (resolve target details)                  │
│                                                                                      │
│  Findings     ──REST──► Compliance Engine  (map finding → controls)                  │
│  Service      ──REST──► Asset Service      (enrich with asset context)               │
│                                                                                      │
│  Analyst      ──REST──► Findings Service   (query/update findings)                   │
│  Workflow     ──REST──► Reporting Service  (trigger report generation)               │
│               ──REST──► Engagement Service (update engagement status)                │
│                                                                                      │
│  Reporting    ──REST──► Findings Service   (fetch validated findings)                │
│  Service      ──REST──► Compliance Engine  (fetch compliance mappings)               │
│               ──REST──► Engagement Service (fetch engagement metadata)               │
│               ──REST──► Asset Service      (fetch asset inventory)                   │
│                                                                                      │
│  Teams Bot    ──REST──► Engagement Service (status queries)                          │
│  Service      ──REST──► Findings Service   (finding summaries)                       │
│               ──REST──► Analyst Workflow   (approval actions)                        │
│                                                                                      │
│  Compliance   ──REST──► Findings Service   (bulk finding queries)                    │
│  Engine                                                                              │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Service 1: Engagement Service

**Purpose:** Manages the lifecycle of VAPT engagements — from creation through scoping, execution, and closure. Acts as the top-level business entity linking assets, scans, findings, and reports.

**Tech Stack:** Go 1.22 · Gin framework · PostgreSQL 16 · Redis 7

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/engagements` | Create new engagement |
| GET | `/api/v1/engagements` | List engagements (paginated, filterable) |
| GET | `/api/v1/engagements/{id}` | Get engagement details |
| PATCH | `/api/v1/engagements/{id}` | Update engagement metadata |
| POST | `/api/v1/engagements/{id}/scope` | Define engagement scope (assets, scan types) |
| POST | `/api/v1/engagements/{id}/launch` | Launch all scans for engagement |
| GET | `/api/v1/engagements/{id}/status` | Aggregated status across all scans |
| POST | `/api/v1/engagements/{id}/close` | Close engagement, finalize reports |
| GET | `/api/v1/engagements/{id}/timeline` | Audit trail of engagement events |

### Database Schema

```sql
-- Core engagement table
CREATE TABLE engagements (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    name            VARCHAR(255) NOT NULL,
    engagement_type ENUM('full_vapt', 'web_only', 'infra_only', 'mobile_only', 'compliance_audit') NOT NULL,
    status          ENUM('draft', 'scoping', 'approved', 'in_progress', 'review', 'closed') DEFAULT 'draft',
    priority        ENUM('critical', 'high', 'medium', 'low') DEFAULT 'medium',
    scheduled_start TIMESTAMPTZ,
    scheduled_end   TIMESTAMPTZ,
    actual_start    TIMESTAMPTZ,
    actual_end      TIMESTAMPTZ,
    created_by      UUID NOT NULL,
    assigned_analyst UUID,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Engagement scope definition
CREATE TABLE engagement_scopes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id   UUID NOT NULL REFERENCES engagements(id),
    asset_id        UUID NOT NULL,
    scan_types      TEXT[] NOT NULL,  -- {'dast', 'sast', 'infra', 'mobile'}
    exclusions      JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Engagement audit log
CREATE TABLE engagement_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id   UUID NOT NULL REFERENCES engagements(id),
    event_type      VARCHAR(50) NOT NULL,
    actor_id        UUID NOT NULL,
    payload         JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_engagements_tenant ON engagements(tenant_id);
CREATE INDEX idx_engagements_status ON engagements(tenant_id, status);
CREATE INDEX idx_engagement_events_eid ON engagement_events(engagement_id);
```

### Kafka Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `engagement.created` | Produces | New engagement created |
| `engagement.launched` | Produces | Scans triggered for engagement |
| `engagement.status_changed` | Produces | Status transition occurred |
| `engagement.closed` | Produces | Engagement finalized |
| `scan.completed` | Consumes | Updates engagement progress |
| `finding.validated` | Consumes | Updates finding counts |

### Dependencies
- **Asset Service** — resolve and validate scoped assets
- **Credential Vault** — link credentials to engagement scope
- **Scan Orchestration** — trigger scan pipelines on launch

### Scaling Strategy
- **Replicas:** 3–6 pods (HPA on CPU/request rate)
- **Database:** Read replicas for listing queries; primary for writes
- **Caching:** Redis for engagement status aggregation (30s TTL)

---

## Service 2: Asset Discovery & Inventory Service

**Purpose:** Maintains the centralized inventory of all target assets (web apps, APIs, infrastructure hosts, mobile apps, cloud resources). Supports auto-discovery and manual registration.

**Tech Stack:** Go 1.22 · Gin framework · PostgreSQL 16 · Elasticsearch 8

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/assets` | Register a new asset |
| GET | `/api/v1/assets` | List assets (paginated, filterable by type/tag) |
| GET | `/api/v1/assets/{id}` | Get asset details with history |
| PATCH | `/api/v1/assets/{id}` | Update asset metadata |
| DELETE | `/api/v1/assets/{id}` | Soft-delete asset |
| POST | `/api/v1/assets/discover` | Trigger auto-discovery (subdomain enum, port scan) |
| GET | `/api/v1/assets/{id}/scan-history` | Scan history for asset |
| POST | `/api/v1/assets/import` | Bulk import from CSV/JSON |
| GET | `/api/v1/assets/search` | Full-text search via Elasticsearch |
| POST | `/api/v1/assets/{id}/tags` | Add tags to asset |

### Database Schema

```sql
CREATE TABLE assets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    asset_type      ENUM('web_app', 'api', 'host', 'network_range', 'mobile_app', 'cloud_resource', 'container') NOT NULL,
    name            VARCHAR(255) NOT NULL,
    identifier      VARCHAR(512) NOT NULL,  -- URL, IP, CIDR, package name
    environment     ENUM('production', 'staging', 'development', 'qa') DEFAULT 'production',
    criticality     ENUM('critical', 'high', 'medium', 'low') DEFAULT 'medium',
    owner           VARCHAR(255),
    tech_stack      JSONB DEFAULT '[]',     -- detected technologies
    discovery_source ENUM('manual', 'subdomain_enum', 'port_scan', 'cloud_sync', 'cicd_import') DEFAULT 'manual',
    status          ENUM('active', 'inactive', 'decommissioned') DEFAULT 'active',
    last_scanned_at TIMESTAMPTZ,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, asset_type, identifier)
);

CREATE TABLE asset_tags (
    asset_id    UUID NOT NULL REFERENCES assets(id),
    tag_key     VARCHAR(100) NOT NULL,
    tag_value   VARCHAR(255) NOT NULL,
    PRIMARY KEY (asset_id, tag_key)
);

CREATE TABLE asset_relationships (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_asset_id UUID NOT NULL REFERENCES assets(id),
    child_asset_id  UUID NOT NULL REFERENCES assets(id),
    relationship    ENUM('hosts', 'exposes_api', 'depends_on', 'part_of') NOT NULL
);

CREATE INDEX idx_assets_tenant_type ON assets(tenant_id, asset_type);
CREATE INDEX idx_assets_identifier ON assets(tenant_id, identifier);
CREATE INDEX idx_assets_criticality ON assets(tenant_id, criticality);
```

### Kafka Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `asset.registered` | Produces | New asset added to inventory |
| `asset.updated` | Produces | Asset metadata changed |
| `asset.discovered` | Produces | Auto-discovery found new asset |
| `scan.completed` | Consumes | Updates `last_scanned_at` timestamp |

### Dependencies
- **Elasticsearch** — full-text search across asset metadata
- **External:** Subdomain enumeration tools (amass, subfinder) for discovery

### Scaling Strategy
- **Replicas:** 3–5 pods
- **Elasticsearch:** 3-node cluster for search indexing
- **Database:** Partitioned by `tenant_id` for large multi-tenant deployments

---

## Service 3: Credential Vault Service

**Purpose:** Securely stores and manages scanner credentials, API keys, SSH keys, and authentication tokens. Provides short-lived credential checkout with automatic rotation and audit logging.

**Tech Stack:** Go 1.22 · Gin framework · HashiCorp Vault · PostgreSQL 16

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/credentials` | Store a new credential |
| GET | `/api/v1/credentials` | List credentials (metadata only, no secrets) |
| GET | `/api/v1/credentials/{id}` | Get credential metadata |
| DELETE | `/api/v1/credentials/{id}` | Revoke and delete credential |
| POST | `/api/v1/credentials/{id}/checkout` | Checkout credential (time-limited, returns secret) |
| POST | `/api/v1/credentials/{id}/checkin` | Return/release checked-out credential |
| POST | `/api/v1/credentials/{id}/rotate` | Trigger credential rotation |
| GET | `/api/v1/credentials/{id}/audit` | Audit log of credential access |
| POST | `/api/v1/credentials/test` | Test credential validity against target |

### Database Schema

```sql
-- Credential metadata (secrets stored in HashiCorp Vault)
CREATE TABLE credentials (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    name            VARCHAR(255) NOT NULL,
    credential_type ENUM('username_password', 'api_key', 'ssh_key', 'oauth_token', 'certificate', 'aws_role') NOT NULL,
    scope           ENUM('scanner', 'target_auth', 'cloud_api', 'cicd') NOT NULL,
    vault_path      VARCHAR(512) NOT NULL,  -- HashiCorp Vault secret path
    linked_assets   UUID[] DEFAULT '{}',
    rotation_policy JSONB DEFAULT '{"enabled": false}',
    last_rotated_at TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    status          ENUM('active', 'expired', 'revoked', 'rotating') DEFAULT 'active',
    created_by      UUID NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE credential_checkouts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    credential_id   UUID NOT NULL REFERENCES credentials(id),
    checked_out_by  VARCHAR(255) NOT NULL,  -- service name or user ID
    purpose         VARCHAR(255) NOT NULL,  -- scan ID or reason
    checked_out_at  TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ NOT NULL,
    checked_in_at   TIMESTAMPTZ,
    status          ENUM('active', 'returned', 'expired') DEFAULT 'active'
);

CREATE TABLE credential_audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    credential_id   UUID NOT NULL,
    action          ENUM('created', 'checkout', 'checkin', 'rotated', 'revoked', 'tested') NOT NULL,
    actor           VARCHAR(255) NOT NULL,
    ip_address      INET,
    details         JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_credentials_tenant ON credentials(tenant_id);
CREATE INDEX idx_checkouts_active ON credential_checkouts(credential_id, status) WHERE status = 'active';
CREATE INDEX idx_audit_credential ON credential_audit_log(credential_id, created_at);
```

### Security Controls
- All secrets stored in HashiCorp Vault (AES-256-GCM encryption at rest)
- Checkout returns time-limited wrapped tokens (max 4-hour TTL)
- mTLS required for all inbound connections
- No secret values ever written to application logs or database
- Automatic expiry of unchecked-in credentials

### Dependencies
- **HashiCorp Vault** — secret storage backend
- **No downstream service dependencies** — this is a leaf service

### Scaling Strategy
- **Replicas:** 2–3 pods (low throughput, high security)
- **Vault:** 3-node HA cluster with auto-unseal via AWS KMS
- **Rate limiting:** Max 10 checkouts/minute per tenant

---

## Service 4: Scan Orchestration Service

**Purpose:** Orchestrates end-to-end scan workflows using Temporal.io. Manages scan lifecycle from request through dispatch to scanner connectors, progress tracking, retry logic, and completion.

**Tech Stack:** Go 1.22 · Temporal.io · PostgreSQL 16 · Redis 7

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/scans` | Request a new scan |
| GET | `/api/v1/scans` | List scans (paginated, filterable) |
| GET | `/api/v1/scans/{id}` | Get scan details and progress |
| POST | `/api/v1/scans/{id}/cancel` | Cancel a running scan |
| POST | `/api/v1/scans/{id}/retry` | Retry a failed scan |
| GET | `/api/v1/scans/{id}/logs` | Stream scan execution logs |
| GET | `/api/v1/scans/queue` | View scan queue depth and wait times |
| POST | `/api/v1/scans/batch` | Submit batch scan request |

### Database Schema

```sql
CREATE TABLE scans (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    engagement_id   UUID NOT NULL,
    asset_id        UUID NOT NULL,
    scan_type       ENUM('dast', 'sast', 'sca', 'infra', 'mobile', 'api_fuzz') NOT NULL,
    scanner         ENUM('burp_suite', 'tenable', 'fortify', 'mobsf', 'nuclei', 'zap') NOT NULL,
    status          ENUM('queued', 'credential_checkout', 'dispatched', 'running', 'collecting_results', 'completed', 'failed', 'cancelled') DEFAULT 'queued',
    priority        INT DEFAULT 5,  -- 1 (highest) to 10 (lowest)
    temporal_workflow_id VARCHAR(255),
    temporal_run_id     VARCHAR(255),
    scan_config     JSONB DEFAULT '{}',  -- scanner-specific configuration
    progress_pct    INT DEFAULT 0,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    error_message   TEXT,
    retry_count     INT DEFAULT 0,
    max_retries     INT DEFAULT 3,
    credential_id   UUID,
    result_summary  JSONB DEFAULT '{}',  -- {critical: 2, high: 5, medium: 12, low: 8, info: 20}
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE scan_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id     UUID NOT NULL REFERENCES scans(id),
    level       ENUM('info', 'warn', 'error', 'debug') NOT NULL,
    message     TEXT NOT NULL,
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scans_tenant_status ON scans(tenant_id, status);
CREATE INDEX idx_scans_engagement ON scans(engagement_id);
CREATE INDEX idx_scans_queue ON scans(status, priority, created_at) WHERE status = 'queued';
CREATE INDEX idx_scan_logs_scan ON scan_logs(scan_id, created_at);
```

### Temporal Workflows

```
ScanWorkflow:
  1. ValidateRequest     → Check asset exists, scan type valid
  2. CheckoutCredential  → Get scanner/target credentials from Vault
  3. DispatchToScanner   → gRPC call to appropriate connector
  4. MonitorProgress     → Poll scanner for status (with timeout)
  5. CollectResults      → Fetch raw results from scanner
  6. PublishResults      → Emit scan.completed event to Kafka
  7. CheckinCredential   → Return credentials to Vault
  8. UpdateStatus        → Mark scan as completed/failed

  Retry Policy: 3 retries with exponential backoff (30s, 120s, 300s)
  Timeout: 4 hours max per scan
```

### Kafka Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `scan.requested` | Consumes | Triggers scan workflow |
| `scan.progress` | Produces | Progress updates (10% increments) |
| `scan.completed` | Produces | Scan finished with result summary |
| `scan.failed` | Produces | Scan failed after all retries |

### Dependencies
- **Temporal.io** — workflow orchestration engine
- **Credential Vault** — checkout/checkin scanner credentials
- **Scanner Connectors (5–8)** — dispatch scans via gRPC
- **Asset Service** — resolve target details

### Scaling Strategy
- **Replicas:** 3–8 pods (HPA on queue depth)
- **Temporal Workers:** Separate worker pool, 5–20 pods based on scan volume
- **Concurrency:** Max 10 concurrent scans per tenant (configurable)
- **Queue:** Priority-based scheduling; critical engagements preempt low-priority

---

## Service 5: Burp Suite Connector

**Purpose:** Interfaces with Burp Suite Enterprise Edition REST API to execute DAST (Dynamic Application Security Testing) scans against web applications and APIs.

**Tech Stack:** Python 3.12 · FastAPI · httpx (async HTTP) · gRPC server

### gRPC Interface

```protobuf
service BurpConnector {
    rpc StartScan(StartScanRequest) returns (StartScanResponse);
    rpc GetScanStatus(ScanStatusRequest) returns (ScanStatusResponse);
    rpc GetScanResults(ScanResultsRequest) returns (stream Finding);
    rpc CancelScan(CancelScanRequest) returns (CancelScanResponse);
    rpc ListScanConfigs(Empty) returns (ScanConfigList);
    rpc HealthCheck(Empty) returns (HealthResponse);
}

message StartScanRequest {
    string scan_id = 1;
    string target_url = 2;
    string scan_config_name = 3;          // "Audit checks - all", "Crawl and audit - lightweight"
    map<string, string> credentials = 4;  // target auth credentials
    repeated string excluded_paths = 5;
    BurpScanOptions options = 6;
}

message Finding {
    string issue_type = 1;
    string name = 2;
    string severity = 3;       // "high", "medium", "low", "info"
    string confidence = 4;     // "certain", "firm", "tentative"
    string url = 5;
    string path = 6;
    string description = 7;
    string remediation = 8;
    repeated Evidence evidence = 9;
    string cwe_id = 10;
}
```

### Scanner Integration Details

| Aspect | Detail |
|--------|--------|
| Burp API Version | Enterprise REST API v2 |
| Authentication | API key (stored in Credential Vault) |
| Scan Profiles | Configurable: Crawl-only, Audit-only, Full Crawl+Audit |
| Result Polling | Every 30s during active scan |
| Max Scan Duration | 4 hours (configurable per engagement) |
| Concurrent Scans | Limited by Burp Enterprise license (typically 5–25) |

### Finding Normalization
Maps Burp-specific issue types to the platform's unified finding schema:
- Severity mapping: Burp High → Platform Critical/High (based on confidence)
- CWE enrichment from Burp issue type database
- Evidence extraction: HTTP request/response pairs, DOM snapshots

### Scaling Strategy
- **Replicas:** 2–4 pods
- **Burp Enterprise:** Deployed in Zone 3 (scanner network), accessed via internal API
- **Connection pool:** Max 5 concurrent API connections to Burp Enterprise

---

## Service 6: Tenable Connector

**Purpose:** Interfaces with Tenable.io / Nessus API to execute infrastructure vulnerability scans (network, OS, configuration audits).

**Tech Stack:** Python 3.12 · FastAPI · httpx · gRPC server

### gRPC Interface

```protobuf
service TenableConnector {
    rpc StartScan(InfraScanRequest) returns (StartScanResponse);
    rpc GetScanStatus(ScanStatusRequest) returns (ScanStatusResponse);
    rpc GetScanResults(ScanResultsRequest) returns (stream InfraFinding);
    rpc CancelScan(CancelScanRequest) returns (CancelScanResponse);
    rpc ListScanTemplates(Empty) returns (ScanTemplateList);
    rpc HealthCheck(Empty) returns (HealthResponse);
}

message InfraScanRequest {
    string scan_id = 1;
    repeated string targets = 2;          // IPs, CIDRs, hostnames
    string scan_template = 3;            // "basic", "advanced", "pci", "webapp"
    map<string, string> credentials = 4; // SSH, WinRM, SNMP credentials
    repeated int32 port_list = 5;
    InfraScanOptions options = 6;
}

message InfraFinding {
    string plugin_id = 1;
    string plugin_name = 2;
    string severity = 3;          // "critical", "high", "medium", "low", "info"
    float cvss_score = 4;
    string cvss_vector = 5;
    string description = 6;
    string solution = 7;
    string host = 8;
    int32 port = 9;
    string protocol = 10;
    repeated string cve_ids = 11;
    string plugin_output = 12;
    string exploit_available = 13;
}
```

### Scanner Integration Details

| Aspect | Detail |
|--------|--------|
| Tenable API Version | Tenable.io REST API v3 |
| Authentication | API key + secret key pair |
| Scan Templates | Basic Network, Advanced, PCI-DSS, SCAP |
| Credential Scans | SSH, WinRM, SNMP v1/v2c/v3 |
| Result Polling | Every 60s during active scan |
| Max Scan Duration | 8 hours |

### Finding Normalization
- Maps Tenable plugin severity + CVSS score → Platform severity
- Extracts CVE references, CVSS vectors, exploit availability
- Groups findings by host for per-asset reporting

### Scaling Strategy
- **Replicas:** 2–3 pods
- **Tenable.io:** Cloud-hosted, API rate limits apply (1000 req/min)
- **Nessus Scanners:** On-premise scanners in Zone 3 for internal network scans

---

## Service 7: Fortify Connector

**Purpose:** Interfaces with Micro Focus Fortify (SSC + ScanCentral) for SAST (Static Application Security Testing) and SCA (Software Composition Analysis) scans.

**Tech Stack:** Java 21 · Spring Boot 3.3 · gRPC server

### gRPC Interface

```protobuf
service FortifyConnector {
    rpc StartSASTScan(SASTScanRequest) returns (StartScanResponse);
    rpc StartSCAScan(SCAScanRequest) returns (StartScanResponse);
    rpc GetScanStatus(ScanStatusRequest) returns (ScanStatusResponse);
    rpc GetScanResults(ScanResultsRequest) returns (stream CodeFinding);
    rpc CancelScan(CancelScanRequest) returns (CancelScanResponse);
    rpc HealthCheck(Empty) returns (HealthResponse);
}

message SASTScanRequest {
    string scan_id = 1;
    string repo_url = 2;
    string branch = 3;
    string commit_sha = 4;
    repeated string languages = 5;        // "java", "csharp", "python", "javascript"
    map<string, string> credentials = 6;  // repo access credentials
    SASTOptions options = 7;
}

message SCAScanRequest {
    string scan_id = 1;
    string repo_url = 2;
    string branch = 3;
    repeated string manifest_files = 4;   // "pom.xml", "package.json", "requirements.txt"
    map<string, string> credentials = 5;
}

message CodeFinding {
    string category = 1;           // "SQL Injection", "XSS", "Buffer Overflow"
    string severity = 2;
    float confidence = 3;
    string file_path = 4;
    int32 line_number = 5;
    string code_snippet = 6;
    string description = 7;
    string remediation = 8;
    string cwe_id = 9;
    string data_flow = 10;         // Source → Sink trace for taint analysis
    string component_name = 11;    // For SCA: vulnerable library name
    string component_version = 12; // For SCA: vulnerable version
    repeated string cve_ids = 13;  // For SCA: associated CVEs
}
```

### Scanner Integration Details

| Aspect | Detail |
|--------|--------|
| Fortify SSC API | REST API v4 |
| ScanCentral | SAST scan offloading to dedicated build agents |
| Languages | Java, C#, Python, JavaScript/TypeScript, Go, C/C++ |
| SCA Engine | Fortify Audit Workbench + Sonatype integration |
| Max Scan Duration | 6 hours (large codebases) |

### Scaling Strategy
- **Replicas:** 2–3 pods
- **ScanCentral Sensors:** 3–10 build agents for parallel SAST analysis
- **Source Code:** Cloned to ephemeral volumes, destroyed post-scan

---

## Service 8: Mobile Security Connector

**Purpose:** Orchestrates mobile application security testing using MobSF (Mobile Security Framework) for both static and dynamic analysis of Android (APK) and iOS (IPA) apps.

**Tech Stack:** Python 3.12 · FastAPI · gRPC server · MobSF API

### gRPC Interface

```protobuf
service MobileConnector {
    rpc StartStaticAnalysis(MobileStaticRequest) returns (StartScanResponse);
    rpc StartDynamicAnalysis(MobileDynamicRequest) returns (StartScanResponse);
    rpc GetScanStatus(ScanStatusRequest) returns (ScanStatusResponse);
    rpc GetScanResults(ScanResultsRequest) returns (stream MobileFinding);
    rpc CancelScan(CancelScanRequest) returns (CancelScanResponse);
    rpc UploadBinary(stream BinaryChunk) returns (UploadResponse);
    rpc HealthCheck(Empty) returns (HealthResponse);
}

message MobileStaticRequest {
    string scan_id = 1;
    string binary_hash = 2;       // SHA-256 of uploaded APK/IPA
    string platform = 3;          // "android" or "ios"
    MobileStaticOptions options = 4;
}

message MobileDynamicRequest {
    string scan_id = 1;
    string binary_hash = 2;
    string platform = 3;
    map<string, string> credentials = 4;  // App login credentials
    MobileDynamicOptions options = 5;
}

message MobileFinding {
    string category = 1;          // "Insecure Storage", "Weak Crypto", "SSL Pinning"
    string severity = 2;
    string description = 3;
    string file_path = 4;         // Decompiled source path
    string code_snippet = 5;
    string remediation = 6;
    string owasp_mobile = 7;      // OWASP Mobile Top 10 mapping (M1-M10)
    string cwe_id = 8;
    string masvs_category = 9;    // MASVS verification category
}
```

### Scanner Integration Details

| Aspect | Detail |
|--------|--------|
| MobSF API | REST API v3 |
| Static Analysis | Decompilation, manifest analysis, code review, binary analysis |
| Dynamic Analysis | Runtime instrumentation via Frida, API hooking, traffic analysis |
| Platforms | Android (APK, AAB), iOS (IPA) |
| Binary Storage | MinIO with encryption, auto-purge after 72 hours |
| Max Binary Size | 500 MB |

### Scaling Strategy
- **Replicas:** 2 pods (static), 1–2 pods (dynamic — requires emulator)
- **Android Emulators:** Dedicated VMs with Android 12–14 images
- **Binary Storage:** MinIO cluster for temporary APK/IPA storage

---

## Service 9: Findings Normalization & Deduplication Service

**Purpose:** Ingests raw scanner output from all connectors, normalizes to a unified schema, deduplicates across scanners and scans, enriches with AI-driven analysis (severity validation, exploitability scoring), and stores the canonical finding records.

**Tech Stack:** Python 3.12 · FastAPI · PostgreSQL 16 · Elasticsearch 8 · Redis 7

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/findings` | List findings (paginated, filterable) |
| GET | `/api/v1/findings/{id}` | Get finding detail with evidence |
| PATCH | `/api/v1/findings/{id}` | Update finding (status, severity override) |
| POST | `/api/v1/findings/{id}/validate` | Analyst validates/rejects finding |
| GET | `/api/v1/findings/stats` | Aggregated finding statistics |
| GET | `/api/v1/findings/duplicates/{id}` | View duplicate cluster for a finding |
| POST | `/api/v1/findings/search` | Advanced search via Elasticsearch |
| GET | `/api/v1/findings/trends` | Finding trends over time |
| POST | `/api/v1/findings/bulk-update` | Bulk status/severity update |
| GET | `/api/v1/findings/{id}/remediation` | AI-generated remediation guidance |

### Database Schema

```sql
CREATE TABLE findings (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL,
    engagement_id       UUID NOT NULL,
    scan_id             UUID NOT NULL,
    asset_id            UUID NOT NULL,

    -- Normalized fields
    title               VARCHAR(500) NOT NULL,
    description         TEXT NOT NULL,
    severity            ENUM('critical', 'high', 'medium', 'low', 'info') NOT NULL,
    original_severity   ENUM('critical', 'high', 'medium', 'low', 'info') NOT NULL,
    confidence          ENUM('confirmed', 'high', 'medium', 'low') DEFAULT 'medium',
    status              ENUM('new', 'confirmed', 'false_positive', 'accepted_risk', 'remediated', 'reopened') DEFAULT 'new',

    -- Classification
    category            VARCHAR(255) NOT NULL,    -- "SQL Injection", "XSS", "Misconfiguration"
    cwe_id              VARCHAR(20),
    cve_ids             TEXT[] DEFAULT '{}',
    cvss_score          DECIMAL(3,1),
    cvss_vector         VARCHAR(100),
    owasp_category      VARCHAR(50),              -- "A01:2021", "A03:2021"

    -- Source
    scanner             VARCHAR(50) NOT NULL,
    scan_type           ENUM('dast', 'sast', 'sca', 'infra', 'mobile') NOT NULL,

    -- Location
    location            JSONB NOT NULL,           -- {url, path, host, port, file, line}

    -- Evidence
    evidence            JSONB DEFAULT '[]',       -- [{type, content}]

    -- AI Analysis
    ai_severity_score   DECIMAL(5,2),             -- ML-predicted severity (0-10)
    ai_exploitability   DECIMAL(5,2),             -- Exploitability score (0-10)
    ai_remediation      TEXT,                     -- AI-generated remediation
    ai_false_positive_probability DECIMAL(3,2),   -- 0.0 to 1.0

    -- Deduplication
    fingerprint         VARCHAR(64) NOT NULL,     -- SHA-256 dedup key
    duplicate_cluster_id UUID,
    is_primary          BOOLEAN DEFAULT true,     -- Primary finding in dedup cluster

    -- Workflow
    assigned_to         UUID,
    validated_by        UUID,
    validated_at        TIMESTAMPTZ,
    remediated_at       TIMESTAMPTZ,

    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE finding_comments (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id  UUID NOT NULL REFERENCES findings(id),
    author_id   UUID NOT NULL,
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_findings_tenant_engagement ON findings(tenant_id, engagement_id);
CREATE INDEX idx_findings_severity ON findings(tenant_id, severity) WHERE status NOT IN ('false_positive', 'remediated');
CREATE INDEX idx_findings_fingerprint ON findings(tenant_id, fingerprint);
CREATE INDEX idx_findings_cwe ON findings(cwe_id) WHERE cwe_id IS NOT NULL;
CREATE INDEX idx_findings_asset ON findings(asset_id);
```

### Deduplication Algorithm

```
1. Generate fingerprint = SHA-256(tenant_id + category + normalized_location + cwe_id)
2. Query existing findings with same fingerprint
3. If match found:
   a. Same engagement → merge evidence, keep highest severity
   b. Different engagement → link as recurrence, track remediation regression
4. If no match → create as new primary finding
5. Cross-scanner correlation: findings from different scanners for same
   vulnerability are clustered (e.g., Burp XSS + Fortify XSS on same endpoint)
```

### Kafka Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `scan.completed` | Consumes | Triggers result ingestion from scanner |
| `finding.normalized` | Produces | New finding normalized and stored |
| `finding.deduplicated` | Produces | Finding matched to existing cluster |
| `finding.ai_enriched` | Produces | AI analysis completed |

### Dependencies
- **Compliance Engine** — map findings to compliance controls
- **Asset Service** — enrich findings with asset context
- **AI/ML pipeline** — severity validation, exploitability scoring, false positive detection

### Scaling Strategy
- **Replicas:** 3–8 pods (HPA on Kafka consumer lag)
- **Elasticsearch:** Dedicated index per tenant for search isolation
- **Batch Processing:** Bulk ingestion of scan results (1000 findings/batch)

---

## Service 10: Analyst Workflow Service

**Purpose:** Manages the human-in-the-loop workflow for finding triage, validation, and remediation tracking. Provides task queues, SLA tracking, and collaboration features for security analysts.

**Tech Stack:** Go 1.22 · Gin framework · PostgreSQL 16 · Redis 7 · WebSocket (gorilla/websocket)

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/worklist` | Get analyst's assigned work items |
| GET | `/api/v1/worklist/queue` | View unassigned finding queue |
| POST | `/api/v1/worklist/claim` | Claim next item from queue |
| POST | `/api/v1/findings/{id}/triage` | Submit triage decision |
| POST | `/api/v1/findings/{id}/validate` | Validate finding (confirm/reject) |
| POST | `/api/v1/findings/{id}/assign` | Assign finding to analyst |
| POST | `/api/v1/findings/{id}/escalate` | Escalate to senior analyst |
| GET | `/api/v1/findings/{id}/ai-assist` | Get AI-assisted triage recommendation |
| POST | `/api/v1/approvals` | Create approval request (e.g., risk acceptance) |
| PATCH | `/api/v1/approvals/{id}` | Approve or reject |
| GET | `/api/v1/sla/dashboard` | SLA compliance dashboard |
| WS | `/ws/v1/notifications` | Real-time notification stream |

### Database Schema

```sql
CREATE TABLE work_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    finding_id      UUID NOT NULL,
    engagement_id   UUID NOT NULL,
    item_type       ENUM('triage', 'validation', 'retest', 'approval') NOT NULL,
    status          ENUM('queued', 'assigned', 'in_progress', 'completed', 'escalated') DEFAULT 'queued',
    priority        INT NOT NULL,  -- calculated from finding severity + SLA urgency
    assigned_to     UUID,
    assigned_at     TIMESTAMPTZ,
    sla_deadline    TIMESTAMPTZ NOT NULL,
    sla_breached    BOOLEAN DEFAULT false,
    completed_at    TIMESTAMPTZ,
    decision        JSONB,         -- {action, justification, overrides}
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE approvals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    finding_id      UUID,
    engagement_id   UUID NOT NULL,
    approval_type   ENUM('risk_acceptance', 'false_positive', 'severity_override', 'report_publish') NOT NULL,
    requested_by    UUID NOT NULL,
    approved_by     UUID,
    status          ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    justification   TEXT NOT NULL,
    decision_notes  TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    decided_at      TIMESTAMPTZ
);

CREATE TABLE sla_policies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    severity        ENUM('critical', 'high', 'medium', 'low', 'info') NOT NULL,
    triage_hours    INT NOT NULL,       -- Hours to complete triage
    validation_hours INT NOT NULL,      -- Hours to complete validation
    escalation_hours INT NOT NULL,      -- Hours before auto-escalation
    UNIQUE(tenant_id, severity)
);

CREATE INDEX idx_workitems_queue ON work_items(tenant_id, status, priority DESC) WHERE status = 'queued';
CREATE INDEX idx_workitems_assigned ON work_items(assigned_to, status) WHERE status IN ('assigned', 'in_progress');
CREATE INDEX idx_workitems_sla ON work_items(sla_deadline) WHERE sla_breached = false AND status NOT IN ('completed');
```

### SLA Engine
```
Default SLA Policies:
  Critical findings: Triage within 4h, Validate within 8h
  High findings:     Triage within 8h, Validate within 24h
  Medium findings:   Triage within 24h, Validate within 72h
  Low findings:      Triage within 72h, Validate within 1 week

Auto-escalation: Finding escalated to senior analyst when 80% of SLA consumed
SLA breach: Notification to team lead + recorded in compliance audit
```

### Kafka Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `finding.normalized` | Consumes | Creates work items for new findings |
| `finding.validated` | Produces | Finding triage/validation completed |
| `sla.breach` | Produces | SLA deadline exceeded |
| `notification.dispatch` | Produces | Triggers notifications |

### Dependencies
- **Findings Service** — query/update finding records
- **Reporting Service** — trigger report generation post-validation
- **Engagement Service** — update engagement status

### Scaling Strategy
- **Replicas:** 3–5 pods
- **WebSocket:** Sticky sessions via Istio for real-time notifications
- **SLA Cron:** Dedicated cron job checking SLA deadlines every 5 minutes

---

## Service 11: Reporting & Export Service

**Purpose:** Generates comprehensive VAPT reports in multiple formats (PDF, DOCX, HTML, JSON). Supports customizable templates, executive summaries, technical details, and compliance mapping sections.

**Tech Stack:** Python 3.12 · FastAPI · WeasyPrint (PDF) · python-docx · Jinja2 · MinIO

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/reports` | Generate a new report |
| GET | `/api/v1/reports` | List generated reports |
| GET | `/api/v1/reports/{id}` | Get report metadata and download URL |
| GET | `/api/v1/reports/{id}/download` | Download report file |
| DELETE | `/api/v1/reports/{id}` | Delete report |
| GET | `/api/v1/reports/templates` | List available report templates |
| POST | `/api/v1/reports/templates` | Upload custom report template |
| POST | `/api/v1/reports/{id}/approve` | Approve report for client delivery |
| POST | `/api/v1/reports/preview` | Generate report preview (first 5 pages) |

### Database Schema

```sql
CREATE TABLE reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    engagement_id   UUID NOT NULL,
    report_type     ENUM('executive_summary', 'full_technical', 'compliance', 'delta', 'custom') NOT NULL,
    format          ENUM('pdf', 'docx', 'html', 'json', 'csv') NOT NULL,
    template_id     UUID REFERENCES report_templates(id),
    status          ENUM('queued', 'generating', 'generated', 'approved', 'delivered', 'failed') DEFAULT 'queued',
    title           VARCHAR(500) NOT NULL,
    file_path       VARCHAR(512),       -- MinIO object path
    file_size_bytes BIGINT,
    page_count      INT,
    generated_by    UUID NOT NULL,
    approved_by     UUID,
    approved_at     TIMESTAMPTZ,
    metadata        JSONB DEFAULT '{}', -- {finding_counts, scope_summary, generation_time_ms}
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE report_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID,               -- NULL = system-wide template
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    template_type   ENUM('executive_summary', 'full_technical', 'compliance', 'delta') NOT NULL,
    template_data   JSONB NOT NULL,     -- Jinja2 template configuration
    branding        JSONB DEFAULT '{}', -- {logo_url, colors, fonts}
    is_default      BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### Report Sections (Full Technical Report)
```
1. Cover Page (client branding + engagement metadata)
2. Executive Summary (risk score, key stats, trend analysis)
3. Scope & Methodology (assets tested, scan types, tools used)
4. Finding Summary (severity distribution chart, top findings)
5. Detailed Findings (per-finding: description, evidence, remediation, CVSS)
6. Compliance Mapping (findings mapped to regulatory controls)
7. Asset Inventory (tested assets with risk ratings)
8. Appendix A: Raw Scanner Output References
9. Appendix B: Glossary & Methodology Notes
```

### Kafka Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `finding.validated` | Consumes | Triggers auto-report if all findings validated |
| `report.generated` | Produces | Report ready for download |
| `report.approved` | Produces | Report approved for delivery |

### Dependencies
- **Findings Service** — fetch validated findings with evidence
- **Compliance Engine** — fetch compliance control mappings
- **Engagement Service** — fetch engagement metadata and scope
- **Asset Service** — fetch asset inventory
- **MinIO** — report file storage

### Scaling Strategy
- **Replicas:** 2–4 pods (HPA on queue depth)
- **PDF Generation:** CPU-intensive; dedicated pod pool with higher CPU limits (2 cores)
- **Storage:** MinIO with tenant-isolated buckets, 90-day retention default

---

## Service 12: Compliance Mapping Engine

**Purpose:** Maps security findings to regulatory and industry compliance frameworks (ISO 27001, SOC 2, PCI-DSS, HIPAA, NIST, OWASP). Provides gap analysis, control coverage reporting, and audit evidence.

**Tech Stack:** Go 1.22 · Gin framework · PostgreSQL 16 · Redis 7

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/frameworks` | List supported compliance frameworks |
| GET | `/api/v1/frameworks/{id}/controls` | List controls for a framework |
| POST | `/api/v1/mappings/analyze` | Map findings to compliance controls |
| GET | `/api/v1/mappings/engagement/{id}` | Get compliance posture for engagement |
| GET | `/api/v1/mappings/gap-analysis/{framework}` | Gap analysis for specific framework |
| GET | `/api/v1/mappings/coverage` | Control coverage percentage |
| POST | `/api/v1/mappings/evidence` | Link evidence to compliance control |
| GET | `/api/v1/mappings/audit-export` | Export audit-ready compliance report |

### Database Schema

```sql
CREATE TABLE compliance_frameworks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(50) UNIQUE NOT NULL,  -- "iso27001", "pci_dss_4", "soc2", "hipaa"
    name            VARCHAR(255) NOT NULL,
    version         VARCHAR(50) NOT NULL,
    description     TEXT,
    total_controls  INT NOT NULL,
    is_active       BOOLEAN DEFAULT true
);

CREATE TABLE compliance_controls (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    framework_id    UUID NOT NULL REFERENCES compliance_frameworks(id),
    control_id      VARCHAR(50) NOT NULL,      -- "A.8.8", "6.2.4", "CC6.1"
    title           VARCHAR(500) NOT NULL,
    description     TEXT,
    category        VARCHAR(255),
    parent_control  UUID REFERENCES compliance_controls(id),
    UNIQUE(framework_id, control_id)
);

-- CWE → Compliance Control mapping
CREATE TABLE cwe_control_mappings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cwe_id          VARCHAR(20) NOT NULL,
    control_id      UUID NOT NULL REFERENCES compliance_controls(id),
    relevance       ENUM('direct', 'indirect', 'supportive') DEFAULT 'direct',
    UNIQUE(cwe_id, control_id)
);

-- Finding → Control instance mapping (per engagement)
CREATE TABLE finding_control_mappings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    engagement_id   UUID NOT NULL,
    finding_id      UUID NOT NULL,
    control_id      UUID NOT NULL REFERENCES compliance_controls(id),
    impact          ENUM('fail', 'partial', 'observation') NOT NULL,
    evidence_notes  TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cwe_mappings ON cwe_control_mappings(cwe_id);
CREATE INDEX idx_finding_controls ON finding_control_mappings(engagement_id, control_id);
```

### Supported Frameworks

| Framework | Version | Controls |
|-----------|---------|----------|
| ISO 27001 | 2022 | 93 controls |
| SOC 2 | 2017 | 64 criteria |
| PCI-DSS | 4.0 | 264 requirements |
| HIPAA | Security Rule | 54 standards |
| NIST CSF | 2.0 | 106 subcategories |
| OWASP Top 10 | 2021 | 10 categories |
| OWASP ASVS | 4.0 | 286 requirements |
| CIS Controls | v8 | 153 safeguards |

### Dependencies
- **Findings Service** — bulk query findings for mapping
- **Pre-loaded:** CWE → Control mappings seeded at deployment

### Scaling Strategy
- **Replicas:** 2–3 pods
- **Caching:** Redis cache for framework data (1-hour TTL, rarely changes)
- **Bulk Processing:** Batch mapping of findings at engagement completion

---

## Service 13: Microsoft Teams Bot Service

**Purpose:** Provides a conversational interface for security analysts and stakeholders via Microsoft Teams. Supports real-time notifications, status queries, approval workflows, and finding summaries directly within Teams channels.

**Tech Stack:** Node.js 20 · Bot Framework SDK v4 · Express.js · Adaptive Cards

### Bot Commands

| Command | Description |
|---------|-------------|
| `@vapt status <engagement-id>` | Get engagement status summary |
| `@vapt findings <engagement-id>` | Finding severity breakdown |
| `@vapt critical` | List all open critical findings |
| `@vapt approve <approval-id>` | Approve a pending request |
| `@vapt reject <approval-id> <reason>` | Reject with justification |
| `@vapt report <engagement-id>` | Request report generation |
| `@vapt subscribe <engagement-id>` | Subscribe to engagement notifications |
| `@vapt unsubscribe <engagement-id>` | Unsubscribe from notifications |
| `@vapt help` | Show available commands |

### Database Schema

```sql
CREATE TABLE teams_subscriptions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    engagement_id   UUID NOT NULL,
    teams_channel_id VARCHAR(255) NOT NULL,
    teams_user_id   VARCHAR(255) NOT NULL,
    notification_types TEXT[] DEFAULT '{all}',  -- 'critical_finding', 'scan_complete', 'sla_breach', 'approval'
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE teams_conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teams_conversation_id VARCHAR(255) NOT NULL,
    teams_user_id   VARCHAR(255) NOT NULL,
    tenant_id       UUID NOT NULL,
    user_id         UUID NOT NULL,       -- Mapped platform user
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### Notification Types (Adaptive Cards)

| Notification | Trigger | Card Content |
|-------------|---------|--------------|
| Critical Finding | `finding.normalized` with severity=critical | Finding title, asset, CVSS, quick-action buttons |
| Scan Complete | `scan.completed` | Scan summary, finding counts, link to dashboard |
| SLA Breach | `sla.breach` | Breach details, affected findings, escalation path |
| Approval Request | `approval.requested` | Request details, Approve/Reject buttons |
| Report Ready | `report.generated` | Report link, summary statistics |
| Engagement Status | `engagement.status_changed` | Status transition, next steps |

### Kafka Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `notification.dispatch` | Consumes | Routes notifications to subscribed channels |
| `finding.normalized` | Consumes | Filters for critical findings → instant alert |
| `scan.completed` | Consumes | Sends scan completion cards |
| `sla.breach` | Consumes | Sends SLA breach alerts |

### Dependencies
- **Engagement Service** — status queries
- **Findings Service** — finding summaries and details
- **Analyst Workflow** — approval actions
- **Microsoft Bot Framework** — Teams integration
- **Azure AD** — user identity mapping

### Scaling Strategy
- **Replicas:** 2–3 pods
- **Rate Limiting:** Teams API rate limits (50 msg/sec per bot)
- **Card Caching:** Redis cache for frequently queried engagement summaries

---

## Cross-Cutting Concerns

### Authentication & Authorization
- **API Gateway:** JWT validation with tenant context extraction
- **Service-to-Service:** mTLS via Istio service mesh
- **RBAC Roles:** `admin`, `lead_analyst`, `analyst`, `viewer`, `api_client`
- **Tenant Isolation:** Every query includes `tenant_id` filter; enforced at ORM level

### Observability Stack
- **Metrics:** Prometheus + Grafana (per-service dashboards)
- **Logging:** Structured JSON logs → Fluentd → Elasticsearch → Kibana
- **Tracing:** OpenTelemetry → Jaeger (distributed trace correlation)
- **Alerting:** PagerDuty integration for SLA breaches and scan failures

### Data Residency & Multi-Tenancy
- **Database:** Row-level tenant isolation with `tenant_id` on every table
- **Storage:** Tenant-isolated MinIO buckets
- **Kafka:** Shared topics with tenant-id message headers for filtering
- **Encryption:** AES-256 at rest, TLS 1.3 in transit, field-level encryption for PII

### Deployment Topology
```
Zone 1 (Public):     API Gateway, Teams Bot
Zone 2 (Application): All microservices (1-4, 9-12)
Zone 3 (Scanner):    Scanner Connectors (5-8), Burp Enterprise, Nessus
Zone 4 (Data):       PostgreSQL, Elasticsearch, Redis, Kafka, MinIO, Vault
```
