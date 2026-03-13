-- ============================================================================
-- AI-Driven VAPT Orchestration Platform — PostgreSQL Database Schema
-- ============================================================================
-- Multi-tenant MSSP architecture supporting 500+ customers
-- PostgreSQL 16 with Row-Level Security (RLS) for tenant isolation
-- ============================================================================

-- ============================================================================
-- 0. EXTENSIONS & ENUMS
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";       -- trigram fuzzy search
CREATE EXTENSION IF NOT EXISTS "btree_gist";    -- exclusion constraints

-- ----------------------------------------------------------------------------
-- Enum Types — centralised so every table references a consistent vocabulary
-- ----------------------------------------------------------------------------

CREATE TYPE engagement_status AS ENUM (
    'draft', 'scoping', 'pending_approval', 'approved',
    'in_progress', 'review', 'closed', 'cancelled'
);

CREATE TYPE engagement_type AS ENUM (
    'full_vapt', 'web_only', 'infra_only', 'mobile_only',
    'api_only', 'cloud_only', 'compliance_audit', 'retest'
);

CREATE TYPE priority_level AS ENUM ('critical', 'high', 'medium', 'low');

CREATE TYPE asset_type AS ENUM (
    'web_application', 'api_endpoint', 'host', 'network_range',
    'mobile_app_android', 'mobile_app_ios', 'cloud_resource',
    'container_image', 'domain', 'wireless_network'
);

CREATE TYPE asset_environment AS ENUM (
    'production', 'staging', 'development', 'qa', 'dr'
);

CREATE TYPE target_protocol AS ENUM (
    'http', 'https', 'ssh', 'rdp', 'smb', 'ftp', 'snmp',
    'tcp_custom', 'udp_custom'
);

CREATE TYPE credential_type AS ENUM (
    'username_password', 'api_key', 'ssh_keypair', 'oauth2_token',
    'client_certificate', 'aws_iam_role', 'azure_service_principal',
    'saml_assertion', 'ntlm', 'kerberos'
);

CREATE TYPE credential_scope AS ENUM (
    'scanner_auth', 'target_auth', 'cloud_api', 'source_repo', 'cicd'
);

CREATE TYPE scan_type AS ENUM (
    'dast', 'sast', 'sca', 'infrastructure', 'mobile_static',
    'mobile_dynamic', 'api_fuzz', 'config_audit', 'cloud_posture'
);

CREATE TYPE scanner_engine AS ENUM (
    'burp_suite', 'tenable_io', 'nessus', 'fortify_sast',
    'fortify_sca', 'mobsf', 'nuclei', 'zap', 'trivy',
    'prowler', 'semgrep', 'custom'
);

CREATE TYPE scan_job_status AS ENUM (
    'queued', 'credential_checkout', 'dispatched', 'running',
    'collecting_results', 'normalizing', 'completed',
    'failed', 'cancelled', 'timed_out'
);

CREATE TYPE severity_rating AS ENUM (
    'critical', 'high', 'medium', 'low', 'informational'
);

CREATE TYPE finding_status AS ENUM (
    'new', 'confirmed', 'false_positive', 'accepted_risk',
    'remediated', 'reopened', 'duplicate'
);

CREATE TYPE confidence_level AS ENUM (
    'confirmed', 'high', 'medium', 'low', 'tentative'
);

CREATE TYPE validation_verdict AS ENUM (
    'confirmed_exploitable', 'confirmed_vulnerable', 'likely_vulnerable',
    'false_positive', 'not_applicable', 'needs_retest', 'accepted_risk'
);

CREATE TYPE report_type AS ENUM (
    'executive_summary', 'full_technical', 'compliance',
    'delta_retest', 'custom'
);

CREATE TYPE report_format AS ENUM ('pdf', 'docx', 'html', 'json', 'csv');

CREATE TYPE report_status AS ENUM (
    'queued', 'generating', 'generated', 'under_review',
    'approved', 'delivered', 'failed'
);


-- ============================================================================
-- 1. CUSTOMERS (TENANTS)
-- ============================================================================
-- Top-level tenant table. Every downstream row is scoped to a customer.
-- This is the root of the multi-tenant hierarchy.
-- ============================================================================

CREATE TABLE customers (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    company_name        VARCHAR(255) NOT NULL,
    slug                VARCHAR(100) NOT NULL UNIQUE,    -- URL-safe identifier
    domain              VARCHAR(255),                     -- primary email domain
    industry            VARCHAR(100),
    company_size        VARCHAR(50),                      -- 'startup', 'smb', 'mid_market', 'enterprise'

    -- Subscription & billing
    subscription_tier   VARCHAR(50) NOT NULL DEFAULT 'professional',  -- 'starter', 'professional', 'enterprise'
    max_engagements     INT NOT NULL DEFAULT 10,
    max_assets          INT NOT NULL DEFAULT 100,
    max_concurrent_scans INT NOT NULL DEFAULT 5,
    billing_email       VARCHAR(255),
    stripe_customer_id  VARCHAR(255),

    -- MSSP relationship
    account_manager_id  UUID,                             -- internal MSSP staff owner
    onboarded_at        TIMESTAMPTZ,

    -- Compliance requirements
    required_frameworks TEXT[] DEFAULT '{}',               -- {'pci_dss_4', 'iso27001', 'soc2'}
    data_residency      VARCHAR(20) DEFAULT 'us-east-1',  -- region constraint

    -- Status
    is_active           BOOLEAN NOT NULL DEFAULT true,
    deactivated_at      TIMESTAMPTZ,
    deactivation_reason TEXT,

    -- Metadata
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_customers_slug ON customers(slug);
CREATE INDEX idx_customers_active ON customers(is_active) WHERE is_active = true;
CREATE INDEX idx_customers_tier ON customers(subscription_tier);
CREATE INDEX idx_customers_account_mgr ON customers(account_manager_id);

COMMENT ON TABLE customers IS
    'Root tenant table. Every entity in the platform belongs to exactly one customer.';


-- ============================================================================
-- 2. USERS
-- ============================================================================
-- Platform users across both customer-side and MSSP-side.
-- Linked to an external IdP (Keycloak/Auth0) via idp_subject_id.
-- ============================================================================

CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,

    -- Identity (synced from IdP)
    email               VARCHAR(255) NOT NULL,
    display_name        VARCHAR(255) NOT NULL,
    idp_subject_id      VARCHAR(255) NOT NULL UNIQUE,   -- external IdP sub claim
    avatar_url          VARCHAR(512),

    -- Role & access
    role                VARCHAR(50) NOT NULL DEFAULT 'viewer',
    --   Customer roles : 'customer_admin', 'customer_user', 'viewer'
    --   MSSP roles     : 'platform_admin', 'lead_analyst', 'analyst', 'scanner_operator'
    permissions         JSONB NOT NULL DEFAULT '[]',     -- fine-grained overrides

    -- Contact
    phone               VARCHAR(30),
    timezone            VARCHAR(50) DEFAULT 'UTC',

    -- Status
    is_active           BOOLEAN NOT NULL DEFAULT true,
    last_login_at       TIMESTAMPTZ,
    mfa_enabled         BOOLEAN NOT NULL DEFAULT false,
    locked_at           TIMESTAMPTZ,
    lock_reason         TEXT,

    -- Metadata
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (customer_id, email)
);

