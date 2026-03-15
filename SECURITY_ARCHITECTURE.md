# Security Architecture — AI-Driven VAPT Orchestration Platform

## Comprehensive Security Design for MSSP Operations at Scale (500+ Customers)

---

## 1. Security Architecture Overview

### Defense-in-Depth Layers

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                  SECURITY ZONES                                     ║
║                                                                                     ║
║  ┌── ZONE 1: DMZ (Perimeter) ──────────────────────────────────────────────────┐    ║
║  │                                                                              │    ║
║  │   CDN/WAF (Cloudflare/Shield) → Kong API Gateway → cert-manager (TLS)       │    ║
║  │                                                                              │    ║
║  │   Controls:                                                                  │    ║
║  │   • DDoS protection (L3/L4/L7)                                              │    ║
║  │   • WAF rules (OWASP CRS)                                                   │    ║
║  │   • TLS 1.3 termination                                                     │    ║
║  │   • JWT validation + tenant routing                                          │    ║
║  │   • Rate limiting (per-tenant, per-IP)                                       │    ║
║  │   • IP allowlisting (platform access tier)                                   │    ║
║  │   • Request size limiting (50MB max)                                         │    ║
║  │   • CORS enforcement                                                         │    ║
║  │                                                                              │    ║
║  └──────────────────────────────────┬───────────────────────────────────────────┘    ║
║                                      │ mTLS                                          ║
║  ┌── ZONE 2: Application Layer ─────┴──────────────────────────────────────────┐    ║
║  │                                                                              │    ║
║  │   Istio Service Mesh (Envoy sidecars) → Microservices (13 + 2 frontends)    │    ║
║  │                                                                              │    ║
║  │   Controls:                                                                  │    ║
║  │   • mTLS pod-to-pod (Istio Citadel)                                         │    ║
║  │   • RBAC enforcement per endpoint                                            │    ║
║  │   • Tenant context propagation (X-Tenant-ID)                                │    ║
║  │   • Request-level audit logging                                              │    ║
║  │   • Circuit breaker / retry policies                                         │    ║
║  │   • Pod Security Standards (restricted)                                      │    ║
║  │   • Read-only root filesystems                                               │    ║
║  │   • Non-root containers (UID 1000)                                           │    ║
║  │   • Network policies (default-deny)                                          │    ║
║  │                                                                              │    ║
║  └──────────────────────────────────┬───────────────────────────────────────────┘    ║
║                                      │                                               ║
║  ┌── ZONE 3: Scanner Execution ─────┴──────────────────────────────────────────┐    ║
║  │                                                                              │    ║
║  │   gVisor sandboxed K8s Jobs → Dedicated scan-pool nodes                      │    ║
║  │                                                                              │    ║
║  │   Controls:                                                                  │    ║
║  │   • gVisor (runsc) kernel isolation — no shared kernel syscalls              │    ║
║  │   • Per-scan resource limits (CPU: 4, Mem: 8Gi, Disk: 10Gi)                 │    ║
║  │   • 4-hour TTL hard deadline                                                 │    ║
║  │   • Egress restricted to approved scan targets only                          │    ║
║  │   • No inter-pod communication                                               │    ║
║  │   • Ephemeral storage (destroyed post-scan)                                  │    ║
║  │   • Credential access via short-lived Vault leases only                      │    ║
║  │   • Scan window enforcement                                                  │    ║
║  │   • IP allowlist validation (scan target tier)                               │    ║
║  │                                                                              │    ║
║  └──────────────────────────────────┬───────────────────────────────────────────┘    ║
║                                      │ Private subnet only                           ║
║  ┌── ZONE 4: Data Layer ────────────┴──────────────────────────────────────────┐    ║
║  │                                                                              │    ║
║  │   PostgreSQL + Elasticsearch + Kafka + Redis + MinIO                         │    ║
║  │                                                                              │    ║
║  │   Controls:                                                                  │    ║
║  │   • PostgreSQL Row-Level Security (tenant_id on every table)                 │    ║
║  │   • AES-256-GCM encryption at rest (gp3-encrypted volumes)                  │    ║
║  │   • TLS in transit for all data connections                                  │    ║
║  │   • No internet egress (data subnet isolation)                               │    ║
║  │   • MinIO tenant-isolated buckets with IAM policies                          │    ║
║  │   • Kafka tenant_id in message headers                                       │    ║
║  │   • Redis keyspace partitioned by tenant                                     │    ║
║  │   • Automated backups with PITR (PostgreSQL WAL-G)                           │    ║
║  │   • PgBouncer connection pooling (max 400)                                   │    ║
║  │                                                                              │    ║
║  └──────────────────────────────────┬───────────────────────────────────────────┘    ║
║                                      │ Authenticated access only                     ║
║  ┌── ZONE 5: Secrets Vault ─────────┴──────────────────────────────────────────┐    ║
║  │                                                                              │    ║
║  │   HashiCorp Vault HA (3-node Raft) + AWS KMS auto-unseal                    │    ║
║  │                                                                              │    ║
║  │   Controls:                                                                  │    ║
║  │   • Raft consensus storage (no external dependency)                          │    ║
║  │   • AWS KMS auto-unseal (eliminates manual unseal risk)                      │    ║
║  │   • Per-tenant Transit encryption keys (AES-256-GCM96)                       │    ║
║  │   • Time-boxed credential leases (1h default TTL)                            │    ║
║  │   • Kubernetes auth backend (pod identity)                                   │    ║
║  │   • Full audit log to immutable store                                        │    ║
║  │   • Zero-knowledge credential architecture                                   │    ║
║  │   • Key rotation on configurable schedule                                    │    ║
║  │   • Tenant key destruction on offboarding                                    │    ║
║  │                                                                              │    ║
║  └──────────────────────────────────────────────────────────────────────────────┘    ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```

### Authentication Flow

```
  User / API Client
        │
        ▼
  ┌─────────────────┐
  │ Keycloak OIDC   │  ← SAML 2.0 for analyst SSO
  │ Realm: vapt     │  ← OAuth 2.0 for customer portal
  │ MFA: enforced   │  ← API keys for service-to-service
  └────────┬────────┘
           │ JWT (RS256, 15min TTL)
           ▼
  ┌─────────────────┐     Claims:
  │ Kong Gateway    │     {
  │ JWT Validation  │       "sub": "user-uuid",
  └────────┬────────┘       "tenant_id": "t-abc123",
           │                "roles": ["lead_analyst"],
           ▼                "permissions": ["finding.validate", ...],
  ┌─────────────────┐       "mfa_verified": true,
  │ Security SVC    │       "engagement_ids": ["eng-1", "eng-2"]
  │ RBAC Enforcer   │     }
  └────────┬────────┘
           │ Validated context
           ▼
  ┌─────────────────┐
  │ Target Service  │  ← Tenant-scoped query execution
  │ (via Istio mTLS)│  ← RLS enforced at database layer
  └─────────────────┘