CREATE INDEX idx_users_customer ON users(customer_id);
CREATE INDEX idx_users_role ON users(customer_id, role);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_idp ON users(idp_subject_id);
CREATE INDEX idx_users_active ON users(customer_id, is_active) WHERE is_active = true;

COMMENT ON TABLE users IS
    'All platform users. Roles span customer-side (viewer, admin) and MSSP-side (analyst, admin).';


-- ============================================================================
-- 3. ENGAGEMENTS
-- ============================================================================
-- A bounded security assessment project for a customer.
-- An engagement scopes which assets are tested, which scan types run,
-- and tracks lifecycle from draft → closed.
-- ============================================================================

CREATE TABLE engagements (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,

    -- Descriptors
    name                VARCHAR(255) NOT NULL,
    reference_code      VARCHAR(50) NOT NULL,            -- human-readable: "ENG-2026-0042"
    engagement_type     engagement_type NOT NULL,
    description         TEXT,
    priority            priority_level NOT NULL DEFAULT 'medium',

    -- Lifecycle
    status              engagement_status NOT NULL DEFAULT 'draft',
    status_changed_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Scheduling
    scheduled_start     TIMESTAMPTZ,
    scheduled_end       TIMESTAMPTZ,
    actual_start        TIMESTAMPTZ,
    actual_end          TIMESTAMPTZ,

    -- People
    created_by          UUID NOT NULL REFERENCES users(id),
    assigned_lead       UUID REFERENCES users(id),       -- lead analyst
    approved_by         UUID REFERENCES users(id),
    approved_at         TIMESTAMPTZ,

    -- Scope boundaries
    scope_definition    JSONB NOT NULL DEFAULT '{}',
    --  {
    --    "included_asset_ids": ["..."],
    --    "scan_types": ["dast", "sast"],
    --    "excluded_paths": ["/admin/debug"],
    --    "testing_window": {"start": "02:00Z", "end": "06:00Z"},
    --    "rate_limit_rps": 50,
    --    "rules_of_engagement": "No DoS testing on production"
    --  }

    -- Compliance
    compliance_frameworks TEXT[] DEFAULT '{}',            -- frameworks to map against

    -- SLA
    sla_profile_id      UUID,                            -- FK to sla_profiles if you extend

    -- Summary (denormalised for dashboard performance)
    total_findings      INT NOT NULL DEFAULT 0,
    critical_findings   INT NOT NULL DEFAULT 0,
    high_findings       INT NOT NULL DEFAULT 0,
    medium_findings     INT NOT NULL DEFAULT 0,
    low_findings        INT NOT NULL DEFAULT 0,
    info_findings       INT NOT NULL DEFAULT 0,

    -- Metadata
    tags                TEXT[] DEFAULT '{}',
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (customer_id, reference_code)
);

CREATE INDEX idx_engagements_customer ON engagements(customer_id);
CREATE INDEX idx_engagements_status ON engagements(customer_id, status);
CREATE INDEX idx_engagements_lead ON engagements(assigned_lead);
CREATE INDEX idx_engagements_dates ON engagements(scheduled_start, scheduled_end);
CREATE INDEX idx_engagements_priority ON engagements(customer_id, priority);
CREATE INDEX idx_engagements_ref ON engagements(reference_code);
CREATE INDEX idx_engagements_tags ON engagements USING gin(tags);

COMMENT ON TABLE engagements IS
    'A bounded VAPT assessment. Links customers to assets, scans, findings, and reports.';


-- ============================================================================
-- 4. ASSETS
-- ============================================================================
-- The inventory of things a customer owns that can be scanned.
-- Assets persist across engagements — they are the durable record.
-- ============================================================================

CREATE TABLE assets (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,

    -- Classification
    asset_type          asset_type NOT NULL,
    name                VARCHAR(255) NOT NULL,
    identifier          VARCHAR(512) NOT NULL,           -- URL, IP, CIDR, bundle ID
    environment         asset_environment NOT NULL DEFAULT 'production',
    criticality         priority_level NOT NULL DEFAULT 'medium',

    -- Ownership
    business_unit       VARCHAR(255),
    owner_name          VARCHAR(255),
    owner_email         VARCHAR(255),
    technical_contact   VARCHAR(255),

    -- Technical profile
    tech_stack          JSONB NOT NULL DEFAULT '[]',     -- ["nginx/1.25", "react/18", "java/21"]
    operating_system    VARCHAR(100),
    hosting             VARCHAR(100),                    -- 'aws', 'azure', 'on_premise', 'hybrid'
    is_internet_facing  BOOLEAN NOT NULL DEFAULT true,

    -- Discovery
    discovery_method    VARCHAR(50) DEFAULT 'manual',    -- 'manual', 'subdomain_enum', 'cloud_sync', 'cicd'
    discovered_at       TIMESTAMPTZ,

    -- Scan history (denormalised)
    last_scanned_at     TIMESTAMPTZ,
    total_scans         INT NOT NULL DEFAULT 0,
    open_findings_count INT NOT NULL DEFAULT 0,

    -- Status
    status              VARCHAR(20) NOT NULL DEFAULT 'active',  -- 'active', 'inactive', 'decommissioned'

    -- Metadata
    tags                TEXT[] DEFAULT '{}',
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (customer_id, asset_type, identifier)
);

CREATE INDEX idx_assets_customer ON assets(customer_id);
CREATE INDEX idx_assets_type ON assets(customer_id, asset_type);
CREATE INDEX idx_assets_criticality ON assets(customer_id, criticality);
CREATE INDEX idx_assets_identifier ON assets(customer_id, identifier);
CREATE INDEX idx_assets_environment ON assets(customer_id, environment);
CREATE INDEX idx_assets_status ON assets(customer_id, status) WHERE status = 'active';
CREATE INDEX idx_assets_tags ON assets USING gin(tags);
CREATE INDEX idx_assets_tech ON assets USING gin(tech_stack jsonb_path_ops);

COMMENT ON TABLE assets IS
    'Durable inventory of customer-owned assets. Persists across engagements.';


-- ============================================================================
-- 4b. ENGAGEMENT ↔ ASSET junction (scope)
-- ============================================================================
-- Which assets are in-scope for a specific engagement, and what scan types
-- are authorised for each.
-- ============================================================================

CREATE TABLE engagement_assets (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id       UUID NOT NULL REFERENCES engagements(id) ON DELETE CASCADE,
    asset_id            UUID NOT NULL REFERENCES assets(id) ON DELETE RESTRICT,
    customer_id         UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,

    -- Scope per asset
    scan_types_allowed  scan_type[] NOT NULL DEFAULT '{}',
    excluded_paths      TEXT[] DEFAULT '{}',
    testing_notes       TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (engagement_id, asset_id)
);

CREATE INDEX idx_ea_engagement ON engagement_assets(engagement_id);
CREATE INDEX idx_ea_asset ON engagement_assets(asset_id);
CREATE INDEX idx_ea_customer ON engagement_assets(customer_id);

COMMENT ON TABLE engagement_assets IS
    'Junction table: which assets are in-scope for an engagement and what scan types are authorised.';


-- ============================================================================
-- 5. TARGETS
-- ============================================================================
-- Concrete network-level endpoints derived from assets.
-- One asset (e.g. "Corporate Website") may yield multiple targets
-- (the main URL, staging URL, API gateway, individual IPs, etc.).
-- Targets are what scanners actually point at.
-- ============================================================================

CREATE TABLE targets (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    asset_id            UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,

    -- Network endpoint
    host                VARCHAR(255) NOT NULL,            -- IP or hostname
    port                INT,
    protocol            target_protocol NOT NULL DEFAULT 'https',
    url                 VARCHAR(2048),                    -- full URL for web targets
    path_prefix         VARCHAR(512),                     -- e.g. /api/v2

    -- Authentication requirements
    requires_auth       BOOLEAN NOT NULL DEFAULT false,
    credential_profile_id UUID,                           -- FK to credential_profiles

    -- Reachability
    is_reachable        BOOLEAN,
    last_reachability_check TIMESTAMPTZ,
    reachability_error  TEXT,

    -- Scan constraints
    max_requests_per_second INT DEFAULT 50,
    scan_window_start   TIME,                             -- e.g. 02:00 (UTC)
    scan_window_end     TIME,                             -- e.g. 06:00 (UTC)

    -- Metadata
    notes               TEXT,
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (customer_id, asset_id, host, port, protocol)
);

CREATE INDEX idx_targets_customer ON targets(customer_id);
CREATE INDEX idx_targets_asset ON targets(asset_id);
CREATE INDEX idx_targets_host ON targets(host);
CREATE INDEX idx_targets_credential ON targets(credential_profile_id)
    WHERE credential_profile_id IS NOT NULL;

COMMENT ON TABLE targets IS
    'Concrete network endpoints derived from assets. Scanners point at targets, not assets.';


-- ============================================================================
-- 6. CREDENTIAL PROFILES
-- ============================================================================
-- Metadata envelope for credentials. Actual secrets live in HashiCorp Vault;
-- this table only stores the Vault path + metadata for checkout/audit.
-- ============================================================================

CREATE TABLE credential_profiles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,

    -- Descriptors
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    credential_type     credential_type NOT NULL,
    scope               credential_scope NOT NULL,

    -- Vault integration (NO secret material stored here)
    vault_secret_path   VARCHAR(512) NOT NULL,            -- vault kv path
    vault_engine        VARCHAR(50) NOT NULL DEFAULT 'kv-v2',

    -- Linked entities
    linked_asset_ids    UUID[] DEFAULT '{}',
    linked_target_ids   UUID[] DEFAULT '{}',

    -- Rotation
    rotation_enabled    BOOLEAN NOT NULL DEFAULT false,
    rotation_interval_days INT,
    last_rotated_at     TIMESTAMPTZ,
    expires_at          TIMESTAMPTZ,

    -- Checkout state
    is_checked_out      BOOLEAN NOT NULL DEFAULT false,
    checked_out_by      VARCHAR(255),
    checkout_expires_at TIMESTAMPTZ,

    -- Validity
    last_tested_at      TIMESTAMPTZ,
    last_test_passed    BOOLEAN,

    -- Status
    status              VARCHAR(20) NOT NULL DEFAULT 'active',  -- 'active', 'expired', 'revoked', 'rotating'
    created_by          UUID NOT NULL REFERENCES users(id),

    -- Metadata
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_credentials_customer ON credential_profiles(customer_id);
CREATE INDEX idx_credentials_type ON credential_profiles(customer_id, credential_type);
CREATE INDEX idx_credentials_scope ON credential_profiles(customer_id, scope);
CREATE INDEX idx_credentials_status ON credential_profiles(customer_id, status)
    WHERE status = 'active';
CREATE INDEX idx_credentials_checkout ON credential_profiles(is_checked_out)
    WHERE is_checked_out = true;
CREATE INDEX idx_credentials_expiry ON credential_profiles(expires_at)
    WHERE expires_at IS NOT NULL;

COMMENT ON TABLE credential_profiles IS
    'Metadata for credentials. Secrets stored in HashiCorp Vault; this table holds vault paths and audit state.';


-- ============================================================================
-- 6b. CREDENTIAL AUDIT LOG
-- ============================================================================

CREATE TABLE credential_audit_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    credential_profile_id UUID NOT NULL REFERENCES credential_profiles(id) ON DELETE CASCADE,
    customer_id         UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,

    action              VARCHAR(30) NOT NULL,             -- 'created','checkout','checkin','rotated','revoked','tested'
    actor_id            UUID,                             -- user or service account
    actor_service       VARCHAR(100),                     -- 'scan_orchestration', 'manual'
    ip_address          INET,
    purpose             TEXT,                             -- scan_id or reason
    details             JSONB NOT NULL DEFAULT '{}',

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_cred_audit_profile ON credential_audit_log(credential_profile_id, created_at DESC);
CREATE INDEX idx_cred_audit_customer ON credential_audit_log(customer_id, created_at DESC);

COMMENT ON TABLE credential_audit_log IS
    'Immutable log of every credential access, rotation, and lifecycle event.';


-- ============================================================================
-- 7. SCAN JOBS
-- ============================================================================
-- Each scan job = one scanner running against one target (or batch of targets).
-- Orchestrated by Temporal workflows in the Scan Orchestration service.
-- ============================================================================