```

---

## 2. Role-Based Access Control (RBAC)

### 2.1 Role Hierarchy

```
  platform_admin ──────────────── Full system access (cross-tenant)
       │
       ├── tenant_admin ──────── Manage users, config, credentials for one tenant
       │       │
       │       ├── engagement_manager ── Create/close engagements, manage scan windows
       │       │       │
       │       │       ├── lead_analyst ── Approve reports, validate findings, escalate
       │       │       │       │
       │       │       │       └── analyst ── Triage, validate, draft reports
       │       │       │
       │       │       └── scanner_operator ── Launch scans, checkout credentials
       │       │
       │       └── customer_admin ── Manage own credentials, view reports
       │               │
       │               └── customer_viewer ── Read-only access to reports/findings
       │
       └── (service accounts) ── Machine-to-machine with scoped permissions
```

### 2.2 Permission Matrix

| Permission | platform_admin | tenant_admin | engagement_mgr | lead_analyst | analyst | scanner_op | customer_admin | customer_viewer |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Engagement** | | | | | | | | |
| engagement.create | ● | ● | ● | | | | ● | |
| engagement.read | ● | ● | ● | ● | ● | ● | ● | ● |
| engagement.update | ● | ● | ● | ● | | | | |
| engagement.delete | ● | | | | | | | |
| engagement.close | ● | ● | ● | | | | | |
| **Scan** | | | | | | | | |
| scan.launch | ● | ● | ● | ● | ● | ● | | |
| scan.read | ● | ● | ● | ● | ● | ● | | |
| scan.cancel | ● | ● | ● | ● | | ● | | |
| scan.configure | ● | ● | ● | | | ● | | |
| **Finding** | | | | | | | | |
| finding.read | ● | ● | ● | ● | ● | ● | ● | ● |
| finding.update | ● | | | ● | ● | | | |
| finding.validate | ● | | | ● | ● | | | |
| finding.triage | ● | | | ● | ● | | | |
| finding.export | ● | ● | ● | ● | | | ● | |
| **Report** | | | | | | | | |
| report.create | ● | ● | ● | ● | ● | | | |
| report.read | ● | ● | ● | ● | ● | | ● | ● |
| report.approve | ● | ● | ● | ● | | | | |
| report.deliver | ● | ● | ● | ● | | | | |
| report.download | ● | ● | ● | ● | ● | | ● | ● |
| **Credential** | | | | | | | | |
| credential.create | ● | ● | ● | | | | ● | |
| credential.read_metadata | ● | ● | ● | ● | ● | ● | ● | |
| credential.checkout | ● | | | | | ● | | |
| credential.rotate | ● | ● | | | | | ● | |
| credential.delete | ● | ● | | | | | ● | |
| **Admin** | | | | | | | | |
| admin.manage_users | ● | ● | | | | | | |
| admin.manage_tenants | ● | | | | | | | |
| admin.view_audit_logs | ● | ● | | | | | | |
| admin.manage_ip_allowlist | ● | ● | | | | | ● | |
| admin.manage_scan_windows | ● | ● | ● | | | | | |
| admin.emergency_override | ● | | | | | | | |
| **AI** | | | | | | | | |
| ai.analyze | ● | ● | ● | ● | ● | | | |
| ai.draft_report | ● | ● | ● | ● | ● | | | |

### 2.3 Attribute-Based Access Control (ABAC) Conditions

| Attribute | Description | Enforcement Point |
|-----------|-------------|-------------------|
| `tenant_id` | User can only access resources in their own tenant | Every API call, every DB query (RLS) |
| `engagement_ids` | Analysts can only access assigned engagements | API middleware for analyst/lead_analyst roles |
| `mfa_verified` | Sensitive operations require MFA | credential.checkout, credential.delete, report.deliver, admin.emergency_override, admin.manage_tenants, engagement.delete |
| `source_ip` | Requests must come from allowlisted IPs | Kong gateway (platform_access allowlist) |
| `time_of_day` | Scan operations restricted to scan windows | Scan orchestrator, scanner connectors |
| `data_classification` | Access to critical data requires elevated clearance | Vault policies for credential access |

### 2.4 Keycloak Realm Configuration

```
Realm: vapt
├── Clients
│   ├── analyst-portal (OIDC, PKCE, redirect: https://analyst.vapt-platform.com/*)
│   ├── customer-portal (OIDC, PKCE, redirect: https://portal.vapt-platform.com/*)
│   ├── vapt-platform (confidential, service-to-service)
│   └── admin-cli (for realm management)
├── Roles
│   ├── Realm roles: platform_admin, tenant_admin, engagement_manager,
│   │                lead_analyst, analyst, scanner_operator,
│   │                customer_admin, customer_viewer
│   └── Client roles: (per-client scoped permissions)
├── Groups (per-tenant)
│   ├── /tenants/{tenant_id}/admins
│   ├── /tenants/{tenant_id}/analysts
│   ├── /tenants/{tenant_id}/operators
│   └── /tenants/{tenant_id}/customers
├── Authentication Flows
│   ├── Browser: username/password → MFA (TOTP/WebAuthn) → consent
│   ├── API: client_credentials or direct_grant with MFA
│   └── Service: client_credentials (mTLS certificate)
├── Identity Providers
│   ├── Corporate SAML 2.0 (per-tenant SSO federation)
│   └── Azure AD / Okta (optional OIDC federation)
└── Mappers
    ├── tenant_id → from group path (/tenants/{tenant_id}/*)
    ├── roles → aggregate realm + client roles
    ├── engagement_ids → from user attribute
    └── mfa_verified → from authentication context
```

---

## 3. Credential Isolation

### 3.1 Zero-Knowledge Architecture

```
  Customer                    Platform                      Vault
  ────────                    ────────                      ─────

  1. Generate keypair (libsodium X25519)
     │
  2. Encrypt credentials client-side
     │  ┌──────────────────────────┐
     │  │ NaCl secretbox:          │
     │  │   nonce + ciphertext     │
     │  │   (only customer has key)│
     │  └────────────┬─────────────┘
     │               │
  3. Submit encrypted ─────────────►  4. Wrap with Transit engine
     blob via TLS 1.3                    ┌────────────────────────┐
                                         │ Vault Transit:         │
                                         │   key = tenant-{id}    │
                                         │   algo = AES-256-GCM96 │
                                         └────────────┬───────────┘
                                                       │
                                      5. Store in KV v2 ──────► credentials/{tenant}/{eng}/{id}
                                                                  double-encrypted blob


  Scanner Worker              Platform                      Vault
  ──────────────              ────────                      ─────

  6. Request checkout ──────►  7. Verify:
     (mTLS + pod identity)       • engagement scope match
                                 • scan window active
                                 • credential.checkout permission
                                 • MFA verified
                                        │
                              8. Fetch from KV ──────────►  9. Return wrapped secret
                                        │                       (1h lease TTL)
                              10. Decrypt Transit layer
                                        │
                              11. Return client-encrypted ───► 12. Scanner decrypts
                                  blob to scanner                  with engagement key
                                  (never plaintext                 (provided at scan config)
                                   on platform)

  INVARIANT: Platform operators NEVER see plaintext credentials.
  Vault Transit key is managed by Vault — not extractable.
  Client-side key is held by customer — not stored on platform.
```

### 3.2 Credential Lifecycle

| Stage | Action | Security Control |
|-------|--------|------------------|
| **Submission** | Customer encrypts with libsodium, submits via TLS | Client-side encryption, TLS 1.3 |
| **Storage** | Vault Transit wraps blob, stores in KV v2 | Double encryption, per-tenant Transit key |
| **Checkout** | Scanner requests via mTLS, gets time-boxed lease | Pod identity, engagement scope, 1h TTL |
| **Usage** | Scanner decrypts and uses for target auth | Ephemeral container, destroyed post-scan |
| **Checkin** | Explicit checkin or lease auto-expires | Vault lease revocation |
| **Rotation** | Customer submits new encrypted blob | Old versions retained in KV v2 history |
| **Deletion** | All versions permanently destroyed in Vault | `delete_metadata_and_all_versions` |
| **Offboarding** | Per-tenant Transit key destroyed | Renders all stored credentials unrecoverable |

### 3.3 Vault Policies

```hcl
# Scanner worker policy — can ONLY checkout credentials
path "secret/data/credentials/{{identity.entity.aliases.kubernetes.metadata.tenant_id}}/*" {
  capabilities = ["read"]
}

# Analyst policy — can view metadata only (no secret data)
path "secret/metadata/credentials/{{identity.entity.aliases.kubernetes.metadata.tenant_id}}/*" {
  capabilities = ["read", "list"]
}

# Tenant admin policy — full credential management
path "secret/data/credentials/{{identity.entity.aliases.kubernetes.metadata.tenant_id}}/*" {
  capabilities = ["create", "read", "update", "delete"]
}
path "secret/metadata/credentials/{{identity.entity.aliases.kubernetes.metadata.tenant_id}}/*" {
  capabilities = ["read", "list", "delete"]
}

# Transit policy — encryption/decryption scoped to tenant key
path "transit/encrypt/tenant-{{identity.entity.aliases.kubernetes.metadata.tenant_id}}" {
  capabilities = ["update"]
}
path "transit/decrypt/tenant-{{identity.entity.aliases.kubernetes.metadata.tenant_id}}" {
  capabilities = ["update"]
}
```

---

## 4. Tenant Isolation

### 4.1 Six-Layer Isolation Model

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                        TENANT ISOLATION LAYERS                          │
  │                                                                         │
  │  Layer 1: API GATEWAY                                                   │
  │  ┌───────────────────────────────────────────────────────────────────┐  │
  │  │ • tenant_id extracted from JWT claims                            │  │
  │  │ • X-Tenant-ID header propagated to all downstream services       │  │
  │  │ • Rate limiting per tenant (600 req/min)                         │  │
  │  │ • Request routing by tenant configuration                        │  │
  │  └───────────────────────────────────────────────────────────────────┘  │
  │                                                                         │
  │  Layer 2: APPLICATION                                                   │
  │  ┌───────────────────────────────────────────────────────────────────┐  │
  │  │ • TenantIsolationMiddleware validates tenant context on every req │  │
  │  │ • RBAC enforcer checks tenant boundary before permission grant   │  │
  │  │ • Service-to-service calls carry X-Tenant-ID header              │  │
  │  │ • Audit log records tenant context for every operation           │  │
  │  └───────────────────────────────────────────────────────────────────┘  │
  │                                                                         │
  │  Layer 3: DATABASE (PostgreSQL RLS)                                     │
  │  ┌───────────────────────────────────────────────────────────────────┐  │
  │  │ • Every table has tenant_id UUID NOT NULL column                 │  │
  │  │ • ROW LEVEL SECURITY enabled + forced on all tables              │  │
  │  │ • SET LOCAL app.current_tenant_id at transaction start           │  │
  │  │ • Indexes: tenant_id as first column for efficient isolation     │  │
  │  │ • Platform admin bypass via separate database role               │  │
  │  └───────────────────────────────────────────────────────────────────┘  │
  │                                                                         │
  │  Layer 4: OBJECT STORAGE (MinIO)                                        │
  │  ┌───────────────────────────────────────────────────────────────────┐  │
  │  │ • Tenant-isolated bucket prefixes: {bucket}/{tenant_id}/...      │  │
  │  │ • Pre-signed URLs scoped to tenant prefix only                   │  │
  │  │ • IAM policies prevent cross-tenant bucket access                │  │
  │  │ • Server-side encryption (SSE-S3) per object                     │  │
  │  └───────────────────────────────────────────────────────────────────┘  │
  │                                                                         │
  │  Layer 5: MESSAGE QUEUE (Kafka)                                         │
  │  ┌───────────────────────────────────────────────────────────────────┐  │
  │  │ • tenant_id in Kafka message headers                             │  │
  │  │ • Consumer group filtering by tenant_id                          │  │
  │  │ • Topic partitioning includes tenant_id in key                   │  │
  │  │ • No inter-tenant message visibility                             │  │
  │  └───────────────────────────────────────────────────────────────────┘  │
  │                                                                         │
  │  Layer 6: ENCRYPTION                                                    │
  │  ┌───────────────────────────────────────────────────────────────────┐  │
  │  │ • Per-tenant Transit encryption keys in Vault                    │  │
  │  │ • Key rotation on configurable schedule                          │  │
  │  │ • Tenant key destruction on offboarding (crypto-shredding)       │  │
  │  │ • All sensitive data encrypted with tenant-specific key          │  │
  │  └───────────────────────────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 PostgreSQL RLS Policy Definitions

```sql
-- Enable RLS on all tenant-scoped tables
ALTER TABLE engagements ENABLE ROW LEVEL SECURITY;
ALTER TABLE engagements FORCE ROW LEVEL SECURITY;

-- Tenant isolation policy (applied to every table)
CREATE POLICY tenant_isolation_engagements ON engagements
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Platform admin bypass (separate DB role)
CREATE POLICY platform_admin_bypass ON engagements
    TO vapt_admin
    USING (true) WITH CHECK (true);

-- Applied to: engagements, scans, findings, reports, credentials,
-- work_items, assets, audit_events, scan_windows, ip_allowlists
-- (10 tables total)
```

### 4.3 Tenant Onboarding / Offboarding

| Phase | Security Actions |
|-------|------------------|
| **Onboarding** | Create Keycloak group `/tenants/{id}`, Vault Transit key `tenant-{id}`, MinIO bucket prefix, PostgreSQL schema verification, IP allowlist seed |
| **Offboarding** | Destroy Vault Transit key (crypto-shredding), purge MinIO bucket, cascade-delete database records, revoke all Keycloak sessions, archive audit logs to cold storage |

---

## 5. Audit Logging

### 5.1 Audit Event Taxonomy (50+ Event Types)

| Category | Events |
|----------|--------|
| **auth** | login_success, login_failure, logout, token_refresh, mfa_challenge, mfa_success, mfa_failure, api_key_created, api_key_revoked, session_expired |
| **access** | permission_denied, resource_accessed, bulk_export, report_downloaded, api_rate_limited |
| **data** | finding_created, finding_updated, finding_deleted, severity_overridden, evidence_uploaded, evidence_deleted |
| **scan** | launched, completed, failed, cancelled, window_violation, emergency_override, scope_modified, target_added, target_removed |
| **report** | generated, submitted_for_review, approved, rejected, delivered, downloaded, regenerated |
| **credential** | created, checkout, checkin, rotated, expired, deleted, access_denied |
| **admin** | user_created, user_deactivated, role_assigned, role_revoked, tenant_created, tenant_suspended, tenant_offboarded, ip_allowlist_updated, scan_window_updated, emergency_scan_override, config_changed |
| **security** | cross_tenant_attempt, ip_denied, brute_force_detected, anomalous_access_pattern, credential_exposure_detected, container_escape_attempt, privilege_escalation_attempt |

### 5.2 Audit Log Pipeline

```
  Application Pods
       │
       │ AuditLogger.log()
       ▼
  ┌──────────────┐
  │ Kafka Topic  │  audit.events (partitioned by tenant_id)
  │ (acks=all,   │  exactly-once semantics (idempotent producer)
  │  RF=3)       │
  └──────┬───────┘
         │
    ┌────┴────┐
    ▼         ▼
  ┌────────┐ ┌──────────┐
  │ Elastic │ │ S3 WORM  │  Write-Once-Read-Many (Object Lock)
  │ Search  │ │ Archive  │  7-year retention for compliance
  │ (30d    │ └──────────┘
  │  hot)   │
  └────────┘
```

### 5.3 Audit Log Schema

```json
{
  "id": "evt-550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-03-15T10:30:00.000Z",
  "category": "credential",
  "action": "credential.checkout",
  "actor_id": "usr-abc123",
  "actor_email": "analyst@mssp.com",
  "actor_roles": ["scanner_operator"],
  "tenant_id": "t-def456",
  "resource_type": "credential",
  "resource_id": "cred-789",
  "engagement_id": "eng-012",
  "source_ip": "10.0.1.50",
  "user_agent": "scan-orchestrator/1.0",
  "result": "success",
  "reason": "",
  "metadata": {
    "scan_job_id": "job-345",
    "lease_ttl": 3600,
    "pod_name": "burp-connector-abc-xyz"
  },
  "previous_hash": "a1b2c3d4e5f6...",
  "event_hash": "f6e5d4c3b2a1..."
}
```

### 5.4 Hash Chain Tamper Detection

Each audit event includes a SHA-256 hash computed over its canonical fields concatenated with the previous event's hash, forming a blockchain-like chain. Any modification to a historical event breaks the chain, which is detectable via `AuditLogger.verify_chain()`.

```
  Event 0          Event 1          Event 2          Event 3
  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
  │ GENESIS  │────►│ hash_0   │────►│ hash_1   │────►│ hash_2   │
  │          │     │ prev=GEN │     │ prev=h_0 │     │ prev=h_1 │
  │ hash=h_0 │     │ hash=h_1 │     │ hash=h_2 │     │ hash=h_3 │
  └──────────┘     └──────────┘     └──────────┘     └──────────┘

  Tamper event 1 → recompute hash ≠ h_1 → CHAIN BROKEN → ALERT
```

### 5.5 Retention Policy

| Tier | Storage | Duration | Access |
|------|---------|----------|--------|
| Hot | Elasticsearch (SSD) | 7 days | Full-text search, real-time dashboards |
| Warm | Elasticsearch (S3 backed) | 30 days | Indexed label queries |
| Cold | S3 Intelligent-Tiering | 365 days | Compliance archive |
| Deep Archive | S3 Glacier + Object Lock | 7 years | Forensics, regulatory audit |

---

## 6. Scan Window Restrictions

### 6.1 Scan Window Data Model

```
ScanWindow {
  id:              UUID
  tenant_id:       UUID
  engagement_id:   UUID
  name:            "Business Hours Only"
  timezone:        "America/New_York"
  allowed_days:    [monday, tuesday, wednesday, thursday, friday]
  start_time:      09:00
  end_time:        18:00
  blackout_dates:  ["2026-12-25", "2026-01-01"]
  effective_from:  2026-03-01T00:00:00Z
  effective_until: 2026-04-30T23:59:59Z
  is_active:       true
}
```

### 6.2 Enforcement Points

```
  scan.launch request
       │
       ▼
  ┌─────────────────────────────┐
  │ 1. API Validation           │  ScanWindowEnforcer.check_window()
  │    Reject if outside window │  ← Returns ScanWindowCheckResult
  └──────────────┬──────────────┘
                 │ (if allowed)
                 ▼
  ┌─────────────────────────────┐
  │ 2. Temporal Workflow Guard  │  Check again before dispatching
  │    Re-verify at dispatch    │  (handles queue delay)
  └──────────────┬──────────────┘
                 │
                 ▼
  ┌─────────────────────────────┐
  │ 3. Connector Pre-Check      │  Verify just before scanner starts
  │    Last-chance verification │
  └──────────────┬──────────────┘
                 │
                 ▼
  ┌─────────────────────────────┐
  │ 4. Periodic Watchdog        │  Every 5 minutes:
  │    Suspend running scans    │  - Check all active scans
  │    when window closes       │  - Suspend if window expired
  └─────────────────────────────┘
```

### 6.3 Emergency Override

Requires **dual-approval** (two distinct approvers, neither of whom is the requestor):

```
  Requestor                Approver 1             Approver 2
  ─────────                ──────────             ──────────
  Submit override ────────► Review justification
  request with              │
  justification             Approve ──────────────► Review
                                                    │
                                                    Approve
                                                       │
                                                       ▼
                                              Override granted
                                              (4h default TTL)
                                              Audit logged as
                                              admin.emergency_scan_override
```

---

## 7. IP Allowlisting

### 7.1 Three-Tier Allowlist Architecture

```
  ┌──────────────────────────────────────────────────────────────────┐
  │                    IP ALLOWLIST TIERS                             │
  │                                                                  │
  │  TIER 1: PLATFORM ACCESS                                         │
  │  ┌────────────────────────────────────────────────────────────┐  │
  │  │ Who:   Analyst/admin workstation IPs                       │  │
  │  │ Where: Kong Gateway (ingress)                              │  │
  │  │ Scope: Per-tenant (allowlist shared across engagements)    │  │
  │  │ Example: 203.0.113.0/24 (MSSP office), 198.51.100.5/32   │  │
  │  └────────────────────────────────────────────────────────────┘  │
  │                                                                  │
  │  TIER 2: SCAN SOURCE                                             │
  │  ┌────────────────────────────────────────────────────────────┐  │
  │  │ Who:   Scanner egress NAT IPs (for customer firewall rules)│  │
  │  │ Where: Displayed to customer for their firewall allowlist  │  │
  │  │ Scope: Per-tenant or shared pool                           │  │
  │  │ Mode:  shared_pool (default) or dedicated_nat (premium)    │  │
  │  │ Example: 52.10.20.0/28 (scanner NAT pool)                 │  │
  │  └────────────────────────────────────────────────────────────┘  │
  │                                                                  │
  │  TIER 3: SCAN TARGET                                             │
  │  ┌────────────────────────────────────────────────────────────┐  │
  │  │ Who:   Customer-approved scan target CIDRs                 │  │
  │  │ Where: Scanner connector (pre-scan validation)             │  │
  │  │ Scope: Per-engagement (strict scope enforcement)           │  │
  │  │ Example: 10.0.0.0/16 (customer internal), *.example.com   │  │
  │  │ Validation: Scanner MUST verify target IP is in allowlist  │  │
  │  │             BEFORE sending any traffic                     │  │
  │  └────────────────────────────────────────────────────────────┘  │
  └──────────────────────────────────────────────────────────────────┘
```

### 7.2 Features

- IPv4 and IPv6 CIDR support
- Maximum 500 entries per tenant
- Per-engagement scoping for scan targets
- Tenant-wide entries apply to all engagements
- Expiration dates for time-limited access
- Duplicate detection and normalization
- Bulk target validation API

---

## 8. Threat Model (STRIDE)

### 8.1 Data Flow Diagram

```
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║                               DATA FLOW DIAGRAM (Level 1)                               ║
║                                                                                         ║
║   ┌───────────┐                                                     ┌───────────┐       ║
║   │ Analyst   │                                                     │ Customer  │       ║
║   │ (Browser) │                                                     │ (Browser) │       ║
║   └─────┬─────┘                                                     └─────┬─────┘       ║
║         │ HTTPS                                                           │ HTTPS       ║
║         │                                                                 │              ║
║   ══════╪═════════════════ TRUST BOUNDARY: INTERNET ══════════════════════╪═══════       ║
║         │                                                                 │              ║
║         ▼                                                                 ▼              ║
║   ┌───────────────────────────────────────────────────────────────────────────────┐     ║
║   │                      [P1] API GATEWAY (Kong)                                  │     ║
║   │                      JWT validation, rate limiting, IP check                  │     ║
║   └───────────────────────────────────┬───────────────────────────────────────────┘     ║
║                                        │                                                 ║
║   ═════════════════════ TRUST BOUNDARY: SERVICE MESH (mTLS) ═════════════════════       ║
║                                        │                                                 ║
║         ┌──────────────────────────────┼────────────────────────────────┐                ║
║         ▼                              ▼                                ▼                ║
║   ┌──────────────┐   ┌────────────────────────┐   ┌──────────────────────────┐          ║
║   │ [P2] Auth    │   │ [P3] Core Services     │   │ [P4] AI Analyst          │          ║
║   │ (Keycloak)   │   │ (Engagement, Findings, │   │ (Claude API calls)       │          ║
║   │              │   │  Analyst Workflow)       │   │                          │          ║
║   └──────────────┘   └────────────┬────────────┘   └──────────┬───────────────┘          ║
║                                    │                            │                         ║
║                          ┌─────────┴──────────┐                │                         ║
║                          ▼                     ▼                ▼                         ║
║   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               ║
║   │ [D1] PostgreSQL│ │ [D2] Elastic │ │ [D3] Kafka   │ │ [D4] Redis   │               ║
║   │ (RLS enabled) │  │ Search       │  │ (events)     │  │ (cache)      │               ║
║   └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘               ║
║                                                                                         ║
║   ═════════════════════ TRUST BOUNDARY: DATA SUBNET ════════════════════════════        ║
║                                                                                         ║
║   ┌──────────────┐  ┌──────────────┐                                                   ║
║   │ [D5] Vault   │  │ [D6] MinIO   │                                                   ║
║   │ (secrets)    │  │ (files)      │                                                   ║
║   └──────────────┘  └──────────────┘                                                   ║
║                                                                                         ║
║   ═════════════════════ TRUST BOUNDARY: SCANNER ZONE ═══════════════════════════        ║
║                                                                                         ║
║   ┌──────────────────────────────────────────────────────────────────────────────┐      ║
║   │ [P5] Scanner Connectors → [P6] gVisor Sandbox Jobs                          │      ║
║   │      (Burp, Tenable, Fortify, Mobile)                                        │      ║
║   └──────────────────────────────────┬───────────────────────────────────────────┘      ║
║                                       │                                                  ║
║   ════════════════════ TRUST BOUNDARY: EXTERNAL TARGETS ════════════════════════        ║
║                                       ▼                                                  ║
║                              ┌─────────────────┐                                        ║
║                              │ Customer Targets │                                        ║
║                              │ (external)       │                                        ║
║                              └─────────────────┘                                        ║
╚══════════════════════════════════════════════════════════════════════════════════════════╝
```

### 8.2 STRIDE Threat Analysis

#### SPOOFING

| ID | Threat | Component | Risk | Mitigation |
|----|--------|-----------|------|------------|
| T-S01 | Forged JWT tokens bypass authentication | P1: API Gateway | **Critical** | RS256 asymmetric signing, JWKS endpoint validation, short TTL (15min), token refresh via Keycloak |
| T-S02 | Tenant impersonation via manipulated tenant_id claims | P1, P3 | **Critical** | tenant_id from signed JWT only (not user input), Keycloak-controlled claim, X-Tenant-ID header cross-checked against JWT |
| T-S03 | Service impersonation in mesh (rogue pod) | P3: Services | **High** | Istio mTLS with Citadel-managed certificates, Kyverno image registry allowlist, network policies restrict pod communication |
| T-S04 | Scanner credential theft enables unauthorized target access | P5, P6 | **Critical** | Time-boxed Vault leases (1h), ephemeral containers (destroyed post-scan), gVisor kernel isolation, credential checkout audit trail |

#### TAMPERING

| ID | Threat | Component | Risk | Mitigation |
|----|--------|-----------|------|------------|
| T-T01 | Finding severity manipulation by compromised analyst account | P3: Findings | **High** | Severity override requires justification, four-eyes principle on report approval, audit log of all severity changes, finding snapshot in report record |
| T-T02 | Report content modification between generation and delivery | D6: MinIO | **High** | SHA-256 file hash stored in report record, hash verified on download, MinIO object immutability during approval window |
| T-T03 | Scan configuration tampering to expand scope beyond authorization | P5: Scanner | **Critical** | Scan target IP allowlist enforcement (Tier 3), scan window restrictions, scope locked to engagement definition, egress network policy |
| T-T04 | Audit log manipulation to hide malicious activity | D3: Kafka, D2: ES | **Critical** | SHA-256 hash chain (tamper-evident), Kafka acks=all with 3x replication, S3 WORM (Object Lock) for long-term storage, separate audit DB role |

#### REPUDIATION

| ID | Threat | Component | Risk | Mitigation |
|----|--------|-----------|------|------------|
| T-R01 | Analyst denies approving a report that was published | P3: Reports | **High** | Immutable audit log with actor_id, timestamp, and hash chain; report.approved event contains approver identity; four-eyes principle with separate approver/generator |
| T-R02 | Scanner operator denies launching an unauthorized scan | P5: Scanner | **High** | scan.launched audit event with actor, IP, user-agent; scan window check recorded; credential checkout trail links scan to operator |
| T-R03 | Customer disputes finding was reported | P3: Findings | **Medium** | Finding creation timestamp, evidence chain with screenshots, finding snapshot in delivered report, signed report hash |

#### INFORMATION DISCLOSURE

| ID | Threat | Component | Risk | Mitigation |
|----|--------|-----------|------|------------|
| T-I01 | Cross-tenant data leakage via SQL injection bypassing RLS | D1: PostgreSQL | **Critical** | Parameterized queries (SQLAlchemy ORM), RLS FORCE enabled (even table owners), separate DB roles, WAF SQL injection rules |
| T-I02 | Scan results from tenant A visible to tenant B | D1, D6 | **Critical** | 6-layer tenant isolation model, RLS on every table, MinIO bucket-level isolation, Kafka consumer tenant filtering |
| T-I03 | Credential exposure in logs, errors, or stack traces | All services | **Critical** | Zero-knowledge architecture (plaintext never on platform), structured logging with redaction, error response sanitization, no credential data in env vars |
| T-I04 | AI model prompt injection leaking other tenant findings | P4: AI Analyst | **High** | Per-request prompt construction with only current tenant data, no persistent context across tenants, output validated before storage, AI response tagged as pending_review |
| T-I05 | MinIO pre-signed URL enumeration | D6: MinIO | **Medium** | UUID-based paths (not guessable), 15-minute TTL on URLs, tenant prefix in path, URL generation requires RBAC check |

#### DENIAL OF SERVICE

| ID | Threat | Component | Risk | Mitigation |
|----|--------|-----------|------|------------|
| T-D01 | Resource exhaustion via unbounded scan requests | P5: Scanner | **High** | Per-tenant concurrent scan limit, global limit (100 concurrent), Karpenter node scaling limits (30 max), scan queue with priority system |
| T-D02 | Kafka topic flooding causing pipeline backlog | D3: Kafka | **High** | Producer rate limiting, message size limit (10MB), consumer lag alerting (>5000), topic partition limits, dead letter queue |
| T-D03 | PDF generation bomb (malicious template data) | Reporting Service | **Medium** | Render timeout (120s), memory limit (4Gi), input validation on data bundle, page count limits |
| T-D04 | API rate limit bypass via distributed requests | P1: Gateway | **High** | Tenant-based rate limiting (not just IP), Redis-backed distributed counter, adaptive rate limiting, WAF behavioral analysis |

#### ELEVATION OF PRIVILEGE

| ID | Threat | Component | Risk | Mitigation |
|----|--------|-----------|------|------------|
| T-E01 | Analyst escalates to lead_analyst by modifying JWT | P1, P2 | **Critical** | RS256 asymmetric signing (private key in Keycloak only), JWT signature verification at gateway, role claims from Keycloak (not user-editable) |
| T-E02 | Scanner pod container escape to host | P6: Scanner | **Critical** | gVisor (runsc) kernel-level isolation, no host network/PID/IPC, read-only root filesystem, seccomp RuntimeDefault, Falco runtime detection |
| T-E03 | Service account token theft for lateral movement | P3: Services | **High** | Automounted SA tokens disabled for most pods, Istio mTLS for service identity, network policies restrict movement, token TTL (1h) |
| T-E04 | SSRF via scanner connecting to internal services | P5, P6 | **Critical** | Egress network policy: scanner can ONLY reach approved targets (Tier 3 allowlist), deny access to cluster CIDR, metadata endpoint blocked (169.254.169.254) |

### 8.3 Risk Matrix

```
                              IMPACT
              │  Negligible │   Low    │  Medium  │   High   │ Critical │
  ────────────┼─────────────┼──────────┼──────────┼──────────┼──────────┤
  Almost      │             │          │          │ T-D02    │ T-I01    │
  Certain     │             │          │          │ T-D04    │          │
  ────────────┼─────────────┼──────────┼──────────┼──────────┼──────────┤
  Likely      │             │          │ T-D03    │ T-T01    │ T-S01    │
              │             │          │ T-I05    │ T-I04    │ T-S02    │
  ────────────┼─────────────┼──────────┼──────────┼──────────┼──────────┤
  Possible    │             │          │ T-R03    │ T-S03    │ T-T03    │
              │             │          │          │ T-T02    │ T-E04    │
              │             │          │          │ T-R01    │ T-I03    │
  L           │             │          │          │ T-R02    │          │
  I ──────────┼─────────────┼──────────┼──────────┼──────────┼──────────┤
  K Unlikely  │             │          │          │ T-D01    │ T-S04    │
  E           │             │          │          │ T-E03    │ T-E01    │
  L           │             │          │          │          │ T-I02    │
  I ──────────┼─────────────┼──────────┼──────────┼──────────┼──────────┤
  H Rare      │             │          │          │ T-T04    │ T-E02    │
  O           │             │          │          │          │          │
  O           │             │          │          │          │          │
  D           │             │          │          │          │          │
  ────────────┴─────────────┴──────────┴──────────┴──────────┴──────────┘
```

---

## 9. Security Monitoring & Incident Response

### 9.1 Security-Specific Prometheus Alerts

```yaml
# Critical — PagerDuty immediate
- VaultSealed: vault_core_unsealed == 0
- CrossTenantAccess: vapt_cross_tenant_attempts_total increase > 0
- BruteForceDetected: vapt_auth_failures_total rate > 10/min per IP
- CredentialExposure: vapt_credential_exposure_detected > 0
- ContainerEscape: falco_alerts{rule="container_escape"} > 0
- PrivilegeEscalation: falco_alerts{rule="privilege_escalation"} > 0
- AuditChainBroken: vapt_audit_chain_verification_failures > 0
- RLSBypassAttempt: vapt_rls_bypass_attempts_total > 0

# Warning — Slack business hours
- HighAuthFailureRate: vapt_auth_failures_total rate > 5/min per tenant
- ScanWindowViolation: vapt_scan_window_violations_total increase > 0
- IPDenied: vapt_ip_denied_total rate > 20/min
- UnusualDataExport: vapt_data_export_size_bytes > 100MB single request
- ServiceAccountAnomalous: vapt_sa_token_usage outside normal patterns
- CertificateExpiry: cert expiry < 14 days
- VaultLeaseExpiry: active Vault leases > 100 per tenant
```

### 9.2 Incident Severity Classification

| Severity | Definition | Example | Response Time |
|----------|-----------|---------|---------------|
| **SEV-1** | Active data breach or complete service compromise | Cross-tenant data exposure, credential theft | 15 minutes |
| **SEV-2** | Security control failure with potential for breach | RLS bypass, Vault sealed, audit chain broken | 1 hour |
| **SEV-3** | Suspicious activity requiring investigation | Brute force, unusual access patterns, scan window violations | 4 hours |
| **SEV-4** | Security configuration issue or minor policy violation | IP allowlist misconfiguration, expired certificate | 24 hours |

### 9.3 Incident Response Runbook Outline

1. **Detect** — Alert fires via Prometheus/Falco → PagerDuty/Slack
2. **Triage** — On-call determines severity, assembles response team
3. **Contain** — Isolate affected tenant/service (network policy, Keycloak session revocation)
4. **Investigate** — Query audit logs (Elasticsearch), trace requests (Tempo), review Falco events
5. **Remediate** — Patch vulnerability, rotate credentials, update allowlists
6. **Recover** — Restore service, verify tenant isolation, re-enable access
7. **Post-mortem** — Root cause analysis, update threat model, improve controls

---

## 10. Compliance Mapping

| Security Control | SOC 2 (CC) | ISO 27001 (A) | PCI DSS 4.0 | GDPR |
|-----------------|-----------|---------------|-------------|------|
| RBAC with least privilege | CC6.1, CC6.3 | A.9.1, A.9.2 | 7.1, 7.2 | Art. 25 (data protection by design) |
| MFA enforcement | CC6.1 | A.9.4.2 | 8.3 | Art. 32 (security of processing) |
| Tenant isolation (RLS) | CC6.1, CC6.3 | A.9.4.1 | 7.2.1 | Art. 25, Art. 32 |
| Encryption at rest | CC6.1, CC6.7 | A.10.1.1 | 3.4, 3.5 | Art. 32(1)(a) |
| Encryption in transit | CC6.1, CC6.7 | A.10.1.1 | 4.1 | Art. 32(1)(a) |
| Audit logging (7yr) | CC7.2, CC7.3 | A.12.4.1 | 10.1, 10.2 | Art. 30 (records of processing) |
| Tamper-evident audit | CC7.2 | A.12.4.2 | 10.5 | Art. 5(1)(f) (integrity) |
| Credential isolation | CC6.1 | A.9.2.4, A.10.1 | 3.6, 8.2 | Art. 32 |
| Scan window restrictions | CC6.1 | A.12.1.2 | 11.4.1 | Art. 25 |
| IP allowlisting | CC6.1, CC6.6 | A.9.4.1, A.13.1 | 1.3 | Art. 32 |
| Network policies (default-deny) | CC6.6 | A.13.1.1 | 1.2, 1.3 | Art. 32 |
| Vulnerability management | CC7.1 | A.12.6.1 | 6.1, 6.2 | Art. 32 |
| Incident response | CC7.3, CC7.4 | A.16.1 | 12.10 | Art. 33 (breach notification) |
| Data retention/deletion | CC6.5 | A.8.3.2 | 3.1 | Art. 17 (right to erasure) |
| Container security (gVisor) | CC6.1 | A.12.1.4 | 6.2 | Art. 32 |
| Secret management (Vault) | CC6.1 | A.10.1.2 | 3.5, 3.6 | Art. 32 |