CREATE TABLE scan_jobs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    engagement_id       UUID NOT NULL REFERENCES engagements(id) ON DELETE RESTRICT,
    asset_id            UUID NOT NULL REFERENCES assets(id) ON DELETE RESTRICT,
    target_id           UUID REFERENCES targets(id) ON DELETE SET NULL,

    -- Scan configuration
    scan_type           scan_type NOT NULL,
    scanner_engine      scanner_engine NOT NULL,
    scan_config         JSONB NOT NULL DEFAULT '{}',
    --  {
    --    "profile": "full_audit",
    --    "max_duration_minutes": 240,
    --    "excluded_checks": [".."],
    --    "custom_headers": {"Authorization": "Bearer ..."}
    --  }

    -- Lifecycle
    status              scan_job_status NOT NULL DEFAULT 'queued',
    priority            INT NOT NULL DEFAULT 5,           -- 1 = highest, 10 = lowest
    queued_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    duration_seconds    INT,

    -- Progress
    progress_percent    SMALLINT NOT NULL DEFAULT 0 CHECK (progress_percent BETWEEN 0 AND 100),

    -- Workflow tracking
    temporal_workflow_id VARCHAR(255),
    temporal_run_id     VARCHAR(255),

    -- Credentials used
    credential_profile_id UUID REFERENCES credential_profiles(id),

    -- Retry
    attempt_number      SMALLINT NOT NULL DEFAULT 1,
    max_attempts        SMALLINT NOT NULL DEFAULT 3,
    last_error          TEXT,

    -- Result summary (denormalised)
    findings_critical   INT NOT NULL DEFAULT 0,
    findings_high       INT NOT NULL DEFAULT 0,
    findings_medium     INT NOT NULL DEFAULT 0,
    findings_low        INT NOT NULL DEFAULT 0,
    findings_info       INT NOT NULL DEFAULT 0,
    total_findings      INT NOT NULL DEFAULT 0,

    -- Initiated by
    initiated_by        UUID REFERENCES users(id),
    initiated_via       VARCHAR(50) DEFAULT 'engagement_launch', -- 'manual', 'scheduled', 'engagement_launch', 'retest'

    -- Metadata
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_scanjobs_customer ON scan_jobs(customer_id);
CREATE INDEX idx_scanjobs_engagement ON scan_jobs(engagement_id);
CREATE INDEX idx_scanjobs_asset ON scan_jobs(asset_id);
CREATE INDEX idx_scanjobs_target ON scan_jobs(target_id) WHERE target_id IS NOT NULL;
CREATE INDEX idx_scanjobs_status ON scan_jobs(customer_id, status);
CREATE INDEX idx_scanjobs_queue ON scan_jobs(status, priority, queued_at)
    WHERE status = 'queued';
CREATE INDEX idx_scanjobs_running ON scan_jobs(status, started_at)
    WHERE status = 'running';
CREATE INDEX idx_scanjobs_temporal ON scan_jobs(temporal_workflow_id)
    WHERE temporal_workflow_id IS NOT NULL;

COMMENT ON TABLE scan_jobs IS
    'One scan job = one scanner engine execution against one target/asset. Tracked via Temporal workflows.';


-- ============================================================================
-- 8. SCAN RESULTS (RAW)
-- ============================================================================
-- Raw, unprocessed output from scanner connectors, stored as JSONB.
-- This is the audit trail of what the scanner actually reported
-- before normalisation into findings.
-- ============================================================================

CREATE TABLE scan_results (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    scan_job_id         UUID NOT NULL REFERENCES scan_jobs(id) ON DELETE CASCADE,

    -- Scanner output
    scanner_engine      scanner_engine NOT NULL,
    raw_output          JSONB NOT NULL,                   -- scanner-native JSON
    output_format       VARCHAR(50) NOT NULL DEFAULT 'json', -- 'json', 'xml_converted', 'sarif'
    output_hash         VARCHAR(64) NOT NULL,             -- SHA-256 of raw_output for integrity

    -- Parsing state
    is_parsed           BOOLEAN NOT NULL DEFAULT false,
    parsed_at           TIMESTAMPTZ,
    parse_errors        TEXT[] DEFAULT '{}',
    findings_extracted  INT NOT NULL DEFAULT 0,

    -- Storage
    raw_file_path       VARCHAR(512),                     -- MinIO path for large outputs
    file_size_bytes     BIGINT,

    -- Metadata
    scanner_version     VARCHAR(50),
    scan_duration_secs  INT,
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_scanresults_customer ON scan_results(customer_id);
CREATE INDEX idx_scanresults_job ON scan_results(scan_job_id);
CREATE INDEX idx_scanresults_parsed ON scan_results(is_parsed)
    WHERE is_parsed = false;
CREATE INDEX idx_scanresults_engine ON scan_results(scanner_engine);

COMMENT ON TABLE scan_results IS
    'Raw scanner output. Immutable audit trail before normalisation into findings.';


-- ============================================================================
-- 9. FINDINGS
-- ============================================================================
-- Normalised, deduplicated vulnerability findings.
-- Every finding is traced back to the scan that discovered it and
-- the asset/target where it exists.
-- ============================================================================

CREATE TABLE findings (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    engagement_id       UUID NOT NULL REFERENCES engagements(id) ON DELETE RESTRICT,
    scan_job_id         UUID NOT NULL REFERENCES scan_jobs(id) ON DELETE RESTRICT,
    asset_id            UUID NOT NULL REFERENCES assets(id) ON DELETE RESTRICT,
    target_id           UUID REFERENCES targets(id) ON DELETE SET NULL,
    scan_result_id      UUID REFERENCES scan_results(id) ON DELETE SET NULL,

    -- Classification
    title               VARCHAR(500) NOT NULL,
    description         TEXT NOT NULL,
    category            VARCHAR(255) NOT NULL,            -- "SQL Injection", "XSS Reflected", "SSH Weak Cipher"
    subcategory         VARCHAR(255),

    -- Severity
    severity            severity_rating NOT NULL,
    original_severity   severity_rating NOT NULL,         -- as reported by scanner
    cvss_score          DECIMAL(3,1) CHECK (cvss_score BETWEEN 0.0 AND 10.0),
    cvss_vector         VARCHAR(200),
    cvss_version        VARCHAR(10) DEFAULT '3.1',
    epss_score          DECIMAL(5,4),                     -- Exploit Prediction Scoring System

    -- Status & workflow
    status              finding_status NOT NULL DEFAULT 'new',
    confidence          confidence_level NOT NULL DEFAULT 'medium',

    -- References
    cwe_id              VARCHAR(20),                      -- "CWE-89"
    cve_ids             TEXT[] DEFAULT '{}',               -- {"CVE-2024-1234", "CVE-2024-5678"}
    owasp_category      VARCHAR(50),                      -- "A03:2021"
    wasc_id             VARCHAR(20),

    -- Source
    scanner_engine      scanner_engine NOT NULL,
    scan_type           scan_type NOT NULL,

    -- Location
    affected_url        VARCHAR(2048),
    affected_host       VARCHAR(255),
    affected_port       INT,
    affected_parameter  VARCHAR(255),
    affected_file       VARCHAR(1024),                    -- for SAST
    affected_line       INT,                              -- for SAST
    affected_component  VARCHAR(500),                     -- for SCA (library name@version)
    location_context    JSONB NOT NULL DEFAULT '{}',
    --  {
    --    "method": "POST",
    --    "path": "/api/v1/users",
    --    "parameter": "email",
    --    "injection_point": "body"
    --  }

    -- Evidence
    evidence            JSONB NOT NULL DEFAULT '[]',
    --  [
    --    {"type": "http_request", "content": "POST /api/..."},
    --    {"type": "http_response", "content": "200 OK ..."},
    --    {"type": "screenshot", "minio_path": "..."},
    --    {"type": "code_snippet", "content": "...", "file": "...", "line": 42}
    --  ]

    -- Remediation
    remediation         TEXT,
    remediation_effort  VARCHAR(20),                      -- 'trivial', 'low', 'medium', 'high', 'complex'
    remediation_deadline TIMESTAMPTZ,

    -- AI enrichment
    ai_severity_score   DECIMAL(5,2),                     -- ML severity 0–10
    ai_exploitability   DECIMAL(5,2),                     -- ML exploitability 0–10
    ai_false_positive_prob DECIMAL(3,2) CHECK (ai_false_positive_prob BETWEEN 0.0 AND 1.0),
    ai_remediation      TEXT,                             -- AI-generated fix guidance
    ai_analysis_at      TIMESTAMPTZ,

    -- Deduplication
    fingerprint         VARCHAR(64) NOT NULL,             -- SHA-256(customer_id+category+location_key+cwe)
    duplicate_cluster_id UUID,
    is_primary          BOOLEAN NOT NULL DEFAULT true,

    -- Workflow assignment
    assigned_to         UUID REFERENCES users(id),
    validated_by        UUID REFERENCES users(id),
    validated_at        TIMESTAMPTZ,
    remediated_at       TIMESTAMPTZ,

    -- First/last seen (for recurring findings)
    first_seen_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    occurrence_count    INT NOT NULL DEFAULT 1,

    -- Metadata
    tags                TEXT[] DEFAULT '{}',
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Core lookups
CREATE INDEX idx_findings_customer ON findings(customer_id);
CREATE INDEX idx_findings_engagement ON findings(customer_id, engagement_id);
CREATE INDEX idx_findings_asset ON findings(asset_id);
CREATE INDEX idx_findings_scan ON findings(scan_job_id);

-- Dashboard queries
CREATE INDEX idx_findings_severity ON findings(customer_id, severity)
    WHERE status NOT IN ('false_positive', 'remediated', 'duplicate');
CREATE INDEX idx_findings_status ON findings(customer_id, status);
CREATE INDEX idx_findings_open_critical ON findings(customer_id, engagement_id, severity)
    WHERE status IN ('new', 'confirmed', 'reopened') AND severity IN ('critical', 'high');

-- Dedup & correlation
CREATE INDEX idx_findings_fingerprint ON findings(customer_id, fingerprint);
CREATE INDEX idx_findings_cluster ON findings(duplicate_cluster_id)
    WHERE duplicate_cluster_id IS NOT NULL;
CREATE INDEX idx_findings_cwe ON findings(cwe_id) WHERE cwe_id IS NOT NULL;
CREATE INDEX idx_findings_cve ON findings USING gin(cve_ids) WHERE cve_ids != '{}';

-- Workflow
CREATE INDEX idx_findings_assigned ON findings(assigned_to, status)
    WHERE assigned_to IS NOT NULL AND status IN ('new', 'confirmed', 'reopened');
CREATE INDEX idx_findings_tags ON findings USING gin(tags);

-- Text search
CREATE INDEX idx_findings_title_trgm ON findings USING gin(title gin_trgm_ops);

COMMENT ON TABLE findings IS
    'Normalised vulnerability findings. Deduplicated, AI-enriched, with full evidence chain.';


-- ============================================================================
-- 10. MANUAL VALIDATION NOTES
-- ============================================================================
-- Analyst observations recorded during manual validation of findings.
-- Each note is an immutable audit record. Analysts may add multiple notes
-- over the triage lifecycle.
-- ============================================================================

CREATE TABLE manual_validation_notes (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    finding_id          UUID NOT NULL REFERENCES findings(id) ON DELETE CASCADE,
    engagement_id       UUID NOT NULL REFERENCES engagements(id) ON DELETE RESTRICT,

    -- Author
    author_id           UUID NOT NULL REFERENCES users(id),

    -- Validation decision
    verdict             validation_verdict NOT NULL,
    severity_override   severity_rating,                  -- NULL = no override

    -- Content
    title               VARCHAR(255),
    notes               TEXT NOT NULL,
    reproduction_steps  TEXT,                              -- step-by-step PoC
    business_impact     TEXT,

    -- Evidence attachments
    evidence_attachments JSONB NOT NULL DEFAULT '[]',
    --  [
    --    {"type": "screenshot",   "minio_path": "...", "caption": "SQLi confirmed"},
    --    {"type": "video",        "minio_path": "...", "duration_secs": 45},
    --    {"type": "pcap",         "minio_path": "...", "description": "Traffic capture"},
    --    {"type": "code_snippet", "content": "...", "language": "python"}
    --  ]

    -- Time tracking
    time_spent_minutes  INT,

    -- Flags
    is_exploitable      BOOLEAN,
    requires_retest     BOOLEAN NOT NULL DEFAULT false,
    is_internal_only    BOOLEAN NOT NULL DEFAULT false,   -- hidden from customer report

    -- Metadata
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_mvn_finding ON manual_validation_notes(finding_id, created_at DESC);
CREATE INDEX idx_mvn_customer ON manual_validation_notes(customer_id);
CREATE INDEX idx_mvn_engagement ON manual_validation_notes(engagement_id);
CREATE INDEX idx_mvn_author ON manual_validation_notes(author_id, created_at DESC);
CREATE INDEX idx_mvn_verdict ON manual_validation_notes(verdict);

COMMENT ON TABLE manual_validation_notes IS
    'Analyst-authored notes during finding triage. Immutable audit trail of validation decisions.';


-- ============================================================================
-- 11. REPORTS
-- ============================================================================
-- Generated VAPT reports. Each report is a point-in-time snapshot of
-- engagement findings, compliance mappings, and analyst notes.
-- ============================================================================

CREATE TABLE reports (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    engagement_id       UUID NOT NULL REFERENCES engagements(id) ON DELETE RESTRICT,

    -- Report definition
    title               VARCHAR(500) NOT NULL,
    report_type         report_type NOT NULL,
    format              report_format NOT NULL,
    template_id         UUID,                             -- FK to report_templates if extended

    -- Lifecycle
    status              report_status NOT NULL DEFAULT 'queued',
    generated_at        TIMESTAMPTZ,
    generation_duration_ms INT,

    -- Content snapshot
    finding_snapshot    JSONB NOT NULL DEFAULT '{}',
    --  {
    --    "total": 47,
    --    "by_severity": {"critical": 3, "high": 8, "medium": 15, "low": 12, "info": 9},
    --    "by_status": {"confirmed": 38, "false_positive": 5, "accepted_risk": 4},
    --    "finding_ids": ["..."]
    --  }
    scope_snapshot      JSONB NOT NULL DEFAULT '{}',      -- engagement scope at generation time
    compliance_snapshot JSONB NOT NULL DEFAULT '{}',      -- compliance mapping at generation time

    -- File storage
    file_path           VARCHAR(512),                     -- MinIO object key
    file_size_bytes     BIGINT,
    page_count          INT,
    file_hash           VARCHAR(64),                      -- SHA-256

    -- Approval & delivery
    generated_by        UUID NOT NULL REFERENCES users(id),
    reviewed_by         UUID REFERENCES users(id),
    reviewed_at         TIMESTAMPTZ,
    approved_by         UUID REFERENCES users(id),
    approved_at         TIMESTAMPTZ,
    delivered_at        TIMESTAMPTZ,
    delivery_method     VARCHAR(50),                      -- 'portal_download', 'email', 'teams', 'api'

    -- Versioning
    version             INT NOT NULL DEFAULT 1,
    parent_report_id    UUID REFERENCES reports(id),      -- previous version

    -- Metadata
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_reports_customer ON reports(customer_id);
CREATE INDEX idx_reports_engagement ON reports(engagement_id);
CREATE INDEX idx_reports_status ON reports(customer_id, status);
CREATE INDEX idx_reports_type ON reports(customer_id, report_type);
CREATE INDEX idx_reports_generated ON reports(generated_at DESC)
    WHERE status = 'generated' OR status = 'approved';

COMMENT ON TABLE reports IS
    'Generated VAPT reports. Point-in-time snapshots with file storage in MinIO.';


-- ============================================================================
-- 12. ROW-LEVEL SECURITY (RLS) FOR MULTI-TENANT ISOLATION
-- ============================================================================
-- Every table is protected by RLS. The application sets a session variable:
--   SET app.current_customer_id = '<uuid>';
-- and the policy ensures a user can only see their own tenant's data.
-- ============================================================================

ALTER TABLE customers              ENABLE ROW LEVEL SECURITY;
ALTER TABLE users                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE engagements            ENABLE ROW LEVEL SECURITY;
ALTER TABLE assets                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE engagement_assets      ENABLE ROW LEVEL SECURITY;
ALTER TABLE targets                ENABLE ROW LEVEL SECURITY;
ALTER TABLE credential_profiles    ENABLE ROW LEVEL SECURITY;
ALTER TABLE credential_audit_log   ENABLE ROW LEVEL SECURITY;
ALTER TABLE scan_jobs              ENABLE ROW LEVEL SECURITY;
ALTER TABLE scan_results           ENABLE ROW LEVEL SECURITY;
ALTER TABLE findings               ENABLE ROW LEVEL SECURITY;
ALTER TABLE manual_validation_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports                ENABLE ROW LEVEL SECURITY;

-- Policy: tenant can only see own rows
-- (Platform admins bypass RLS via BYPASSRLS role attribute)

CREATE POLICY tenant_isolation_customers ON customers
    USING (id = current_setting('app.current_customer_id')::UUID);

CREATE POLICY tenant_isolation_users ON users
    USING (customer_id = current_setting('app.current_customer_id')::UUID);

CREATE POLICY tenant_isolation_engagements ON engagements
    USING (customer_id = current_setting('app.current_customer_id')::UUID);

CREATE POLICY tenant_isolation_assets ON assets
    USING (customer_id = current_setting('app.current_customer_id')::UUID);

CREATE POLICY tenant_isolation_ea ON engagement_assets
    USING (customer_id = current_setting('app.current_customer_id')::UUID);

CREATE POLICY tenant_isolation_targets ON targets
    USING (customer_id = current_setting('app.current_customer_id')::UUID);

CREATE POLICY tenant_isolation_credentials ON credential_profiles
    USING (customer_id = current_setting('app.current_customer_id')::UUID);

CREATE POLICY tenant_isolation_cred_audit ON credential_audit_log
    USING (customer_id = current_setting('app.current_customer_id')::UUID);

CREATE POLICY tenant_isolation_scanjobs ON scan_jobs
    USING (customer_id = current_setting('app.current_customer_id')::UUID);

CREATE POLICY tenant_isolation_scanresults ON scan_results
    USING (customer_id = current_setting('app.current_customer_id')::UUID);

CREATE POLICY tenant_isolation_findings ON findings
    USING (customer_id = current_setting('app.current_customer_id')::UUID);

CREATE POLICY tenant_isolation_mvn ON manual_validation_notes
    USING (customer_id = current_setting('app.current_customer_id')::UUID);

CREATE POLICY tenant_isolation_reports ON reports
    USING (customer_id = current_setting('app.current_customer_id')::UUID);


-- ============================================================================
-- 13. TRIGGER: auto-update updated_at columns
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_customers_updated_at
    BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_engagements_updated_at
    BEFORE UPDATE ON engagements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_assets_updated_at
    BEFORE UPDATE ON assets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_targets_updated_at
    BEFORE UPDATE ON targets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_credentials_updated_at
    BEFORE UPDATE ON credential_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_scanjobs_updated_at
    BEFORE UPDATE ON scan_jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_findings_updated_at
    BEFORE UPDATE ON findings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_mvn_updated_at
    BEFORE UPDATE ON manual_validation_notes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_reports_updated_at
    BEFORE UPDATE ON reports FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- 14. TRIGGER: update engagement finding counts on finding INSERT/UPDATE
-- ============================================================================

CREATE OR REPLACE FUNCTION update_engagement_finding_counts()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE engagements SET
        total_findings    = sub.total,
        critical_findings = sub.crit,
        high_findings     = sub.high,
        medium_findings   = sub.med,
        low_findings      = sub.low,
        info_findings     = sub.info
    FROM (
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE severity = 'critical')      AS crit,
            COUNT(*) FILTER (WHERE severity = 'high')          AS high,
            COUNT(*) FILTER (WHERE severity = 'medium')        AS med,
            COUNT(*) FILTER (WHERE severity = 'low')           AS low,
            COUNT(*) FILTER (WHERE severity = 'informational') AS info
        FROM findings
        WHERE engagement_id = COALESCE(NEW.engagement_id, OLD.engagement_id)
          AND status NOT IN ('false_positive', 'duplicate')
    ) sub
    WHERE engagements.id = COALESCE(NEW.engagement_id, OLD.engagement_id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_findings_count_sync
    AFTER INSERT OR UPDATE OF severity, status OR DELETE ON findings
    FOR EACH ROW EXECUTE FUNCTION update_engagement_finding_counts();


-- ============================================================================
-- 15. ENTITY-RELATIONSHIP SUMMARY
-- ============================================================================
--
--  customers (1) ──────┬──── (N) users
--                      ├──── (N) engagements
--                      ├──── (N) assets
--                      ├──── (N) targets
--                      ├──── (N) credential_profiles
--                      ├──── (N) scan_jobs
--                      ├──── (N) scan_results
--                      ├──── (N) findings
--                      ├──── (N) manual_validation_notes
--                      └──── (N) reports
--
--  engagements (1) ────┬──── (N) engagement_assets ──── (1) assets
--                      ├──── (N) scan_jobs
--                      ├──── (N) findings
--                      ├──── (N) manual_validation_notes
--                      └──── (N) reports
--
--  assets (1) ─────────┬──── (N) targets
--                      ├──── (N) engagement_assets
--                      ├──── (N) scan_jobs
--                      └──── (N) findings
--
--  targets (1) ────────┬──── (N) scan_jobs
--                      └──── (N) findings
--
--  scan_jobs (1) ──────┬──── (N) scan_results
--                      └──── (N) findings
--
--  findings (1) ───────└──── (N) manual_validation_notes
--
--  credential_profiles (1) ── (N) credential_audit_log
--                            ── (N) scan_jobs (via credential_profile_id)
--                            ── (N) targets  (via credential_profile_id)
--
-- ============================================================================


-- ============================================================================
-- 16. EXAMPLE QUERIES
-- ============================================================================

-- ────────────────────────────────────────────────────────────────────────────
-- Q1: Executive dashboard — finding severity breakdown per customer
-- ────────────────────────────────────────────────────────────────────────────
-- Used by: Customer Portal dashboard, MSSP overview screen
-- Performance: Uses idx_findings_severity partial index
-- ────────────────────────────────────────────────────────────────────────────

/*
SELECT
    c.company_name,
    COUNT(*) FILTER (WHERE f.severity = 'critical')      AS critical,
    COUNT(*) FILTER (WHERE f.severity = 'high')          AS high,
    COUNT(*) FILTER (WHERE f.severity = 'medium')        AS medium,
    COUNT(*) FILTER (WHERE f.severity = 'low')           AS low,
    COUNT(*) FILTER (WHERE f.severity = 'informational') AS info,
    COUNT(*)                                              AS total_open
FROM findings f
JOIN customers c ON c.id = f.customer_id
WHERE f.status IN ('new', 'confirmed', 'reopened')
GROUP BY c.id, c.company_name
ORDER BY critical DESC, high DESC;
*/


-- ────────────────────────────────────────────────────────────────────────────
-- Q2: Engagement status with scan progress and finding counts
-- ────────────────────────────────────────────────────────────────────────────
-- Used by: Engagement detail page
-- Performance: Uses idx_scanjobs_engagement, idx_engagements_customer
-- ────────────────────────────────────────────────────────────────────────────

/*
SELECT
    e.id                    AS engagement_id,
    e.reference_code,
    e.name,
    e.status,
    e.priority,
    e.scheduled_start,
    e.scheduled_end,
    u.display_name          AS lead_analyst,
    e.total_findings,
    e.critical_findings,
    e.high_findings,
    COUNT(sj.id)            AS total_scans,
    COUNT(sj.id) FILTER (WHERE sj.status = 'completed') AS completed_scans,
    COUNT(sj.id) FILTER (WHERE sj.status = 'running')   AS running_scans,
    COUNT(sj.id) FILTER (WHERE sj.status = 'failed')    AS failed_scans
FROM engagements e
LEFT JOIN users u ON u.id = e.assigned_lead
LEFT JOIN scan_jobs sj ON sj.engagement_id = e.id
WHERE e.customer_id = '{{customer_id}}'
  AND e.status IN ('in_progress', 'review')
GROUP BY e.id, u.display_name
ORDER BY e.priority, e.scheduled_end;
*/


-- ────────────────────────────────────────────────────────────────────────────
-- Q3: Open critical/high findings with asset context for analyst worklist
-- ────────────────────────────────────────────────────────────────────────────
-- Used by: Analyst triage queue
-- Performance: Uses idx_findings_open_critical partial index
-- ────────────────────────────────────────────────────────────────────────────

/*
SELECT
    f.id                    AS finding_id,
    f.title,
    f.severity,
    f.confidence,
    f.category,
    f.cwe_id,
    f.cvss_score,
    f.ai_exploitability,
    f.ai_false_positive_prob,
    a.name                  AS asset_name,
    a.criticality           AS asset_criticality,
    a.environment,
    t.host,
    t.port,
    f.affected_url,
    f.status,
    f.assigned_to,
    ua.display_name         AS assigned_analyst,
    f.first_seen_at,
    f.occurrence_count
FROM findings f
JOIN assets a ON a.id = f.asset_id
LEFT JOIN targets t ON t.id = f.target_id
LEFT JOIN users ua ON ua.id = f.assigned_to
WHERE f.customer_id = '{{customer_id}}'
  AND f.engagement_id = '{{engagement_id}}'
  AND f.status IN ('new', 'confirmed', 'reopened')
  AND f.severity IN ('critical', 'high')
ORDER BY
    CASE f.severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 END,
    f.cvss_score DESC NULLS LAST,
    f.ai_exploitability DESC NULLS LAST;
*/


-- ────────────────────────────────────────────────────────────────────────────
-- Q4: Scan job queue with priority ordering
-- ────────────────────────────────────────────────────────────────────────────
-- Used by: Scan Orchestration Service to pick next job
-- Performance: Uses idx_scanjobs_queue partial index
-- ────────────────────────────────────────────────────────────────────────────

/*
SELECT
    sj.id,
    sj.customer_id,
    sj.scan_type,
    sj.scanner_engine,
    sj.priority,
    sj.queued_at,
    a.name              AS asset_name,
    a.identifier        AS asset_identifier,
    t.host,
    t.port,
    t.url               AS target_url,
    sj.credential_profile_id,
    sj.scan_config,
    c.max_concurrent_scans
FROM scan_jobs sj
JOIN assets a ON a.id = sj.asset_id
LEFT JOIN targets t ON t.id = sj.target_id
JOIN customers c ON c.id = sj.customer_id
WHERE sj.status = 'queued'
ORDER BY sj.priority ASC, sj.queued_at ASC
LIMIT 10
FOR UPDATE SKIP LOCKED;
*/


-- ────────────────────────────────────────────────────────────────────────────
-- Q5: Finding deduplication — check if a normalised finding already exists
-- ────────────────────────────────────────────────────────────────────────────
-- Used by: Findings Normalisation Service during ingestion
-- Performance: Uses idx_findings_fingerprint
-- ────────────────────────────────────────────────────────────────────────────

/*
SELECT
    f.id,
    f.title,
    f.severity,
    f.status,
    f.engagement_id,
    f.first_seen_at,
    f.occurrence_count,
    f.duplicate_cluster_id
FROM findings f
WHERE f.customer_id = '{{customer_id}}'
  AND f.fingerprint = encode(
        sha256(
            '{{customer_id}}' || '{{category}}' || '{{location_key}}' || '{{cwe_id}}'
        ),
        'hex'
      )
ORDER BY f.first_seen_at ASC;
*/


-- ────────────────────────────────────────────────────────────────────────────
-- Q6: Credential checkout — atomic check-and-lock
-- ────────────────────────────────────────────────────────────────────────────
-- Used by: Scan Orchestration before dispatching to scanner connectors
-- Performance: Uses idx_credentials_checkout partial index
-- ────────────────────────────────────────────────────────────────────────────

/*
UPDATE credential_profiles
SET
    is_checked_out      = true,
    checked_out_by      = 'scan_orchestration:{{scan_job_id}}',
    checkout_expires_at = now() + interval '4 hours',
    updated_at          = now()
WHERE id = '{{credential_profile_id}}'
  AND customer_id = '{{customer_id}}'
  AND status = 'active'
  AND is_checked_out = false
RETURNING id, vault_secret_path, vault_engine;
*/


-- ────────────────────────────────────────────────────────────────────────────
-- Q7: Finding validation history — full audit trail for a finding
-- ────────────────────────────────────────────────────────────────────────────
-- Used by: Finding detail page, compliance auditors
-- Performance: Uses idx_mvn_finding
-- ────────────────────────────────────────────────────────────────────────────

/*
SELECT
    mvn.id,
    mvn.verdict,
    mvn.severity_override,
    mvn.title,
    mvn.notes,
    mvn.reproduction_steps,
    mvn.business_impact,
    mvn.is_exploitable,
    mvn.requires_retest,
    mvn.time_spent_minutes,
    mvn.evidence_attachments,
    u.display_name      AS analyst_name,
    u.email             AS analyst_email,
    mvn.created_at
FROM manual_validation_notes mvn
JOIN users u ON u.id = mvn.author_id
WHERE mvn.finding_id = '{{finding_id}}'
ORDER BY mvn.created_at ASC;
*/


-- ────────────────────────────────────────────────────────────────────────────
-- Q8: Report generation — gather all confirmed findings for an engagement
-- ────────────────────────────────────────────────────────────────────────────
-- Used by: Reporting Service during PDF/DOCX generation
-- Performance: Uses idx_findings_engagement + status filter
-- ────────────────────────────────────────────────────────────────────────────

/*
SELECT
    f.id,
    f.title,
    f.category,
    f.severity,
    f.cvss_score,
    f.cvss_vector,
    f.cwe_id,
    f.cve_ids,
    f.owasp_category,
    f.description,
    f.affected_url,
    f.affected_host,
    f.affected_port,
    f.affected_file,
    f.affected_line,
    f.affected_component,
    f.evidence,
    f.remediation,
    f.remediation_effort,
    f.ai_remediation,
    f.confidence,
    a.name              AS asset_name,
    a.asset_type,
    a.environment,
    a.criticality       AS asset_criticality,
    latest_note.verdict AS validation_verdict,
    latest_note.notes   AS validation_notes,
    validator.display_name AS validated_by_name
FROM findings f
JOIN assets a ON a.id = f.asset_id
LEFT JOIN LATERAL (
    SELECT mvn.verdict, mvn.notes, mvn.author_id
    FROM manual_validation_notes mvn
    WHERE mvn.finding_id = f.id
    ORDER BY mvn.created_at DESC
    LIMIT 1
) latest_note ON true
LEFT JOIN users validator ON validator.id = latest_note.author_id
WHERE f.engagement_id = '{{engagement_id}}'
  AND f.customer_id   = '{{customer_id}}'
  AND f.status IN ('confirmed', 'accepted_risk')
  AND f.is_primary = true
ORDER BY
    CASE f.severity
        WHEN 'critical'      THEN 1
        WHEN 'high'          THEN 2
        WHEN 'medium'        THEN 3
        WHEN 'low'           THEN 4
        WHEN 'informational' THEN 5
    END,
    f.cvss_score DESC NULLS LAST;
*/


-- ────────────────────────────────────────────────────────────────────────────
-- Q9: MSSP cross-tenant analytics — top vulnerabilities across all customers
-- ────────────────────────────────────────────────────────────────────────────
-- Used by: MSSP internal analytics dashboard (platform_admin role, bypasses RLS)
-- Performance: Uses idx_findings_cwe
-- ────────────────────────────────────────────────────────────────────────────

/*
SELECT
    f.cwe_id,
    f.category,
    COUNT(DISTINCT f.customer_id)   AS affected_customers,
    COUNT(*)                        AS total_occurrences,
    COUNT(*) FILTER (WHERE f.severity = 'critical') AS critical_count,
    COUNT(*) FILTER (WHERE f.severity = 'high')     AS high_count,
    AVG(f.cvss_score)::DECIMAL(3,1) AS avg_cvss,
    MODE() WITHIN GROUP (ORDER BY f.remediation_effort) AS typical_effort
FROM findings f
WHERE f.status IN ('new', 'confirmed', 'reopened')
  AND f.cwe_id IS NOT NULL
  AND f.is_primary = true
GROUP BY f.cwe_id, f.category
HAVING COUNT(DISTINCT f.customer_id) >= 3
ORDER BY affected_customers DESC, critical_count DESC
LIMIT 25;
*/


-- ────────────────────────────────────────────────────────────────────────────
-- Q10: Asset risk scorecard — open findings grouped by asset
-- ────────────────────────────────────────────────────────────────────────────
-- Used by: Asset inventory page, risk heat map
-- Performance: Uses idx_findings_asset, idx_assets_customer
-- ────────────────────────────────────────────────────────────────────────────

/*
SELECT
    a.id                AS asset_id,
    a.name,
    a.asset_type,
    a.identifier,
    a.environment,
    a.criticality,
    a.last_scanned_at,
    COUNT(*) FILTER (WHERE f.severity = 'critical')      AS open_critical,
    COUNT(*) FILTER (WHERE f.severity = 'high')          AS open_high,
    COUNT(*) FILTER (WHERE f.severity = 'medium')        AS open_medium,
    COUNT(*) FILTER (WHERE f.severity = 'low')           AS open_low,
    COUNT(*)                                              AS total_open,
    MAX(f.cvss_score)                                     AS highest_cvss,
    -- Risk score: weighted sum normalised to 0–100
    LEAST(100, (
        COUNT(*) FILTER (WHERE f.severity = 'critical') * 40 +
        COUNT(*) FILTER (WHERE f.severity = 'high')     * 20 +
        COUNT(*) FILTER (WHERE f.severity = 'medium')   * 5  +
        COUNT(*) FILTER (WHERE f.severity = 'low')      * 1
    ))::INT AS risk_score
FROM assets a
LEFT JOIN findings f ON f.asset_id = a.id
    AND f.status IN ('new', 'confirmed', 'reopened')
WHERE a.customer_id = '{{customer_id}}'
  AND a.status = 'active'
GROUP BY a.id
ORDER BY risk_score DESC, open_critical DESC;
*/


-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
