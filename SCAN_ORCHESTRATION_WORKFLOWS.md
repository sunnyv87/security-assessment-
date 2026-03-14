# Scan Orchestration Workflows — AI-Driven VAPT Platform

## Temporal.io Workflow Definitions for Multi-Scanner Coordination

---

## 1. Orchestration Architecture

```
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                   SCAN REQUEST SOURCES                                        ║
║                                                                                                ║
║  ┌────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  ┌───────────────┐  ║
║  │ MCP Server         │  │ Engagement Service  │  │ CI/CD Webhook       │  │ Cron Scheduler│  ║
║  │ (AI agent / human) │  │ (engagement.launch) │  │ (PR merge trigger)  │  │ (recurring)   │  ║
║  └────────┬───────────┘  └────────┬────────────┘  └────────┬────────────┘  └───────┬───────┘  ║
║           │                       │                         │                       │          ║
║           ▼                       ▼                         ▼                       ▼          ║
║  ┌──────────────────────────────────────────────────────────────────────────────────────────┐  ║
║  │                         SCAN ORCHESTRATION SERVICE (Go 1.22)                             │  ║
║  │                                                                                          │  ║
║  │  ┌─────────────────────┐  ┌──────────────────────────────────────────────────────────┐   │  ║
║  │  │  REST API            │  │  JOB SCHEDULER                                          │   │  ║
║  │  │  POST /api/v1/scans  │  │  ┌────────────────────────────────────────────────────┐  │   │  ║
║  │  │  POST /api/v1/scans/ │  │  │             PRIORITY QUEUE (Redis Sorted Set)       │  │   │  ║
║  │  │       batch          │  │  │                                                    │  │   │  ║
║  │  │  GET  /api/v1/scans/ │  │  │  Score = (10-priority)*1M + epoch_ms              │  │   │  ║
║  │  │       {id}           │  │  │                                                    │  │   │  ║
║  │  │  POST /api/v1/scans/ │  │  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │  │   │  ║
║  │  │       {id}/cancel    │  │  │  │ P=1  │ │ P=2  │ │ P=3  │ │ P=5  │ │ P=10 │   │  │   │  ║
║  │  │  POST /api/v1/scans/ │  │  │  │ Crit.│ │ High │ │ Med  │ │ Norm │ │ Low  │   │  │   │  ║
║  │  │       {id}/retry     │  │  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘   │  │   │  ║
║  │  └─────────────────────┘  │  └────────────────────────────────────────────────────┘  │   │  ║
║  │                            │                                                          │   │  ║
║  │                            │  ┌────────────────────────────────────────────────────┐  │   │  ║
║  │                            │  │        CONCURRENCY GOVERNOR                        │  │   │  ║
║  │                            │  │                                                    │  │   │  ║
║  │                            │  │  Per-tenant limits:   max_concurrent_scans         │  │   │  ║
║  │                            │  │  Per-scanner limits:  burp=5, tenable=8, fortify=4 │  │   │  ║
║  │                            │  │  Global limit:        100 concurrent scans         │  │   │  ║
║  │                            │  │  Scan window checks:  respect maintenance windows  │  │   │  ║
║  │                            │  └────────────────────────────────────────────────────┘  │   │  ║
║  │                            └──────────────────────────────────────────────────────────┘   │  ║
║  └────────────────────────────────────────────┬─────────────────────────────────────────────┘  ║
╚═══════════════════════════════════════════════╬══════════════════════════════════════════════════╝
                                                │
                                                ▼
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                               TEMPORAL.IO CLUSTER (Multi-AZ)                                  ║
║                                                                                                ║
║  ┌─────────────────────────────────────────────────────────────────────────────────────────┐   ║
║  │                         WORKFLOW ENGINE                                                 │   ║
║  │                                                                                         │   ║
║  │  Task Queue: "scan-orchestration"                                                       │   ║
║  │  ┌─────────────────────────────────────────────────────────────────────────────────────┐│   ║
║  │  │                                                                                     ││   ║
║  │  │  ┌───────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐  ││   ║
║  │  │  │ WebAppScanWorkflow    │  │ APIScanWorkflow        │  │ InfraScanWorkflow      │  ││   ║
║  │  │  │ (Burp DAST)          │  │ (Burp API mode)        │  │ (Tenable/Nessus)       │  ││   ║
║  │  │  └───────────────────────┘  └────────────────────────┘  └────────────────────────┘  ││   ║
║  │  │  ┌───────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐  ││   ║
║  │  │  │ SourceCodeScanWF     │  │ MobileStaticScanWF     │  │ MobileDynamicScanWF    │  ││   ║
║  │  │  │ (Fortify SAST/SCA)   │  │ (MobSF static)        │  │ (MobSF dynamic)        │  ││   ║
║  │  │  └───────────────────────┘  └────────────────────────┘  └────────────────────────┘  ││   ║
║  │  │                                                                                     ││   ║
║  │  │  ┌───────────────────────┐                                                          ││   ║
║  │  │  │ EngagementScanWF     │  ← Parent workflow: fans out child workflows per asset    ││   ║
║  │  │  │ (fan-out/fan-in)     │                                                           ││   ║
║  │  │  └───────────────────────┘                                                          ││   ║
║  │  └─────────────────────────────────────────────────────────────────────────────────────┘│   ║
║  │                                                                                         │   ║
║  │  Worker Pool: 5–20 pods (HPA on queue depth)                                            │   ║
║  └─────────────────────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                                ║
║  ┌──────────────────────────────────────────────────────────────────────────────────────────┐  ║
║  │                         ACTIVITY WORKERS                                                 │  ║
║  │                                                                                          │  ║
║  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌───────────────┐ ┌──────────────┐  │  ║
║  │  │ Validation   │ │ Credential   │ │ Scanner      │ │ Progress      │ │ Result       │  │  ║
║  │  │ Activities   │ │ Activities   │ │ Dispatch     │ │ Monitor       │ │ Collection   │  │  ║
║  │  │              │ │              │ │ Activities   │ │ Activities    │ │ Activities   │  │  ║
║  │  │ •ValidReq    │ │ •Checkout    │ │ •DispatchBurp│ │ •PollBurp     │ │ •CollectBurp │  │  ║
║  │  │ •CheckScope  │ │ •Checkin     │ │ •DispatchTen │ │ •PollTenable  │ │ •CollectTen  │  │  ║
║  │  │ •CheckWindow │ │ •Validate    │ │ •DispatchFort│ │ •PollFortify  │ │ •CollectFort │  │  ║
║  │  │ •CheckQuota  │ │              │ │ •DispatchMobS│ │ •PollMobSF    │ │ •CollectMobSF│  │  ║
║  │  └──────────────┘ └──────────────┘ └──────────────┘ └───────────────┘ └──────────────┘  │  ║
║  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                                     │  ║
║  │  │ Publish      │ │ Notification │ │ Cleanup      │                                     │  ║
║  │  │ Activities   │ │ Activities   │ │ Activities   │                                     │  ║
║  │  │              │ │              │ │              │                                     │  ║
║  │  │ •KafkaPublish│ │ •SendUpdate  │ │ •PurgeTempDir│                                     │  ║
║  │  │ •StoreRaw    │ │ •SLACheck    │ │ •ReleaseSlot │                                     │  ║
║  │  │ •UpdateDB    │ │ •Escalate    │ │ •Archive     │                                     │  ║
║  │  └──────────────┘ └──────────────┘ └──────────────┘                                     │  ║
║  └──────────────────────────────────────────────────────────────────────────────────────────┘  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
                        │                              │
            gRPC (mTLS) │                              │ gRPC (mTLS)
           ┌────────────┼──────────────┬───────────────┼───────────────┐
           ▼            ▼              ▼               ▼               ▼
      ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ ┌────────────┐
      │ Burp    │ │ Tenable  │ │ Fortify  │ │ MobSF        │ │ Credential │
      │ Suite   │ │ Connector│ │ Connector│ │ Connector    │ │ Vault Svc  │
      │Connector│ │          │ │          │ │              │ │            │
      └─────────┘ └──────────┘ └──────────┘ └──────────────┘ └────────────┘
```

---

## 2. Temporal Foundations

### 2.1 Shared Type Definitions

```go
// ─── Domain types used across all scan workflows ───

package workflows

import (
    "time"
    "github.com/google/uuid"
)

// ScanRequest is the canonical input for all scan workflows.
type ScanRequest struct {
    ScanJobID           uuid.UUID              `json:"scan_job_id"`
    TenantID            uuid.UUID              `json:"tenant_id"`
    EngagementID        uuid.UUID              `json:"engagement_id"`
    AssetID             uuid.UUID              `json:"asset_id"`
    TargetID            *uuid.UUID             `json:"target_id,omitempty"`
    ScanType            string                 `json:"scan_type"`       // dast, sast, sca, infrastructure, mobile_static, mobile_dynamic, api_fuzz
    ScannerEngine       string                 `json:"scanner_engine"`  // burp_suite, tenable_io, fortify_sast, fortify_sca, mobsf
    Priority            int                    `json:"priority"`        // 1 (critical) → 10 (low)
    CredentialProfileID *uuid.UUID             `json:"credential_profile_id,omitempty"`
    InitiatedBy         uuid.UUID              `json:"initiated_by"`
    Config              map[string]interface{} `json:"config"`
    MaxDurationMinutes  int                    `json:"max_duration_minutes"`
}

// ScanResult is the canonical output from all scan workflows.
type ScanResult struct {
    ScanJobID        uuid.UUID         `json:"scan_job_id"`
    Status           string            `json:"status"`     // completed, failed, cancelled, timed_out
    StartedAt        time.Time         `json:"started_at"`
    CompletedAt      time.Time         `json:"completed_at"`
    DurationSeconds  int               `json:"duration_seconds"`
    FindingSummary   FindingSummary    `json:"finding_summary"`
    RawResultPath    string            `json:"raw_result_path"`    // MinIO object key
    RawResultHash    string            `json:"raw_result_hash"`   // SHA-256
    AttemptNumber    int               `json:"attempt_number"`
    ErrorMessage     string            `json:"error_message,omitempty"`
    ScannerMetadata  map[string]string `json:"scanner_metadata"`
}

type FindingSummary struct {
    Critical int `json:"critical"`
    High     int `json:"high"`
    Medium   int `json:"medium"`
    Low      int `json:"low"`
    Info     int `json:"info"`
    Total    int `json:"total"`
}

// CredentialLease represents a time-limited credential checkout.
type CredentialLease struct {
    LeaseID             uuid.UUID `json:"lease_id"`
    CredentialProfileID uuid.UUID `json:"credential_profile_id"`
    VaultSecretPath     string    `json:"vault_secret_path"`
    VaultToken          string    `json:"vault_token"`      // wrapped, single-use
    ExpiresAt           time.Time `json:"expires_at"`
}

// ScanProgress is emitted by monitor activities.
type ScanProgress struct {
    ScanJobID       uuid.UUID `json:"scan_job_id"`
    ProgressPercent int       `json:"progress_percent"`
    Phase           string    `json:"phase"`    // crawl, audit, analysis, collecting
    Message         string    `json:"message"`
    FindingsSoFar   int       `json:"findings_so_far"`
    Timestamp       time.Time `json:"timestamp"`
}
```

### 2.2 Retry & Timeout Configuration

```go
// ─── Retry policies per activity type ───

package workflows

import (
    "time"
    "go.temporal.io/sdk/temporal"
    "go.temporal.io/sdk/workflow"
)

// ValidateActivityOptions — fast, idempotent checks.
var ValidateActivityOptions = workflow.ActivityOptions{
    StartToCloseTimeout: 30 * time.Second,
    RetryPolicy: &temporal.RetryPolicy{
        InitialInterval:    1 * time.Second,
        BackoffCoefficient: 2.0,
        MaximumInterval:    10 * time.Second,
        MaximumAttempts:    3,
        NonRetryableErrorTypes: []string{
            "ScopeViolationError",
            "EngagementStateError",
            "AssetNotFoundError",
        },
    },
}

// CredentialActivityOptions — Vault calls; slightly longer timeout.
var CredentialActivityOptions = workflow.ActivityOptions{
    StartToCloseTimeout: 60 * time.Second,
    HeartbeatTimeout:    30 * time.Second,
    RetryPolicy: &temporal.RetryPolicy{
        InitialInterval:    2 * time.Second,
        BackoffCoefficient: 2.0,
        MaximumInterval:    30 * time.Second,
        MaximumAttempts:    5,
        NonRetryableErrorTypes: []string{
            "CredentialRevokedError",
            "CredentialNotFoundError",
        },
    },
}

// DispatchActivityOptions — gRPC call to scanner connector.
var DispatchActivityOptions = workflow.ActivityOptions{
    StartToCloseTimeout: 5 * time.Minute,
    HeartbeatTimeout:    2 * time.Minute,
    RetryPolicy: &temporal.RetryPolicy{
        InitialInterval:    5 * time.Second,
        BackoffCoefficient: 2.0,
        MaximumInterval:    60 * time.Second,
        MaximumAttempts:    3,
        NonRetryableErrorTypes: []string{
            "ScannerLicenseExhaustedError",
            "TargetUnreachableError",
            "InvalidScanConfigError",
        },
    },
}

// MonitorActivityOptions — long-running poll loop; heartbeat is critical.
var MonitorActivityOptions = workflow.ActivityOptions{
    StartToCloseTimeout: 8 * time.Hour,   // max scan duration
    HeartbeatTimeout:    5 * time.Minute,  // must heartbeat or activity fails
    RetryPolicy: &temporal.RetryPolicy{
        InitialInterval:    10 * time.Second,
        BackoffCoefficient: 1.5,
        MaximumInterval:    120 * time.Second,
        MaximumAttempts:    3,
        NonRetryableErrorTypes: []string{
            "ScanCancelledError",
        },
    },
}

// CollectActivityOptions — stream results from scanner.
var CollectActivityOptions = workflow.ActivityOptions{
    StartToCloseTimeout: 30 * time.Minute,
    HeartbeatTimeout:    5 * time.Minute,
    RetryPolicy: &temporal.RetryPolicy{
        InitialInterval:    5 * time.Second,
        BackoffCoefficient: 2.0,
        MaximumInterval:    60 * time.Second,
        MaximumAttempts:    5,
    },
}

// PublishActivityOptions — Kafka publish + DB update.
var PublishActivityOptions = workflow.ActivityOptions{
    StartToCloseTimeout: 30 * time.Second,
    RetryPolicy: &temporal.RetryPolicy{
        InitialInterval:    1 * time.Second,
        BackoffCoefficient: 2.0,
        MaximumInterval:    15 * time.Second,
        MaximumAttempts:    5,
    },
}

// CleanupActivityOptions — best-effort cleanup; failure is logged, not fatal.
var CleanupActivityOptions = workflow.ActivityOptions{
    StartToCloseTimeout: 60 * time.Second,
    RetryPolicy: &temporal.RetryPolicy{
        InitialInterval:    2 * time.Second,
        BackoffCoefficient: 2.0,
        MaximumInterval:    30 * time.Second,
        MaximumAttempts:    3,
    },
}

// ─── Workflow-level timeouts (scanner-specific) ───

var WorkflowTimeouts = map[string]time.Duration{
    "burp_suite_web":    4 * time.Hour,
    "burp_suite_api":    3 * time.Hour,
    "tenable_io":        8 * time.Hour,
    "fortify_sast":      6 * time.Hour,
    "fortify_sca":       2 * time.Hour,
    "mobsf_static":      1 * time.Hour,
    "mobsf_dynamic":     2 * time.Hour,
}
```

### 2.3 Status State Machine

Every scan job follows a deterministic state machine enforced by the workflow:

```
                     ┌──────────────────────────────────────────────────────────┐
                     │                                                          │
                     │              SCAN JOB STATE MACHINE                      │
                     │                                                          │
                     │  ┌─────────┐                                             │
                     │  │ QUEUED  │ ◄─── Initial state (created by API)         │
                     │  └────┬────┘                                             │
                     │       │ Scheduler dequeues                               │
                     │       ▼                                                  │
                     │  ┌──────────────────────┐                                │
                     │  │ CREDENTIAL_CHECKOUT  │ ◄── Vault lease acquired       │
                     │  └──────────┬───────────┘                                │
                     │             │ Credentials ready                          │
                     │             ▼                                            │
                     │  ┌──────────────────────┐                                │
                     │  │ DISPATCHED           │ ◄── gRPC StartScan sent        │
                     │  └──────────┬───────────┘                                │
                     │             │ Scanner acknowledged                       │
                     │             ▼                                            │
           ┌─────────┤  ┌──────────────────────┐                                │
           │         │  │ RUNNING              │ ◄── Scanner executing          │
           │         │  │ (progress 0→100%)    │     (heartbeats + progress)    │
           │         │  └──────────┬───────────┘                                │
           │         │             │ Scanner reports done                       │
    cancel │         │             ▼                                            │
    signal │         │  ┌──────────────────────┐                                │
           │         │  │ COLLECTING_RESULTS   │ ◄── Streaming findings via     │
           │         │  │                      │     gRPC GetScanResults        │
           │         │  └──────────┬───────────┘                                │
           │         │             │ Results stored                             │
           │         │             ▼                                            │
           │         │  ┌──────────────────────┐                                │
           │         │  │ NORMALIZING          │ ◄── Raw → unified schema       │
           │         │  │                      │     (Findings Service)         │
           │         │  └──────────┬───────────┘                                │
           │         │             │                                            │
           │         │             ▼                                            │
           │         │  ┌──────────────────────┐     ┌──────────────────────┐   │
           │         │  │ ██ COMPLETED ██      │     │ ██ FAILED ██        │   │
           │         │  │                      │     │                      │   │
           │         │  │ Terminal success     │     │ Terminal after       │   │
           │         │  └──────────────────────┘     │ max retries          │   │
           │         │                               └──────────┬───────────┘   │
           │         │                                          │               │
           │         │                               ┌──────────┴───────────┐   │
           │         │                               │ Retry? attempt < max │   │
           │         │                               │ ─────────────────────│   │
           │         │                               │ Yes → back to QUEUED │   │
           │         │                               │ No  → stay FAILED   │   │
           │         │                               └──────────────────────┘   │
           │         │                                                          │
           │         │  ┌──────────────────────┐                                │
           └─────────┼─►│ ██ CANCELLED ██      │ ◄── External cancel signal    │
                     │  └──────────────────────┘                                │
                     │                                                          │
                     │  ┌──────────────────────┐                                │
                     │  │ ██ TIMED_OUT ██      │ ◄── Workflow timeout expired   │
                     │  └──────────────────────┘                                │
                     │                                                          │
                     └──────────────────────────────────────────────────────────┘

Valid transitions:
  queued                → credential_checkout | cancelled
  credential_checkout   → dispatched | failed | cancelled
  dispatched            → running | failed | cancelled
  running               → collecting_results | failed | cancelled | timed_out
  collecting_results    → normalizing | failed
  normalizing           → completed | failed
  failed                → queued (retry) | [terminal]
  completed             → [terminal]
  cancelled             → [terminal]
  timed_out             → queued (retry) | [terminal]
```

---

## 3. Workflow 1 — Web Application Scan (Burp Suite DAST)

### 3.1 Workflow Diagram

```
WebAppScanWorkflow
══════════════════════════════════════════════════════════════════════════════════════
│
│  ┌────────────────────────────────────────────────────────┐
│  │  INPUT: ScanRequest                                    │
│  │  scanner_engine: "burp_suite"                         │
│  │  scan_type: "dast"                                    │
│  │  config.profile: "crawl_and_audit_full"               │
│  │  config.target_url: "https://portal.acme.com"         │
│  │  config.excluded_paths: ["/logout", "/health"]        │
│  │  config.rate_limit_rps: 30                            │
│  │  config.max_duration_minutes: 240                     │
│  └────────────────────────────────────────────────────────┘
│
│  ── Activity 1: ValidateRequest ──────────────────────── timeout: 30s ──
│  │
│  │  ✓ Engagement exists and status ∈ {approved, in_progress}
│  │  ✓ Asset exists and status = active
│  │  ✓ Target is in-scope for engagement with scan_type = dast
│  │  ✓ Target is_reachable = true (last check < 1 hour)
│  │  ✓ Tenant concurrent scan count < max_concurrent_scans
│  │  ✓ Current time is within scan_window (if defined)
│  │  ✗ Fail → NonRetryable: ScopeViolationError / EngagementStateError
│  │
│  │  Side effects:
│  │    → UPDATE scan_jobs SET status = 'credential_checkout'
│  │    → Kafka: scan.progress { phase: "validating", progress: 5% }
│  │
│  ── Activity 2: CheckoutCredentials ──────────────────── timeout: 60s ──
│  │
│  │  2a. Checkout SCANNER credential (Burp API key)
│  │      → POST /api/v1/credentials/{burp_api_cred}/checkout
│  │      → Vault returns wrapped token, 4h TTL
│  │
│  │  2b. Checkout TARGET credential (if authenticated scan)
│  │      → POST /api/v1/credentials/{target_cred}/checkout
│  │      → Returns username/password or session token
│  │
│  │  Failure modes:
│  │    → Credential already checked out → wait 30s, retry (max 5)
│  │    → Credential expired → NonRetryable: CredentialExpiredError
│  │    → Vault unreachable → Retryable (backoff 2s, 4s, 8s, 16s, 30s)
│  │
│  │  Side effects:
│  │    → Credential audit log entry: action=checkout
│  │    → Kafka: scan.progress { phase: "credential_checkout", progress: 10% }
│  │
│  ── Activity 3: DispatchToBurp ───────────────────────── timeout: 5min ──
│  │
│  │  gRPC call: BurpConnector.StartScan(StartScanRequest{
│  │      scan_id:          scan_job_id,
│  │      target_url:       config.target_url,
│  │      scan_config_name: map_profile(config.profile),
│  │                        // "crawl_and_audit_full" → "Audit checks - all"
│  │      credentials:      { "username": ..., "password": ... },
│  │      excluded_paths:   config.excluded_paths,
│  │      options: {
│  │          max_crawl_depth: 10,
│  │          max_crawl_links: 5000,
│  │          rate_limit_rps:  config.rate_limit_rps,
│  │          custom_headers:  config.custom_headers,
│  │          scope_includes:  config.scope_includes,
│  │          scope_excludes:  config.scope_excludes,
│  │      }
│  │  })
│  │
│  │  Response: StartScanResponse{
│  │      burp_scan_id: "burp-internal-uuid",
│  │      status: "started",
│  │      estimated_duration_seconds: 12000
│  │  }
│  │
│  │  Failure modes:
│  │    → Burp Enterprise busy → Retryable (backoff 5s, 10s, 60s)
│  │    → License exhausted → NonRetryable: ScannerLicenseExhaustedError
│  │    → Target unreachable from scanner → NonRetryable: TargetUnreachableError
│  │
│  │  Side effects:
│  │    → UPDATE scan_jobs SET status='dispatched', external_scan_id=burp_scan_id
│  │    → Kafka: scan.progress { phase: "dispatched", progress: 15% }
│  │
│  ── Activity 4: MonitorBurpProgress ──────────────────── timeout: 4h ──
│  │
│  │  LOOP every 30 seconds:
│  │    gRPC call: BurpConnector.GetScanStatus(scan_id)
│  │    Response: ScanStatusResponse{
│  │        status: "crawling" | "auditing" | "succeeded" | "failed",
│  │        progress_percent: 0-100,
│  │        items_crawled: 1247,
│  │        items_audited: 823,
│  │        issue_count: 29,
│  │        elapsed_seconds: 5670
│  │    }
│  │
│  │    Heartbeat to Temporal (keeps activity alive)
│  │
│  │    On each 10% increment:
│  │      → UPDATE scan_jobs SET progress_pct = N, status = 'running'
│  │      → Kafka: scan.progress { progress: N%, phase, findings_so_far }
│  │
│  │    On status = "succeeded":
│  │      → BREAK loop, proceed to collection
│  │
│  │    On status = "failed":
│  │      → Throw ScannerExecutionError (retryable)
│  │
│  │    Cancellation check (Temporal signal):
│  │      → If CancelSignal received → gRPC BurpConnector.CancelScan()
│  │      → Throw ScanCancelledError (non-retryable)
│  │
│  │  Timeout handling:
│  │    → If elapsed > max_duration_minutes → gRPC CancelScan()
│  │    → Throw ScanTimeoutError → triggers retry or terminal TIMED_OUT
│  │
│  ── Activity 5: CollectBurpResults ───────────────────── timeout: 30min ──
│  │
│  │  gRPC call: BurpConnector.GetScanResults(scan_id)
│  │  → Server-side streaming: yields Finding messages
│  │
│  │  For each Finding:
│  │    → Accumulate into raw result batch (max 500 per write)
│  │    → Count by severity for summary
│  │    → Heartbeat to Temporal with progress
│  │
│  │  After streaming completes:
│  │    → Serialize full result set as JSON
│  │    → Compute SHA-256 hash
│  │    → Upload to MinIO: s3://scan-results/{tenant_id}/{scan_job_id}/burp_raw.json
│  │    → INSERT scan_results (raw_output, output_hash, raw_file_path, findings_extracted)
│  │
│  │  Side effects:
│  │    → UPDATE scan_jobs SET status='collecting_results', progress=90%
│  │    → Kafka: scan.progress { phase: "collecting_results", progress: 90% }
│  │
│  ── Activity 6: PublishResults ───────────────────────── timeout: 30s ──
│  │
│  │  → UPDATE scan_jobs SET
│  │        status = 'completed',
│  │        completed_at = NOW(),
│  │        duration_seconds = elapsed,
│  │        progress_pct = 100,
│  │        findings_critical = N, findings_high = N, ...,
│  │        total_findings = N
│  │
│  │  → Kafka: scan.completed {
│  │        scan_job_id, tenant_id, engagement_id, asset_id,
│  │        scanner_engine: "burp_suite",
│  │        scan_type: "dast",
│  │        raw_result_path: "s3://...",
│  │        raw_result_hash: "sha256:...",
│  │        finding_summary: { critical: 2, high: 5, medium: 12, low: 8, info: 2 },
│  │        duration_seconds: 12345
│  │    }
│  │
│  │  → This event triggers the Findings Normalization Service (async consumer)
│  │
│  ── Activity 7: CheckinCredentials ───────────────────── timeout: 60s ──
│  │
│  │  → POST /api/v1/credentials/{burp_api_cred}/checkin
│  │  → POST /api/v1/credentials/{target_cred}/checkin (if checked out)
│  │  → Credential audit log: action=checkin
│  │
│  ── Activity 8: Cleanup ──────────────────────────────── timeout: 60s ──
│  │
│  │  → Release tenant concurrency slot (Redis DECR)
│  │  → Release scanner concurrency slot (Redis DECR)
│  │  → Purge any temporary scan artifacts
│  │
│  └── RETURN ScanResult ─────────────────────────────────────────────────
│
══════════════════════════════════════════════════════════════════════════════════════
```

### 3.2 Workflow Implementation

```go
func WebAppScanWorkflow(ctx workflow.Context, req ScanRequest) (ScanResult, error) {
    logger := workflow.GetLogger(ctx)
    logger.Info("WebAppScanWorkflow started",
        "scan_job_id", req.ScanJobID,
        "target", req.Config["target_url"],
    )

    var result ScanResult
    result.ScanJobID = req.ScanJobID
    result.AttemptNumber = req.Config["attempt_number"].(int)

    // ── Set workflow-level timeout ──
    ctx, cancel := workflow.WithCancel(ctx)
    defer cancel()

    // ── Register cancel signal handler ──
    cancelCh := workflow.GetSignalChannel(ctx, "cancel-scan")
    workflow.Go(ctx, func(gCtx workflow.Context) {
        cancelCh.Receive(gCtx, nil)
        logger.Info("Cancel signal received")
        cancel()
    })

    // ── Step 1: Validate ──
    valCtx := workflow.WithActivityOptions(ctx, ValidateActivityOptions)
    err := workflow.ExecuteActivity(valCtx, ValidateRequestActivity, req).Get(ctx, nil)
    if err != nil {
        return handleWorkflowError(ctx, req, result, err, "validation")
    }

    // ── Step 2: Checkout credentials ──
    credCtx := workflow.WithActivityOptions(ctx, CredentialActivityOptions)
    var lease CredentialLease
    err = workflow.ExecuteActivity(credCtx, CheckoutCredentialsActivity, CheckoutRequest{
        TenantID:            req.TenantID,
        ScanJobID:           req.ScanJobID,
        ScannerCredentialID: getScannerCredID("burp_suite"),
        TargetCredentialID:  req.CredentialProfileID,
    }).Get(ctx, &lease)
    if err != nil {
        return handleWorkflowError(ctx, req, result, err, "credential_checkout")
    }
    // Ensure credentials are returned even on failure
    defer func() {
        cleanCtx, _ := workflow.NewDisconnectedContext(ctx)
        cleanCtx = workflow.WithActivityOptions(cleanCtx, CleanupActivityOptions)
        _ = workflow.ExecuteActivity(cleanCtx, CheckinCredentialsActivity, lease).Get(cleanCtx, nil)
    }()

    // ── Step 3: Dispatch to Burp ──
    dispCtx := workflow.WithActivityOptions(ctx, DispatchActivityOptions)
    var dispatchResult DispatchResult
    err = workflow.ExecuteActivity(dispCtx, DispatchBurpActivity, DispatchBurpRequest{
        ScanJobID:     req.ScanJobID,
        TargetURL:     req.Config["target_url"].(string),
        ScanProfile:   req.Config["profile"].(string),
        Credentials:   lease,
        ExcludedPaths: getStringSlice(req.Config, "excluded_paths"),
        Options:       req.Config,
    }).Get(ctx, &dispatchResult)
    if err != nil {
        return handleWorkflowError(ctx, req, result, err, "dispatch")
    }

    result.StartedAt = time.Now()

    // ── Step 4: Monitor progress ──
    monCtx := workflow.WithActivityOptions(ctx, MonitorActivityOptions)
    var monitorResult MonitorResult
    err = workflow.ExecuteActivity(monCtx, MonitorBurpProgressActivity, MonitorRequest{
        ScanJobID:          req.ScanJobID,
        ExternalScanID:     dispatchResult.ExternalScanID,
        MaxDurationMinutes: req.MaxDurationMinutes,
        PollIntervalSecs:   30,
        TenantID:           req.TenantID,
        EngagementID:       req.EngagementID,
    }).Get(ctx, &monitorResult)
    if err != nil {
        return handleWorkflowError(ctx, req, result, err, "monitoring")
    }

    // ── Step 5: Collect results ──
    collCtx := workflow.WithActivityOptions(ctx, CollectActivityOptions)
    var collectResult CollectResult
    err = workflow.ExecuteActivity(collCtx, CollectBurpResultsActivity, CollectRequest{
        ScanJobID:      req.ScanJobID,
        TenantID:       req.TenantID,
        ExternalScanID: dispatchResult.ExternalScanID,
    }).Get(ctx, &collectResult)
    if err != nil {
        return handleWorkflowError(ctx, req, result, err, "collection")
    }

    // ── Step 6: Publish ──
    pubCtx := workflow.WithActivityOptions(ctx, PublishActivityOptions)
    result.CompletedAt = time.Now()
    result.DurationSeconds = int(result.CompletedAt.Sub(result.StartedAt).Seconds())
    result.Status = "completed"
    result.FindingSummary = collectResult.Summary
    result.RawResultPath = collectResult.RawResultPath
    result.RawResultHash = collectResult.RawResultHash

    err = workflow.ExecuteActivity(pubCtx, PublishScanCompletedActivity, result).Get(ctx, nil)
    if err != nil {
        logger.Error("Failed to publish results", "error", err)
        // Non-fatal: scan completed, just publish failed
    }

    // ── Step 7: Cleanup (handled by defer for credentials) ──
    cleanCtx := workflow.WithActivityOptions(ctx, CleanupActivityOptions)
    _ = workflow.ExecuteActivity(cleanCtx, ReleaseConcurrencySlotActivity, req).Get(ctx, nil)

    logger.Info("WebAppScanWorkflow completed",
        "scan_job_id", req.ScanJobID,
        "findings", result.FindingSummary.Total,
        "duration", result.DurationSeconds,
    )

    return result, nil
}
```

---

## 4. Workflow 2 — API Scan (Burp Suite API Mode)

### 4.1 Workflow Diagram

```
APIScanWorkflow
══════════════════════════════════════════════════════════════════════════════════════
│
│  ┌────────────────────────────────────────────────────────┐
│  │  INPUT: ScanRequest                                    │
│  │  scanner_engine: "burp_suite"                         │
│  │  scan_type: "api_fuzz"                                │
│  │  config.profile: "api_scan"                           │
│  │  config.target_url: "https://api.acme.com/v2"         │
│  │  config.openapi_spec: "s3://specs/openapi.yaml"       │
│  │  config.auth_type: "oauth2_bearer"                    │
│  │  config.rate_limit_rps: 20                            │
│  └────────────────────────────────────────────────────────┘
│
│  ── Activity 1: ValidateRequest ──────────────────────── (same as web) ──
│
│  ── Activity 2: FetchOpenAPISpec ─────────────────────── timeout: 60s ──
│  │
│  │  → Download OpenAPI/Swagger spec from MinIO or URL
│  │  → Parse and validate spec (OpenAPI 3.0/3.1 or Swagger 2.0)
│  │  → Extract endpoint count, auth schemes, parameter types
│  │  → Fail if spec is invalid or contains > 500 endpoints (configurable)
│  │
│  │  Output: ParsedAPISpec {
│  │      endpoint_count: 87,
│  │      auth_schemes: ["bearer", "api_key"],
│  │      has_file_uploads: true,
│  │      estimated_scan_duration_min: 120
│  │  }
│  │
│  ── Activity 3: CheckoutCredentials ──────────────────── (same as web) ──
│
│  ── Activity 4: DispatchToBurpAPI ────────────────────── timeout: 5min ──
│  │
│  │  gRPC call: BurpConnector.StartScan(StartScanRequest{
│  │      scan_id:          scan_job_id,
│  │      target_url:       config.target_url,
│  │      scan_config_name: "API scan",
│  │      credentials:      { "Authorization": "Bearer ..." },
│  │      options: {
│  │          openapi_spec_content: spec_content,
│  │          api_scan_mode:        true,
│  │          crawl_mode:           "api_definition",  // not browser crawl
│  │          fuzz_parameters:      true,
│  │          rate_limit_rps:       config.rate_limit_rps,
│  │          include_methods:      ["GET","POST","PUT","PATCH","DELETE"],
│  │      }
│  │  })
│  │
│  │  Key difference from web scan:
│  │    → Uses OpenAPI spec for endpoint discovery (not crawling)
│  │    → Fuzzes all parameter types (path, query, header, body)
│  │    → Tests authentication bypass, IDOR, mass assignment
│  │    → No DOM-based checks (no browser)
│  │
│  ── Activity 5: MonitorBurpProgress ──────────────────── (same as web) ──
│  ── Activity 6: CollectBurpResults ───────────────────── (same as web) ──
│  │
│  │  Additional post-processing:
│  │    → Tag each finding with affected API endpoint (method + path)
│  │    → Map findings to OpenAPI operation IDs
│  │    → Classify: auth bypass, injection, business logic, data exposure
│  │
│  ── Activity 7: PublishResults ───────────────────────── (same as web) ──
│  ── Activity 8: CheckinCredentials ───────────────────── (same as web) ──
│  ── Activity 9: Cleanup ──────────────────────────────── (same as web) ──
│
══════════════════════════════════════════════════════════════════════════════════════
```

### 4.2 Key Differences from Web Workflow

| Aspect | Web App Scan | API Scan |
|--------|-------------|----------|
| Discovery | Browser-based crawling | OpenAPI spec parsing |
| Scope | URLs discovered by crawler | Endpoints defined in spec |
| Authentication | Session cookies, form login | OAuth2 Bearer, API keys, mTLS |
| Checks | XSS, CSRF, clickjacking, DOM | Injection, IDOR, mass assignment, auth bypass |
| Rate limiting | 30-50 RPS typical | 10-30 RPS (API rate limits) |
| Duration | 2-4 hours | 1-3 hours |
| Extra input | N/A | OpenAPI/Swagger specification |

---

## 5. Workflow 3 — Infrastructure Scan (Tenable.io / Nessus)

### 5.1 Workflow Diagram

```
InfraScanWorkflow
══════════════════════════════════════════════════════════════════════════════════════
│
│  ┌────────────────────────────────────────────────────────┐
│  │  INPUT: ScanRequest                                    │
│  │  scanner_engine: "tenable_io"                         │
│  │  scan_type: "infrastructure"                          │
│  │  config.template: "advanced"                          │
│  │  config.targets: ["10.0.1.0/24", "10.0.2.0/24"]      │
│  │  config.port_range: "1-65535"                         │
│  │  config.credential_types: ["ssh", "winrm"]           │
│  │  config.scan_window: { start: "02:00", end: "06:00" }│
│  │  config.max_duration_minutes: 480                     │
│  └────────────────────────────────────────────────────────┘
│
│  ── Activity 1: ValidateRequest ──────────────────────── timeout: 30s ──
│  │
│  │  ✓ Standard engagement/asset/scope validation
│  │  ✓ Validate all target CIDRs are within engagement scope
│  │  ✓ Ensure no target overlaps with other running scans (deconfliction)
│  │  ✓ Check scan window: if defined and current time is outside window,
│  │    SCHEDULE the workflow to start at window.start (Temporal timer)
│  │
│  │  Unique: if outside scan window →
│  │    waitDuration = time until next window.start
│  │    workflow.Sleep(ctx, waitDuration)
│  │    Re-validate after wake-up (engagement may have been cancelled)
│  │
│  ── Activity 2: CheckoutCredentials ──────────────────── timeout: 60s ──
│  │
│  │  2a. Checkout SCANNER credential (Tenable API key + secret)
│  │  2b. Checkout TARGET credentials (per credential type):
│  │      → SSH: username + private key
│  │      → WinRM: domain\username + password
│  │      → SNMP: community string or v3 credentials
│  │  2c. Validate each credential against one target host (pre-flight check)
│  │      → gRPC TenableConnector.TestCredential()
│  │      → If test fails → log warning, continue (partial cred scan)
│  │
│  ── Activity 3: DispatchToTenable ────────────────────── timeout: 5min ──
│  │
│  │  gRPC call: TenableConnector.StartScan(InfraScanRequest{
│  │      scan_id:       scan_job_id,
│  │      targets:       ["10.0.1.0/24", "10.0.2.0/24"],
│  │      scan_template: "advanced",
│  │      credentials:   { "ssh_user": "root", "ssh_key": "...", ... },
│  │      port_list:     parse_port_range("1-65535"),
│  │      options: {
│  │          enable_local_checks:  true,
│  │          safe_checks:          true,     // no DoS plugins
│  │          unscanned_closed:     false,
│  │          max_hosts_per_scan:   50,
│  │          max_checks_per_host:  5,
│  │          network_timeout:      30,
│  │      }
│  │  })
│  │
│  │  Response: StartScanResponse{
│  │      tenable_scan_id: "tenable-uuid",
│  │      scanner_name: "scanner-zone3-01",
│  │      status: "launched"
│  │  }
│  │
│  ── Activity 4: MonitorTenableProgress ───────────────── timeout: 8h ──
│  │
│  │  LOOP every 60 seconds:
│  │    gRPC call: TenableConnector.GetScanStatus(scan_id)
│  │    Response: ScanStatusResponse{
│  │        status: "running" | "completed" | "aborted" | "paused",
│  │        progress: {
│  │            total_hosts: 510,
│  │            scanned_hosts: 340,
│  │            percent_complete: 66
│  │        },
│  │        host_results: [
│  │            { host: "10.0.1.1", status: "completed", vulns: 12 },
│  │            { host: "10.0.1.2", status: "running", vulns: 3 },
│  │            ...
│  │        ]
│  │    }
│  │
│  │    Progress calculation:
│  │      scanned_hosts / total_hosts × 100 = progress_percent
│  │
│  │    Emit progress at every 10% increment
│  │
│  │    Scan window enforcement:
│  │      If current time > scan_window.end AND scan_window defined:
│  │        → gRPC TenableConnector.PauseScan()
│  │        → workflow.Sleep until next window.start
│  │        → gRPC TenableConnector.ResumeScan()
│  │
│  ── Activity 5: CollectTenableResults ────────────────── timeout: 30min ──
│  │
│  │  gRPC call: TenableConnector.GetScanResults(scan_id)
│  │  → Streams InfraFinding messages (one per plugin hit per host)
│  │
│  │  Post-processing:
│  │    → Group findings by host for per-asset reporting
│  │    → Extract CVE references, CVSS vectors
│  │    → Flag findings with exploit_available = true
│  │    → Map Tenable severity + CVSS → platform severity
│  │      • CVSS ≥ 9.0 → critical
│  │      • CVSS 7.0–8.9 → high
│  │      • CVSS 4.0–6.9 → medium
│  │      • CVSS 0.1–3.9 → low
│  │      • CVSS 0.0 or info → informational
│  │
│  │  Store raw results in MinIO:
│  │    s3://scan-results/{tenant_id}/{scan_job_id}/tenable_raw.json
│  │
│  ── Activity 6: PublishResults ───────────────────────── (same pattern) ──
│  ── Activity 7: CheckinCredentials ───────────────────── (same) ──
│  ── Activity 8: Cleanup ──────────────────────────────── (same) ──
│
══════════════════════════════════════════════════════════════════════════════════════
```

### 5.2 Infrastructure-Specific: Scan Window Enforcement

```go
// enforceScanWindow pauses/resumes scans during maintenance windows only.
func enforceScanWindow(ctx workflow.Context, window *ScanWindow, req ScanRequest) error {
    if window == nil {
        return nil // No window constraint
    }

    now := workflow.Now(ctx).UTC()
    windowStart := todayAt(now, window.Start)  // e.g., 02:00 UTC
    windowEnd   := todayAt(now, window.End)    // e.g., 06:00 UTC

    if now.Before(windowStart) {
        // Wait until window opens
        waitDuration := windowStart.Sub(now)
        workflow.GetLogger(ctx).Info("Waiting for scan window",
            "opens_in", waitDuration, "window_start", windowStart)

        _ = workflow.ExecuteActivity(
            workflow.WithActivityOptions(ctx, PublishActivityOptions),
            UpdateScanStatusActivity,
            StatusUpdate{ScanJobID: req.ScanJobID, Message: fmt.Sprintf(
                "Scan queued. Scan window opens at %s UTC.", window.Start,
            )},
        ).Get(ctx, nil)

        if err := workflow.Sleep(ctx, waitDuration); err != nil {
            return err // cancelled during sleep
        }

        // Re-validate after sleeping (engagement may have been cancelled)
        valCtx := workflow.WithActivityOptions(ctx, ValidateActivityOptions)
        return workflow.ExecuteActivity(valCtx, ValidateRequestActivity, req).Get(ctx, nil)
    }

    if now.After(windowEnd) {
        // Window closed today; sleep until tomorrow's window
        nextOpen := windowStart.Add(24 * time.Hour)
        waitDuration := nextOpen.Sub(now)
        if err := workflow.Sleep(ctx, waitDuration); err != nil {
            return err
        }
        valCtx := workflow.WithActivityOptions(ctx, ValidateActivityOptions)
        return workflow.ExecuteActivity(valCtx, ValidateRequestActivity, req).Get(ctx, nil)
    }

    // Within window — proceed
    return nil
}
```

### 5.3 Infrastructure-Specific: Deconfliction Logic

```go
// checkDeconfliction ensures no two scans target overlapping IP ranges.
func checkDeconfliction(ctx context.Context, tenantID uuid.UUID, targets []string) error {
    runningScans, err := scanRepo.ListRunning(ctx, tenantID, "infrastructure")
    if err != nil {
        return err
    }

    requestedNets := parseCIDRs(targets)

    for _, running := range runningScans {
        runningNets := parseCIDRs(running.Config.Targets)
        for _, reqNet := range requestedNets {
            for _, runNet := range runningNets {
                if reqNet.Contains(runNet.IP) || runNet.Contains(reqNet.IP) || reqNet.String() == runNet.String() {
                    return &DeconflictionError{
                        Message: fmt.Sprintf(
                            "Target %s overlaps with running scan %s (targets: %s). "+
                            "Wait for it to complete or cancel it first.",
                            reqNet.String(), running.ID, runNet.String(),
                        ),
                        ConflictingScanID: running.ID,
                    }
                }
            }
        }
    }
    return nil
}
```

---

## 6. Workflow 4 — Source Code Scan (Fortify SAST / SCA)

### 6.1 Workflow Diagram

```
SourceCodeScanWorkflow
══════════════════════════════════════════════════════════════════════════════════════
│
│  ┌────────────────────────────────────────────────────────┐
│  │  INPUT: ScanRequest                                    │
│  │  scanner_engine: "fortify_sast" | "fortify_sca"       │
│  │  scan_type: "sast" | "sca"                            │
│  │  config.repo_url: "https://github.com/acme/portal"    │
│  │  config.branch: "main"                                │
│  │  config.commit_sha: "a1b2c3d4..."                     │
│  │  config.languages: ["java", "javascript"]             │
│  │  config.exclude_patterns: ["**/test/**"]              │
│  │  config.max_duration_minutes: 360                     │
│  └────────────────────────────────────────────────────────┘
│
│  ── Activity 1: ValidateRequest ──────────────────────── timeout: 30s ──
│  │
│  │  ✓ Standard engagement/asset/scope validation
│  │  ✓ Validate repo_url is an allowed source (not arbitrary URLs)
│  │  ✓ Verify scan_type matches scanner_engine
│  │
│  ── Activity 2: CheckoutCredentials ──────────────────── timeout: 60s ──
│  │
│  │  2a. Checkout SCANNER credential (Fortify SSC API token)
│  │  2b. Checkout REPO credential (Git SSH key or HTTPS token)
│  │
│  ── Activity 3: CloneRepository ──────────────────────── timeout: 15min ──
│  │
│  │  → Create ephemeral volume (emptyDir, 10GB max)
│  │  → git clone --depth=1 --branch={branch} {repo_url} /workspace/{scan_job_id}
│  │  → If commit_sha: git checkout {commit_sha}
│  │  → Validate checkout: confirm expected files exist
│  │  → Calculate repo metrics:
│  │      total_files, total_lines, languages_detected, size_mb
│  │
│  │  Security controls:
│  │    → Clone into gVisor-sandboxed container (no network after clone)
│  │    → Strip .git directory after checkout
│  │    → Scan for secrets (pre-flight: reject if repo contains .env, credentials)
│  │
│  │  Failure modes:
│  │    → Auth failure → NonRetryable: RepoAccessDeniedError
│  │    → Repo too large (> 5GB) → NonRetryable: RepoTooLargeError
│  │    → Timeout on clone → Retryable
│  │
│  │  Side effects:
│  │    → Kafka: scan.progress { phase: "cloning_repository", progress: 15% }
│  │
│  ── Activity 4: DispatchToFortify ────────────────────── timeout: 5min ──
│  │
│  │  IF scan_type == "sast":
│  │    gRPC call: FortifyConnector.StartSASTScan(SASTScanRequest{
│  │        scan_id:     scan_job_id,
│  │        repo_url:    "internal://workspace/{scan_job_id}",  // local path
│  │        branch:      config.branch,
│  │        commit_sha:  config.commit_sha,
│  │        languages:   config.languages,
│  │        credentials: {},  // repo already cloned, no further auth needed
│  │        options: {
│  │            translation_excludes: config.exclude_patterns,
│  │            scan_central_pool:    "sast-pool-01",
│  │            memory_mb:            8192,
│  │            enable_dataflow:      true,
│  │            enable_controlflow:   true,
│  │            enable_semantic:      true,
│  │            rules_packs:          ["fortify-secure-coding"],
│  │        }
│  │    })
│  │
│  │  IF scan_type == "sca":
│  │    gRPC call: FortifyConnector.StartSCAScan(SCAScanRequest{
│  │        scan_id:        scan_job_id,
│  │        repo_url:       "internal://workspace/{scan_job_id}",
│  │        branch:         config.branch,
│  │        manifest_files: auto_detect_manifests(workspace),
│  │                        // ["pom.xml", "package.json", "requirements.txt"]
│  │        credentials:    {},
│  │    })
│  │
│  ── Activity 5: MonitorFortifyProgress ───────────────── timeout: 6h ──
│  │
│  │  SAST scan phases (monitored via polling):
│  │    1. Translation (source → Fortify IL):   0% → 30%
│  │    2. Analysis (dataflow + controlflow):  30% → 80%
│  │    3. Post-processing (rule matching):    80% → 95%
│  │    4. Upload to SSC:                      95% → 100%
│  │
│  │  SCA scan phases:
│  │    1. Dependency resolution:               0% → 40%
│  │    2. CVE database lookup:                40% → 70%
│  │    3. License analysis:                   70% → 90%
│  │    4. Report generation:                  90% → 100%
│  │
│  │  Poll interval: 30s (SAST), 15s (SCA — faster scans)
│  │
│  ── Activity 6: CollectFortifyResults ────────────────── timeout: 30min ──
│  │
│  │  gRPC call: FortifyConnector.GetScanResults(scan_id)
│  │  → Streams CodeFinding messages
│  │
│  │  Post-processing for SAST:
│  │    → Extract source→sink dataflow traces
│  │    → Map Fortify categories to CWE IDs
│  │    → Include code snippets (5 lines context)
│  │    → Classify: injection, XSS, crypto, auth, config, etc.
│  │
│  │  Post-processing for SCA:
│  │    → Resolve transitive dependency trees
│  │    → Map CVEs to specific component versions
│  │    → Flag components with known exploits (EPSS > 0.5)
│  │    → Check license compatibility
│  │
│  │  Store: s3://scan-results/{tenant_id}/{scan_job_id}/fortify_{sast|sca}_raw.json
│  │
│  ── Activity 7: PurgeWorkspace ───────────────────────── timeout: 60s ──
│  │
│  │  → Securely delete cloned source code (shred -u)
│  │  → Remove ephemeral volume
│  │  → Log workspace cleanup completion for audit trail
│  │
│  ── Activity 8: PublishResults ───────────────────────── (same pattern) ──
│  ── Activity 9: CheckinCredentials ───────────────────── (same) ──
│  ── Activity 10: Cleanup ─────────────────────────────── (same) ──
│
══════════════════════════════════════════════════════════════════════════════════════
```

### 6.2 Source Code Security: Workspace Isolation

```go
// CloneRepositoryActivity clones a repo into an isolated, ephemeral workspace.
func CloneRepositoryActivity(ctx context.Context, req CloneRequest) (CloneResult, error) {
    activity.RecordHeartbeat(ctx, "starting clone")

    workDir := filepath.Join("/workspace", req.ScanJobID.String())

    // Create isolated workspace with size limit
    if err := os.MkdirAll(workDir, 0700); err != nil {
        return CloneResult{}, fmt.Errorf("create workspace: %w", err)
    }

    // Clone with depth=1 (shallow) to minimise data transfer
    cmd := exec.CommandContext(ctx, "git", "clone",
        "--depth=1",
        "--branch", req.Branch,
        "--single-branch",
        req.RepoURL,
        workDir,
    )
    cmd.Env = append(os.Environ(),
        fmt.Sprintf("GIT_SSH_COMMAND=ssh -i %s -o StrictHostKeyChecking=no", req.SSHKeyPath),
    )

    output, err := cmd.CombinedOutput()
    if err != nil {
        if strings.Contains(string(output), "Authentication failed") {
            return CloneResult{}, temporal.NewNonRetryableApplicationError(
                "Repository authentication failed", "RepoAccessDeniedError", err)
        }
        return CloneResult{}, fmt.Errorf("git clone failed: %s: %w", output, err)
    }

    // Checkout specific commit if provided
    if req.CommitSHA != "" {
        cmd = exec.CommandContext(ctx, "git", "-C", workDir, "checkout", req.CommitSHA)
        if _, err := cmd.CombinedOutput(); err != nil {
            return CloneResult{}, fmt.Errorf("git checkout %s failed: %w", req.CommitSHA, err)
        }
    }

    // Security: remove .git directory (no history needed, prevents leaking secrets)
    os.RemoveAll(filepath.Join(workDir, ".git"))

    // Calculate metrics
    metrics := calculateRepoMetrics(workDir)

    activity.RecordHeartbeat(ctx, fmt.Sprintf("cloned: %d files, %d lines", metrics.TotalFiles, metrics.TotalLines))

    // Size guard
    if metrics.SizeMB > 5000 {
        os.RemoveAll(workDir)
        return CloneResult{}, temporal.NewNonRetryableApplicationError(
            fmt.Sprintf("Repository too large: %dMB (max 5000MB)", metrics.SizeMB),
            "RepoTooLargeError", nil)
    }

    return CloneResult{
        WorkspacePath: workDir,
        Metrics:       metrics,
    }, nil
}
```

---

## 7. Workflow 5 — Mobile App Scan (MobSF)

### 7.1 Workflow Diagram

```
MobileScanWorkflow (static + dynamic combined)
══════════════════════════════════════════════════════════════════════════════════════
│
│  ┌────────────────────────────────────────────────────────┐
│  │  INPUT: ScanRequest                                    │
│  │  scanner_engine: "mobsf"                              │
│  │  scan_type: "mobile_static" | "mobile_dynamic"        │
│  │  config.platform: "android" | "ios"                   │
│  │  config.binary_reference: "uploads/acme-v3.2.1.apk"  │
│  │  config.analysis_type: "static" | "dynamic"           │
│  │  config.max_duration_minutes: 120                     │
│  └────────────────────────────────────────────────────────┘
│
│  ════════════ STATIC ANALYSIS PATH ═══════════════════════
│  │
│  │  ── Activity 1: ValidateRequest ──────────────────────
│  │  │  ✓ Standard validation
│  │  │  ✓ Asset type = mobile_app_android | mobile_app_ios
│  │  │  ✓ Binary exists in MinIO and hash matches
│  │  │  ✓ Binary size < 500MB
│  │  │  ✓ File extension matches platform (.apk/.aab for android, .ipa for ios)
│  │  │
│  │  ── Activity 2: ValidateBinary ───────────────────── timeout: 5min ──
│  │  │
│  │  │  → Download binary from MinIO to scanner workspace
│  │  │  → Verify SHA-256 hash matches recorded hash
│  │  │  → Validate file magic bytes (APK = PK zip, IPA = zip)
│  │  │  → Antivirus scan of binary (ClamAV)
│  │  │    → If malware detected → NonRetryable: MalwareBinaryError
│  │  │
│  │  │  Security controls:
│  │  │    → Binary processed in sandboxed container
│  │  │    → No network access during analysis
│  │  │    → File size limits enforced by MinIO policy
│  │  │
│  │  ── Activity 3: UploadToMobSF ───────────────────── timeout: 10min ──
│  │  │
│  │  │  gRPC call: MobileConnector.UploadBinary(stream BinaryChunk{
│  │  │      scan_id: scan_job_id,
│  │  │      chunk_data: <binary chunks, 4MB each>,
│  │  │      total_size: file_size_bytes,
│  │  │      sha256_hash: binary_hash
│  │  │  })
│  │  │
│  │  │  Response: UploadResponse{
│  │  │      hash: "mobsf-internal-hash",
│  │  │      file_name: "acme-v3.2.1.apk",
│  │  │      status: "uploaded"
│  │  │  }
│  │  │
│  │  ── Activity 4: DispatchStaticAnalysis ───────────── timeout: 5min ──
│  │  │
│  │  │  gRPC call: MobileConnector.StartStaticAnalysis(MobileStaticRequest{
│  │  │      scan_id:     scan_job_id,
│  │  │      binary_hash: "mobsf-internal-hash",
│  │  │      platform:    "android",
│  │  │      options: {
│  │  │          decompile:          true,
│  │  │          manifest_analysis:  true,
│  │  │          code_analysis:      true,
│  │  │          binary_analysis:    true,
│  │  │          certificate_check:  true,
│  │  │          network_analysis:   true,
│  │  │      }
│  │  │  })
│  │  │
│  │  ── Activity 5: MonitorMobSFProgress ─────────────── timeout: 1h ──
│  │  │
│  │  │  Static analysis phases:
│  │  │    1. Decompilation (dex2jar, jadx):     0% → 20%
│  │  │    2. Manifest analysis:                20% → 35%
│  │  │    3. Code pattern analysis:            35% → 65%
│  │  │    4. Binary analysis (native libs):    65% → 80%
│  │  │    5. Certificate/signing check:        80% → 90%
│  │  │    6. Report compilation:               90% → 100%
│  │  │
│  │  │  Poll interval: 15 seconds (static analysis is fast)
│  │  │
│  │  ── Activity 6: CollectMobSFResults ──────────────── timeout: 10min ──
│  │  │
│  │  │  gRPC call: MobileConnector.GetScanResults(scan_id)
│  │  │  → Streams MobileFinding messages
│  │  │
│  │  │  Post-processing:
│  │  │    → Map OWASP Mobile Top 10 (M1-M10) categories
│  │  │    → Map MASVS verification categories
│  │  │    → Extract decompiled code snippets as evidence
│  │  │    → Flag hardcoded secrets (API keys, credentials in code)
│  │  │    → Check certificate pinning implementation
│  │  │    → Analyse AndroidManifest.xml permissions
│  │  │    → Check for debuggable/backup flags
│  │  │
│  │  │  Store: s3://scan-results/{tenant_id}/{scan_job_id}/mobsf_static_raw.json
│  │  │
│  │  ── Activities 7-9: Publish, Checkin, Cleanup ─── (same pattern) ──
│  │
│  ════════════ DYNAMIC ANALYSIS PATH ══════════════════════
│  │
│  │  All static activities above, PLUS:
│  │
│  │  ── Activity 6b: ProvisionEmulator ───────────────── timeout: 10min ──
│  │  │
│  │  │  → Request Android emulator from device farm pool
│  │  │  → Wait for emulator to boot (AVD with API 33/34)
│  │  │  → Install Frida server on emulator
│  │  │  → Configure proxy (mitmproxy for traffic capture)
│  │  │  → Install target APK on emulator
│  │  │
│  │  │  For iOS:
│  │  │    → Request corellium instance or jailbroken device
│  │  │    → Install Frida gadget
│  │  │    → Configure SSL kill switch
│  │  │
│  │  ── Activity 6c: DispatchDynamicAnalysis ─────────── timeout: 5min ──
│  │  │
│  │  │  gRPC call: MobileConnector.StartDynamicAnalysis(MobileDynamicRequest{
│  │  │      scan_id:     scan_job_id,
│  │  │      binary_hash: "mobsf-internal-hash",
│  │  │      platform:    "android",
│  │  │      credentials: { "username": "test@acme.com", "password": "..." },
│  │  │      options: {
│  │  │          frida_scripts:     ["ssl-pinning-bypass", "root-detection-bypass"],
│  │  │          api_monitoring:    true,
│  │  │          traffic_capture:   true,
│  │  │          runtime_analysis:  true,
│  │  │          input_fuzzing:     true,
│  │  │          duration_minutes:  60,
│  │  │      }
│  │  │  })
│  │  │
│  │  ── Activity 6d: MonitorDynamicAnalysis ──────────── timeout: 2h ──
│  │  │
│  │  │  Dynamic analysis phases:
│  │  │    1. App launch + instrumentation:       0% → 10%
│  │  │    2. Automated interaction (UI monkey):  10% → 40%
│  │  │    3. API call monitoring:               40% → 60%
│  │  │    4. Runtime analysis (Frida hooks):    60% → 80%
│  │  │    5. Traffic analysis:                  80% → 90%
│  │  │    6. Report compilation:                90% → 100%
│  │  │
│  │  ── Activity 6e: CollectDynamicResults ───────────── timeout: 10min ──
│  │  │
│  │  │  Additional artefacts collected:
│  │  │    → Network traffic capture (PCAP, filtered)
│  │  │    → API call log with request/response bodies
│  │  │    → Screenshots at key interaction points
│  │  │    → Frida hook outputs (hooked function calls)
│  │  │    → File system changes (created/modified files)
│  │  │    → SharedPreferences / Keychain dump
│  │  │
│  │  │  Store: s3://scan-results/{tenant_id}/{scan_job_id}/mobsf_dynamic_raw.json
│  │  │
│  │  ── Activity 6f: DestroyEmulator ─────────────────── timeout: 5min ──
│  │  │
│  │  │  → Terminate emulator instance
│  │  │  → Wipe emulator disk image
│  │  │  → Return device to pool
│  │  │  → Purge traffic captures from proxy
│  │  │
│  │  ── Merge static + dynamic findings ──────────────────────────────
│  │  ── Continue with Activities 7-9 ─────────────────────────────────
│
══════════════════════════════════════════════════════════════════════════════════════
```

---

## 8. Job Scheduling Logic

### 8.1 Priority Queue Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           JOB SCHEDULER                                          │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │  Redis Sorted Set: "scan:queue"                                            │  │
│  │                                                                            │  │
│  │  Score formula:                                                            │  │
│  │    score = (10 - priority) × 1,000,000,000 + unix_epoch_ms                │  │
│  │                                                                            │  │
│  │  Higher priority → higher score → dequeued first.                         │  │
│  │  Equal priority → FIFO (earlier epoch_ms = higher score within bracket).  │  │
│  │                                                                            │  │
│  │  Example (dequeue order: top to bottom):                                  │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐    │  │
│  │  │  Score: 9,001,710,936,000  │ P=1 (critical) │ ENG-2026-0001     │    │  │
│  │  │  Score: 8,001,710,935,500  │ P=2 (high)     │ ENG-2026-0042     │    │  │
│  │  │  Score: 8,001,710,936,200  │ P=2 (high)     │ ENG-2026-0015     │    │  │
│  │  │  Score: 5,001,710,934,000  │ P=5 (normal)   │ ENG-2026-0099     │    │  │
│  │  │  Score: 5,001,710,937,000  │ P=5 (normal)   │ ENG-2026-0101     │    │  │
│  │  │  Score: 0,001,710,930,000  │ P=10 (low)     │ ENG-2026-0200     │    │  │
│  │  └────────────────────────────────────────────────────────────────────┘    │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │  Scheduler Loop (runs in Scan Orchestration Service, every 1s)            │  │
│  │                                                                            │  │
│  │  LOOP:                                                                    │  │
│  │    1. ZPOPMAX scan:queue → get highest-priority job                       │  │
│  │    2. Check concurrency gates:                                            │  │
│  │       a. Global:  GET scan:slots:global < 100                             │  │
│  │       b. Tenant:  GET scan:slots:tenant:{tid} < customer.max_concurrent   │  │
│  │       c. Scanner: GET scan:slots:scanner:{engine} < scanner_limit         │  │
│  │    3. If ALL gates pass:                                                  │  │
│  │       → INCR scan:slots:global                                            │  │
│  │       → INCR scan:slots:tenant:{tid}                                      │  │
│  │       → INCR scan:slots:scanner:{engine}                                  │  │
│  │       → Start Temporal workflow                                            │  │
│  │    4. If ANY gate fails:                                                   │  │
│  │       → ZADD scan:queue {score} {job} (re-enqueue)                        │  │
│  │       → Sleep 5s before retrying this tenant/scanner                      │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │  Concurrency Limits                                                       │  │
│  │                                                                            │  │
│  │  ┌──────────────────┬──────────────────┬──────────────────────────────┐   │  │
│  │  │ Gate             │ Key              │ Default Limit                │   │  │
│  │  ├──────────────────┼──────────────────┼──────────────────────────────┤   │  │
│  │  │ Global           │ scan:slots:global│ 100                          │   │  │
│  │  │ Per-tenant       │ scan:slots:t:{id}│ customer.max_concurrent_scans│   │  │
│  │  │ Burp Suite       │ scan:slots:s:burp│ 5  (license-bound)          │   │  │
│  │  │ Tenable.io       │ scan:slots:s:ten │ 8  (API rate limit)         │   │  │
│  │  │ Fortify SAST     │ scan:slots:s:fsas│ 4  (ScanCentral agents)     │   │  │
│  │  │ Fortify SCA      │ scan:slots:s:fsca│ 6  (lighter weight)         │   │  │
│  │  │ MobSF Static     │ scan:slots:s:mobs│ 4  (CPU-bound)              │   │  │
│  │  │ MobSF Dynamic    │ scan:slots:s:mobd│ 2  (emulator-bound)         │   │  │
│  │  └──────────────────┴──────────────────┴──────────────────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Scheduler Implementation

```go
// scanScheduler dequeues scan jobs from Redis and starts Temporal workflows.
type scanScheduler struct {
    redis          *redis.Client
    temporal       client.Client
    scanRepo       ScanRepository
    customerRepo   CustomerRepository
    logger         *slog.Logger
}

func (s *scanScheduler) Run(ctx context.Context) error {
    ticker := time.NewTicker(1 * time.Second)
    defer ticker.Stop()

    for {
        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-ticker.C:
            if err := s.dequeueAndDispatch(ctx); err != nil {
                s.logger.Error("scheduler iteration failed", "error", err)
            }
        }
    }
}

func (s *scanScheduler) dequeueAndDispatch(ctx context.Context) error {
    // Pop highest-priority job (atomic operation)
    results, err := s.redis.ZPopMax(ctx, "scan:queue", 1).Result()
    if err != nil || len(results) == 0 {
        return nil // empty queue
    }

    job := deserializeScanJob(results[0].Member.(string))
    score := results[0].Score

    // ── Gate 1: Global concurrency ──
    globalSlots, _ := s.redis.Get(ctx, "scan:slots:global").Int()
    if globalSlots >= GlobalMaxConcurrent {
        s.requeue(ctx, job, score)
        return nil
    }

    // ── Gate 2: Tenant concurrency ──
    tenantKey := fmt.Sprintf("scan:slots:tenant:%s", job.TenantID)
    tenantSlots, _ := s.redis.Get(ctx, tenantKey).Int()
    customer, _ := s.customerRepo.Get(ctx, job.TenantID)
    if tenantSlots >= customer.MaxConcurrentScans {
        s.requeue(ctx, job, score)
        return nil
    }

    // ── Gate 3: Scanner concurrency ──
    scannerKey := fmt.Sprintf("scan:slots:scanner:%s", job.ScannerEngine)
    scannerSlots, _ := s.redis.Get(ctx, scannerKey).Int()
    if scannerSlots >= ScannerLimits[job.ScannerEngine] {
        s.requeue(ctx, job, score)
        return nil
    }

    // ── All gates passed: acquire slots ──
    pipe := s.redis.Pipeline()
    pipe.Incr(ctx, "scan:slots:global")
    pipe.Incr(ctx, tenantKey)
    pipe.Incr(ctx, scannerKey)
    if _, err := pipe.Exec(ctx); err != nil {
        s.requeue(ctx, job, score)
        return fmt.Errorf("acquire slots: %w", err)
    }

    // ── Start Temporal workflow ──
    workflowID := fmt.Sprintf("scan-%s-%s", job.ScannerEngine, job.ScanJobID)
    workflowType := selectWorkflow(job.ScanType, job.ScannerEngine)

    _, err = s.temporal.ExecuteWorkflow(ctx, client.StartWorkflowOptions{
        ID:        workflowID,
        TaskQueue: "scan-orchestration",
    }, workflowType, job.ToScanRequest())

    if err != nil {
        // Release slots on failure
        pipe = s.redis.Pipeline()
        pipe.Decr(ctx, "scan:slots:global")
        pipe.Decr(ctx, tenantKey)
        pipe.Decr(ctx, scannerKey)
        pipe.Exec(ctx)
        return fmt.Errorf("start workflow: %w", err)
    }

    // Update database record
    s.scanRepo.Update(ctx, job.ScanJobID, map[string]interface{}{
        "status":               "dispatched",
        "temporal_workflow_id": workflowID,
    })

    s.logger.Info("scan dispatched",
        "scan_job_id", job.ScanJobID,
        "scanner", job.ScannerEngine,
        "priority", job.Priority,
        "workflow_id", workflowID,
    )

    return nil
}

func selectWorkflow(scanType, scanner string) interface{} {
    switch {
    case scanner == "burp_suite" && scanType == "dast":
        return WebAppScanWorkflow
    case scanner == "burp_suite" && scanType == "api_fuzz":
        return APIScanWorkflow
    case scanner == "tenable_io":
        return InfraScanWorkflow
    case scanner == "fortify_sast" || scanner == "fortify_sca":
        return SourceCodeScanWorkflow
    case scanner == "mobsf":
        return MobileScanWorkflow
    default:
        return GenericScanWorkflow
    }
}
```

### 8.3 Engagement Fan-Out Workflow

When an engagement is launched, a parent workflow fans out to child workflows per asset/scan-type:

```go
// EngagementScanWorkflow launches all scans for an engagement.
func EngagementScanWorkflow(ctx workflow.Context, req EngagementLaunchRequest) (EngagementScanResult, error) {
    logger := workflow.GetLogger(ctx)
    logger.Info("EngagementScanWorkflow started", "engagement_id", req.EngagementID)

    var result EngagementScanResult
    result.EngagementID = req.EngagementID

    // ── Resolve scope: get all in-scope asset+scantype pairs ──
    valCtx := workflow.WithActivityOptions(ctx, ValidateActivityOptions)
    var scopeItems []ScopeItem
    err := workflow.ExecuteActivity(valCtx, ResolveScopeActivity, req).Get(ctx, &scopeItems)
    if err != nil {
        return result, err
    }

    logger.Info("Scope resolved", "scan_count", len(scopeItems))

    // ── Fan out: launch a child workflow per scan ──
    var futures []workflow.Future
    var scanJobIDs []uuid.UUID

    for _, item := range scopeItems {
        scanJob, err := createScanJobRecord(ctx, req, item)
        if err != nil {
            continue
        }
        scanJobIDs = append(scanJobIDs, scanJob.ID)

        childCtx := workflow.WithChildOptions(ctx, workflow.ChildWorkflowOptions{
            WorkflowID: fmt.Sprintf("scan-%s-%s", item.ScannerEngine, scanJob.ID),
            TaskQueue:  "scan-orchestration",
        })

        workflowFn := selectWorkflow(item.ScanType, item.ScannerEngine)
        future := workflow.ExecuteChildWorkflow(childCtx, workflowFn, scanJob.ToScanRequest())
        futures = append(futures, future)
    }

    // ── Fan in: collect results ──
    for i, future := range futures {
        var scanResult ScanResult
        if err := future.Get(ctx, &scanResult); err != nil {
            logger.Error("Child scan failed",
                "scan_job_id", scanJobIDs[i],
                "error", err,
            )
            result.FailedScans++
        } else {
            result.CompletedScans++
            result.TotalFindings += scanResult.FindingSummary.Total
        }
    }

    result.Status = "completed"
    if result.FailedScans > 0 && result.CompletedScans == 0 {
        result.Status = "failed"
    } else if result.FailedScans > 0 {
        result.Status = "partially_completed"
    }

    // ── Update engagement status ──
    pubCtx := workflow.WithActivityOptions(ctx, PublishActivityOptions)
    _ = workflow.ExecuteActivity(pubCtx, UpdateEngagementStatusActivity, UpdateEngagementRequest{
        EngagementID: req.EngagementID,
        Status:       "review",
        ScanSummary:  result,
    }).Get(ctx, nil)

    return result, nil
}
```

---

## 9. Scan Retry Mechanisms

### 9.1 Retry Decision Tree

```
Scan Failed
    │
    ├── Is error Non-Retryable?
    │   │
    │   ├── YES (ScopeViolation, CredentialRevoked, LicenseExhausted,
    │   │        TargetUnreachable, MalwareBinary, RepoAccessDenied)
    │   │   │
    │   │   └── ██ TERMINAL FAILURE ██
    │   │       → UPDATE scan_jobs SET status='failed', error_message=...
    │   │       → Kafka: scan.failed { reason, non_retryable: true }
    │   │       → Notification: alert lead analyst
    │   │
    │   └── NO (retryable error)
    │       │
    │       ├── attempt_number < max_attempts (default 3)?
    │       │   │
    │       │   ├── YES
    │       │   │   │
    │       │   │   ├── Calculate backoff:
    │       │   │   │   attempt 1 → 30 seconds
    │       │   │   │   attempt 2 → 120 seconds (2 minutes)
    │       │   │   │   attempt 3 → 300 seconds (5 minutes)
    │       │   │   │
    │       │   │   ├── Determine retry strategy based on failure phase:
    │       │   │   │
    │       │   │   │   credential_checkout failed:
    │       │   │   │     → Retry from credential_checkout
    │       │   │   │     → Skip validation (already passed)
    │       │   │   │
    │       │   │   │   dispatch failed:
    │       │   │   │     → Retry from dispatch
    │       │   │   │     → Reuse credentials if lease still valid
    │       │   │   │
    │       │   │   │   monitoring failed (scanner crash):
    │       │   │   │     → Full restart from dispatch
    │       │   │   │     → Fresh credential checkout
    │       │   │   │
    │       │   │   │   collection failed:
    │       │   │   │     → Retry collection only
    │       │   │   │     → Scanner results may still be available
    │       │   │   │
    │       │   │   │   timeout:
    │       │   │   │     → Increase max_duration by 50%
    │       │   │   │     → Full restart from dispatch
    │       │   │   │
    │       │   │   └── → UPDATE scan_jobs SET
    │       │   │           status='queued',
    │       │   │           retry_count=retry_count+1,
    │       │   │           last_error=error_message
    │       │   │       → Re-enqueue to priority queue (same priority)
    │       │   │       → Kafka: scan.retrying { attempt, backoff, reason }
    │       │   │
    │       │   └── NO (max attempts exhausted)
    │       │       │
    │       │       └── ██ TERMINAL FAILURE ██
    │       │           → UPDATE scan_jobs SET status='failed'
    │       │           → Kafka: scan.failed { reason, attempts_exhausted: true }
    │       │           → Notification: escalate to lead analyst
    │       │           → Create work item for manual investigation
    │       │
    │       └── (unreachable)
    │
    └── Was it a cancellation?
        │
        └── ██ CANCELLED ██
            → No retry
            → Credentials returned
            → Slots released
```

### 9.2 Retry Implementation

```go
// handleWorkflowError handles failure at any workflow step and implements retry.
func handleWorkflowError(
    ctx workflow.Context,
    req ScanRequest,
    result ScanResult,
    err error,
    phase string,
) (ScanResult, error) {
    logger := workflow.GetLogger(ctx)

    // ── Check for non-retryable errors ──
    var appErr *temporal.ApplicationError
    if errors.As(err, &appErr) && appErr.NonRetryable() {
        result.Status = "failed"
        result.ErrorMessage = fmt.Sprintf("[%s] %s (non-retryable)", phase, appErr.Message())

        // Record terminal failure
        pubCtx := workflow.WithActivityOptions(ctx, PublishActivityOptions)
        _ = workflow.ExecuteActivity(pubCtx, RecordScanFailureActivity, FailureRecord{
            ScanJobID:    req.ScanJobID,
            Phase:        phase,
            Error:        result.ErrorMessage,
            IsRetryable:  false,
            AttemptNum:   result.AttemptNumber,
        }).Get(ctx, nil)

        logger.Error("Scan failed (non-retryable)", "phase", phase, "error", err)
        return result, err
    }

    // ── Check retry budget ──
    maxAttempts := req.Config["max_retries"].(int)
    if maxAttempts == 0 {
        maxAttempts = 3
    }

    if result.AttemptNumber >= maxAttempts {
        result.Status = "failed"
        result.ErrorMessage = fmt.Sprintf("[%s] %s (attempts exhausted: %d/%d)",
            phase, err.Error(), result.AttemptNumber, maxAttempts)

        pubCtx := workflow.WithActivityOptions(ctx, PublishActivityOptions)
        _ = workflow.ExecuteActivity(pubCtx, RecordScanFailureActivity, FailureRecord{
            ScanJobID:       req.ScanJobID,
            Phase:           phase,
            Error:           result.ErrorMessage,
            IsRetryable:     false,
            AttemptNum:      result.AttemptNumber,
            AttemptsExhausted: true,
        }).Get(ctx, nil)

        // Escalation: create work item for manual investigation
        _ = workflow.ExecuteActivity(pubCtx, EscalateScanFailureActivity, EscalationRequest{
            ScanJobID:    req.ScanJobID,
            TenantID:     req.TenantID,
            EngagementID: req.EngagementID,
            Error:        result.ErrorMessage,
            Phase:        phase,
            Attempts:     result.AttemptNumber,
        }).Get(ctx, nil)

        logger.Error("Scan failed (attempts exhausted)", "phase", phase, "attempts", result.AttemptNumber)
        return result, err
    }

    // ── Calculate backoff ──
    backoffTable := []time.Duration{30 * time.Second, 120 * time.Second, 300 * time.Second}
    backoff := backoffTable[min(result.AttemptNumber-1, len(backoffTable)-1)]

    logger.Warn("Scan failed, scheduling retry",
        "phase", phase,
        "attempt", result.AttemptNumber,
        "backoff", backoff,
        "error", err,
    )

    // Record retry
    pubCtx := workflow.WithActivityOptions(ctx, PublishActivityOptions)
    _ = workflow.ExecuteActivity(pubCtx, RecordScanRetryActivity, RetryRecord{
        ScanJobID:  req.ScanJobID,
        Phase:      phase,
        Error:      err.Error(),
        AttemptNum: result.AttemptNumber,
        NextAttemptAfter: backoff,
    }).Get(ctx, nil)

    // Sleep before retry
    if err := workflow.Sleep(ctx, backoff); err != nil {
        return result, err // cancelled during sleep
    }

    // Return a ContinueAsNew error to restart the workflow with incremented attempt
    req.Config["attempt_number"] = result.AttemptNumber + 1

    // Adjust timeout on retry for timeout failures
    if phase == "monitoring" && strings.Contains(err.Error(), "timeout") {
        newMax := int(float64(req.MaxDurationMinutes) * 1.5)
        if newMax > maxDurationCap(req.ScannerEngine) {
            newMax = maxDurationCap(req.ScannerEngine)
        }
        req.MaxDurationMinutes = newMax
    }

    return result, workflow.NewContinueAsNewError(ctx, selectWorkflow(req.ScanType, req.ScannerEngine), req)
}
```

---

## 10. Status Tracking

### 10.1 Real-Time Progress Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         STATUS TRACKING DATA FLOW                                   │
│                                                                                     │
│  Temporal Workflow                                                                  │
│  (Activity heartbeats)                                                              │
│       │                                                                             │
│       │  1. Activity heartbeats contain ScanProgress struct                         │
│       ▼                                                                             │
│  ┌─────────────────┐                                                                │
│  │ Progress Store  │  2. Written on each heartbeat                                  │
│  │ (Redis)         │     Key: scan:progress:{scan_job_id}                           │
│  │                 │     Value: { percent, phase, message, findings_so_far, ts }    │
│  │                 │     TTL: 1 hour                                                │
│  └────────┬────────┘                                                                │
│           │                                                                         │
│           │  3. Every 10% increment:                                                │
│           │                                                                         │
│           ├──────────────────────────────────────────┐                               │
│           │                                          │                               │
│           ▼                                          ▼                               │
│  ┌─────────────────┐                        ┌─────────────────┐                     │
│  │ PostgreSQL      │                        │ Kafka           │                     │
│  │ (scan_jobs)     │                        │ scan.progress   │                     │
│  │                 │                        │ topic           │                     │
│  │ UPDATE          │                        │                 │                     │
│  │  progress_pct   │                        │ Consumed by:    │                     │
│  │  status         │                        │  • MCP Server   │                     │
│  │  updated_at     │                        │    (→ SSE to    │                     │
│  └─────────────────┘                        │     clients)    │                     │
│                                              │  • Engagement   │                     │
│                                              │    Service      │                     │
│                                              └─────────────────┘                     │
│                                                                                     │
│  Polling path (REST API):                                                           │
│    GET /api/v1/scans/{id}                                                           │
│      → Read from Redis first (fresh heartbeat data)                                 │
│      → Fallback to PostgreSQL (last persisted state)                                │
│                                                                                     │
│  Subscription path (MCP Resources):                                                 │
│    vapt://scans/{id}/status                                                         │
│      → MCP Server Kafka consumer receives scan.progress                             │
│      → Pushes notifications/resources/updated to subscribed clients                 │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Progress Recording Implementation

```go
// MonitorBurpProgressActivity polls Burp and emits progress updates.
func MonitorBurpProgressActivity(ctx context.Context, req MonitorRequest) (MonitorResult, error) {
    logger := activity.GetLogger(ctx)

    var lastReportedPercent int
    startTime := time.Now()

    for {
        select {
        case <-ctx.Done():
            return MonitorResult{}, ctx.Err()
        default:
        }

        // Poll scanner via gRPC
        status, err := burpClient.GetScanStatus(ctx, &pb.ScanStatusRequest{
            ScanId: req.ExternalScanID,
        })
        if err != nil {
            logger.Warn("Poll failed, will retry", "error", err)
            time.Sleep(30 * time.Second)
            continue
        }

        currentPercent := int(status.ProgressPercent)
        phase := mapBurpPhase(status.Status) // "crawling" → "crawl", "auditing" → "audit"
        elapsed := int(time.Since(startTime).Seconds())

        // ── Heartbeat to Temporal (keeps activity alive) ──
        activity.RecordHeartbeat(ctx, ScanProgress{
            ScanJobID:       req.ScanJobID,
            ProgressPercent: currentPercent,
            Phase:           phase,
            Message:         fmt.Sprintf("%s: %d%% (%d items)", phase, currentPercent, status.ItemsAudited),
            FindingsSoFar:   int(status.IssueCount),
            Timestamp:       time.Now(),
        })

        // ── Write to Redis for fast polling ──
        progressData, _ := json.Marshal(ScanProgress{
            ScanJobID:       req.ScanJobID,
            ProgressPercent: currentPercent,
            Phase:           phase,
            FindingsSoFar:   int(status.IssueCount),
            Timestamp:       time.Now(),
        })
        redisClient.Set(ctx,
            fmt.Sprintf("scan:progress:%s", req.ScanJobID),
            progressData,
            1*time.Hour,
        )

        // ── Emit on every 10% increment ──
        if currentPercent/10 > lastReportedPercent/10 {
            // Persist to PostgreSQL
            scanRepo.UpdateProgress(ctx, req.ScanJobID, currentPercent, phase)

            // Publish to Kafka
            kafkaProducer.Publish(ctx, "scan.progress", ScanProgressEvent{
                ScanJobID:       req.ScanJobID,
                TenantID:        req.TenantID,
                EngagementID:    req.EngagementID,
                ProgressPercent: currentPercent,
                Phase:           phase,
                FindingsSoFar:   int(status.IssueCount),
                ElapsedSeconds:  elapsed,
            })

            lastReportedPercent = currentPercent
        }

        // ── Check terminal states ──
        switch status.Status {
        case "succeeded":
            return MonitorResult{
                FinalStatus:    "completed",
                TotalFindings:  int(status.IssueCount),
                DurationSeconds: elapsed,
            }, nil
        case "failed":
            return MonitorResult{}, fmt.Errorf("scanner reported failure: %s", status.ErrorMessage)
        }

        // ── Timeout check ──
        if elapsed > req.MaxDurationMinutes*60 {
            // Force cancel the scan at the scanner
            burpClient.CancelScan(ctx, &pb.CancelScanRequest{ScanId: req.ExternalScanID})
            return MonitorResult{}, &ScanTimeoutError{
                Elapsed:    elapsed,
                MaxAllowed: req.MaxDurationMinutes * 60,
            }
        }

        time.Sleep(time.Duration(req.PollIntervalSecs) * time.Second)
    }
}
```

### 10.3 Status Dashboard Query (used by REST API and MCP resource)

```sql
-- Real-time scan dashboard for an engagement
-- Falls back to PostgreSQL when Redis progress is stale

SELECT
    sj.id                AS scan_job_id,
    sj.scan_type,
    sj.scanner_engine,
    sj.status,
    sj.progress_pct,
    sj.priority,
    sj.queued_at,
    sj.started_at,
    sj.completed_at,
    EXTRACT(EPOCH FROM (COALESCE(sj.completed_at, NOW()) - sj.started_at))::INT
                         AS elapsed_seconds,
    sj.attempt_number,
    sj.max_attempts,
    sj.last_error,
    sj.findings_critical,
    sj.findings_high,
    sj.findings_medium,
    sj.findings_low,
    sj.findings_info,
    sj.total_findings,
    a.name               AS asset_name,
    a.identifier         AS asset_identifier,
    t.host               AS target_host,
    t.port               AS target_port,
    t.url                AS target_url,
    sj.temporal_workflow_id
FROM scan_jobs sj
JOIN assets a ON a.id = sj.asset_id
LEFT JOIN targets t ON t.id = sj.target_id
WHERE sj.engagement_id = $1
  AND sj.customer_id = $2
ORDER BY
    CASE sj.status
        WHEN 'running' THEN 1
        WHEN 'collecting_results' THEN 2
        WHEN 'dispatched' THEN 3
        WHEN 'credential_checkout' THEN 4
        WHEN 'queued' THEN 5
        WHEN 'completed' THEN 6
        WHEN 'failed' THEN 7
        WHEN 'cancelled' THEN 8
        WHEN 'timed_out' THEN 9
    END,
    sj.priority ASC,
    sj.queued_at ASC;
```

---

## 11. Result Ingestion Pipeline

### 11.1 End-to-End Ingestion Flow

```
Scanner Connector                   Scan Orchestration              Kafka                Findings Service
═══════════════                     ══════════════════              ═════                ════════════════
      │                                     │                        │                        │
      │  gRPC GetScanResults()              │                        │                        │
      │◄────────────────────────────────────│                        │                        │
      │                                     │                        │                        │
      │  stream Finding { ... }             │                        │                        │
      │  stream Finding { ... }             │                        │                        │
      │  stream Finding { ... }             │                        │                        │
      │────────────────────────────────────►│                        │                        │
      │                                     │                        │                        │
      │                                     │  Batch & serialize     │                        │
      │                                     │  ┌────────────────┐    │                        │
      │                                     │  │ Raw JSON blob   │    │                        │
      │                                     │  │ SHA-256 hash    │    │                        │
      │                                     │  └────────┬───────┘    │                        │
      │                                     │           │            │                        │
      │                                     │  Upload to MinIO       │                        │
      │                                     │  s3://scan-results/    │                        │
      │                                     │    {tenant}/{job}/     │                        │
      │                                     │    raw.json            │                        │
      │                                     │           │            │                        │
      │                                     │  INSERT scan_results   │                        │
      │                                     │  (raw_output, hash,    │                        │
      │                                     │   file_path, count)    │                        │
      │                                     │           │            │                        │
      │                                     │  Kafka: scan.completed │                        │
      │                                     │──────────────────────►│                        │
      │                                     │                        │                        │
      │                                     │                        │  Consumer receives     │
      │                                     │                        │──────────────────────►│
      │                                     │                        │                        │
      │                                     │                        │  ┌─────────────────┐  │
      │                                     │                        │  │ INGESTION PIPELINE│  │
      │                                     │                        │  │                   │  │
      │                                     │                        │  │ 1. Download raw   │  │
      │                                     │                        │  │    from MinIO     │  │
      │                                     │                        │  │                   │  │
      │                                     │                        │  │ 2. Verify hash    │  │
      │                                     │                        │  │    (integrity)    │  │
      │                                     │                        │  │                   │  │
      │                                     │                        │  │ 3. Parse by       │  │
      │                                     │                        │  │    scanner type   │  │
      │                                     │                        │  │    (Burp/Tenable/ │  │
      │                                     │                        │  │     Fortify/MobSF)│  │
      │                                     │                        │  │                   │  │
      │                                     │                        │  │ 4. Normalize to   │  │
      │                                     │                        │  │    unified schema │  │
      │                                     │                        │  │                   │  │
      │                                     │                        │  │ 5. Severity map   │  │
      │                                     │                        │  │    (CVSS 3.1/4.0) │  │
      │                                     │                        │  │                   │  │
      │                                     │                        │  │ 6. CWE/CVE enrich │  │
      │                                     │                        │  │                   │  │
      │                                     │                        │  │ 7. Fingerprint    │  │
      │                                     │                        │  │    generation     │  │
      │                                     │                        │  │                   │  │
      │                                     │                        │  │ 8. Deduplication  │  │
      │                                     │                        │  │    check          │  │
      │                                     │                        │  │                   │  │
      │                                     │                        │  │ 9. INSERT findings│  │
      │                                     │                        │  │                   │  │
      │                                     │                        │  │10. AI enrichment  │  │
      │                                     │                        │  │    (async)        │  │
      │                                     │                        │  │                   │  │
      │                                     │                        │  │11. Kafka:         │  │
      │                                     │                        │  │    finding        │  │
      │                                     │                        │  │    .normalized    │  │
      │                                     │                        │  └─────────────────┘  │
      │                                     │                        │                        │
      │                                     │                        │  12. UPDATE            │
      │                                     │                        │      scan_results      │
      │                                     │                        │      is_parsed=true    │
      │                                     │                        │      parsed_at=NOW()   │
      │                                     │                        │                        │
```

### 11.2 Scanner-Specific Normalisation Rules

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│                           NORMALISATION MATRIX                                                │
│                                                                                               │
│  ┌─────────────┬────────────────────────────────────────────────────────────────────────────┐ │
│  │ Scanner     │ Normalisation Rules                                                       │ │
│  ├─────────────┼────────────────────────────────────────────────────────────────────────────┤ │
│  │             │                                                                            │ │
│  │ Burp Suite  │ Severity: high+certain→critical, high+firm→high, high+tentative→medium    │ │
│  │ (DAST)      │ Location: url + path + parameter + method                                 │ │
│  │             │ Evidence: HTTP request/response pairs, DOM snapshots                       │ │
│  │             │ CWE:      Burp issue_type → CWE mapping table (300+ mappings)             │ │
│  │             │ Dedup:    SHA256(tenant + category + url + parameter + cwe)                │ │
│  │             │ OWASP:    Burp category → OWASP Top 10 2021 mapping                       │ │
│  │             │                                                                            │ │
│  ├─────────────┼────────────────────────────────────────────────────────────────────────────┤ │
│  │             │                                                                            │ │
│  │ Tenable     │ Severity: CVSS ≥9.0→critical, 7.0-8.9→high, 4.0-6.9→medium,             │ │
│  │ (Infra)     │           0.1-3.9→low, info→informational                                 │ │
│  │             │ Location: host + port + protocol + plugin_id                               │ │
│  │             │ Evidence: plugin_output, compliance check details                          │ │
│  │             │ CVE:      Direct from Tenable plugin database                              │ │
│  │             │ Dedup:    SHA256(tenant + plugin_id + host + port)                         │ │
│  │             │ Exploit:  exploit_available flag → set ai_exploitability boost             │ │
│  │             │                                                                            │ │
│  ├─────────────┼────────────────────────────────────────────────────────────────────────────┤ │
│  │             │                                                                            │ │
│  │ Fortify     │ Severity: critical+high_confidence→critical, high→high,                   │ │
│  │ (SAST)      │           medium→medium, low→low                                          │ │
│  │             │ Location: file_path + line_number + function_name                          │ │
│  │             │ Evidence: code_snippet (5 lines), dataflow trace (source→sink)             │ │
│  │             │ CWE:      Direct from Fortify category database                            │ │
│  │             │ Dedup:    SHA256(tenant + category + file + function + cwe)                │ │
│  │             │ Context:  Include data_flow as structured evidence                         │ │
│  │             │                                                                            │ │
│  ├─────────────┼────────────────────────────────────────────────────────────────────────────┤ │
│  │             │                                                                            │ │
│  │ Fortify     │ Severity: Based on CVSS of known CVE                                      │ │
│  │ (SCA)       │ Location: component_name + component_version + manifest_file               │ │
│  │             │ Evidence: dependency tree path, license info                                │ │
│  │             │ CVE:      Direct from SCA CVE database                                     │ │
│  │             │ Dedup:    SHA256(tenant + component + version + cve_id)                    │ │
│  │             │ EPSS:     Fetch EPSS score for each CVE (exploit prediction)               │ │
│  │             │                                                                            │ │
│  ├─────────────┼────────────────────────────────────────────────────────────────────────────┤ │
│  │             │                                                                            │ │
│  │ MobSF       │ Severity: MobSF severity direct mapping                                   │ │
│  │ (Mobile)    │ Location: file_path (decompiled) + activity/service name                   │ │
│  │             │ Evidence: code_snippet, manifest excerpt, screenshot (dynamic)             │ │
│  │             │ CWE:      MobSF category → CWE mapping                                    │ │
│  │             │ Dedup:    SHA256(tenant + category + file + owasp_mobile)                  │ │
│  │             │ OWASP:    Direct OWASP Mobile Top 10 (M1-M10) mapping                     │ │
│  │             │ MASVS:    Direct MASVS verification category mapping                      │ │
│  │             │                                                                            │ │
│  └─────────────┴────────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 11.3 Deduplication Algorithm

```go
// deduplicateFinding checks if a normalised finding already exists.
func deduplicateFinding(ctx context.Context, finding *NormalizedFinding) (*DeduplicationResult, error) {
    // ── Step 1: Generate fingerprint ──
    fingerprintInput := fmt.Sprintf("%s|%s|%s|%s",
        finding.TenantID,
        finding.Category,
        finding.LocationKey(), // scanner-specific location serialisation
        finding.CWEID,
    )
    fingerprint := sha256Hex(fingerprintInput)
    finding.Fingerprint = fingerprint

    // ── Step 2: Query existing findings with same fingerprint ──
    existing, err := findingsRepo.FindByFingerprint(ctx, finding.TenantID, fingerprint)
    if err != nil {
        return nil, err
    }

    if len(existing) == 0 {
        // ── No match: new primary finding ──
        finding.IsPrimary = true
        finding.Status = "new"
        finding.FirstSeenAt = time.Now()
        finding.LastSeenAt = time.Now()
        finding.OccurrenceCount = 1

        return &DeduplicationResult{
            Action:   "new",
            Finding:  finding,
        }, nil
    }

    // ── Step 3: Match found — determine relationship ──
    primary := findPrimary(existing)

    if primary.EngagementID == finding.EngagementID {
        // ── Same engagement: merge (cross-scanner correlation) ──
        // e.g., Burp found XSS + Fortify found XSS on same endpoint
        finding.IsPrimary = false
        finding.DuplicateClusterID = &primary.DuplicateClusterID
        finding.Status = "duplicate"

        // Update primary with highest severity
        if severityRank(finding.Severity) > severityRank(primary.Severity) {
            findingsRepo.UpdateSeverity(ctx, primary.ID, finding.Severity)
        }

        // Merge evidence arrays
        findingsRepo.AppendEvidence(ctx, primary.ID, finding.Evidence)

        // Increment occurrence count
        findingsRepo.IncrementOccurrence(ctx, primary.ID)

        return &DeduplicationResult{
            Action:       "merged",
            Finding:      finding,
            MergedIntoID: primary.ID,
        }, nil

    } else {
        // ── Different engagement: recurrence tracking ──
        finding.IsPrimary = true
        finding.Status = "new"
        finding.FirstSeenAt = primary.FirstSeenAt // track original discovery
        finding.LastSeenAt = time.Now()
        finding.OccurrenceCount = primary.OccurrenceCount + 1

        // Check if previously remediated → mark as "reopened"
        if primary.Status == "remediated" {
            finding.Status = "reopened"
        }

        return &DeduplicationResult{
            Action:            "recurrence",
            Finding:           finding,
            PreviousFindingID: primary.ID,
            PreviousEngagementID: primary.EngagementID,
            WasRemediated:     primary.Status == "remediated",
        }, nil
    }
}
```

### 11.4 AI Enrichment Pipeline (Async)

After normalisation, findings are enqueued for AI analysis:

```
finding.normalized event
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    AI ENRICHMENT PIPELINE                            │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Stage 1: Severity Validation (Claude API)                     │  │
│  │                                                                │  │
│  │  Prompt: "Given this vulnerability finding, assess the true    │  │
│  │  severity considering: target environment ({production}),      │  │
│  │  asset criticality ({critical}), exploit availability          │  │
│  │  ({exploit_available}), and the specific vulnerability         │  │
│  │  details. Return a severity score from 0.0 to 10.0."          │  │
│  │                                                                │  │
│  │  Output: ai_severity_score (0.0 – 10.0)                       │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Stage 2: Exploitability Assessment (Claude API)               │  │
│  │                                                                │  │
│  │  Input: finding details + asset context + network exposure     │  │
│  │  Output: ai_exploitability (0.0 – 10.0)                       │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Stage 3: False Positive Detection (ML model)                  │  │
│  │                                                                │  │
│  │  Input: finding + evidence + scanner confidence + history      │  │
│  │  Output: ai_false_positive_prob (0.0 – 1.0)                   │  │
│  │                                                                │  │
│  │  If prob > 0.8: auto-flag for analyst review                   │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Stage 4: Remediation Generation (Claude API)                  │  │
│  │                                                                │  │
│  │  Input: finding + tech_stack + code context (SAST)             │  │
│  │  Output: ai_remediation (contextual fix guidance)              │  │
│  │                                                                │  │
│  │  For SAST: include code-level fix with before/after example    │  │
│  │  For DAST: include configuration/code fix guidance             │  │
│  │  For Infra: include exact commands/config changes              │  │
│  │  For SCA: include upgrade path + breaking change analysis      │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  UPDATE findings SET                                                 │
│    ai_severity_score = ...,                                          │
│    ai_exploitability = ...,                                          │
│    ai_false_positive_prob = ...,                                     │
│    ai_remediation = ...,                                             │
│    ai_analysis_at = NOW()                                            │
│                                                                      │
│  Kafka: finding.ai_enriched { finding_id, tenant_id }                │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 12. Observability & Monitoring

### 12.1 Key Workflow Metrics

```
# Active scans by scanner type
scan_active_total{scanner="burp_suite", tenant_id="..."}

# Scan queue depth
scan_queue_depth{priority="1..10"}

# Scan workflow duration (histogram)
scan_workflow_duration_seconds{scanner="burp_suite", status="completed", bucket="..."}

# Activity duration by type
scan_activity_duration_seconds{activity="MonitorBurpProgress", scanner="burp_suite"}

# Retry count distribution
scan_retry_total{scanner="tenable_io", phase="dispatch", attempt="2"}

# Concurrency slot utilisation
scan_concurrency_utilization{gate="global|tenant|scanner", scanner="..."}

# Credential checkout duration
scan_credential_checkout_seconds{type="scanner|target"}

# Finding ingestion rate
findings_ingested_total{scanner="fortify_sast", severity="critical|high|medium|low|info"}

# AI enrichment latency
findings_ai_enrichment_seconds{stage="severity|exploitability|false_positive|remediation"}

# Scanner connector health
scanner_connector_health{connector="burp|tenable|fortify|mobsf", status="healthy|degraded|down"}
```

### 12.2 Alerting Rules

```yaml
# Prometheus alerting rules

groups:
  - name: scan-orchestration
    rules:
      - alert: ScanQueueBacklog
        expr: scan_queue_depth > 50
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Scan queue has {{ $value }} pending jobs"

      - alert: ScanFailureRateHigh
        expr: |
          rate(scan_workflow_duration_seconds_count{status="failed"}[15m])
          / rate(scan_workflow_duration_seconds_count[15m]) > 0.2
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Scan failure rate > 20% for {{ $labels.scanner }}"

      - alert: ScannerConnectorDown
        expr: scanner_connector_health{status="down"} == 1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Scanner connector {{ $labels.connector }} is down"

      - alert: CredentialCheckoutStuck
        expr: scan_credential_checkout_seconds > 120
        labels:
          severity: warning
        annotations:
          summary: "Credential checkout taking > 2 minutes"

      - alert: ConcurrencySlotExhausted
        expr: scan_concurrency_utilization{gate="scanner"} >= 1.0
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Scanner {{ $labels.scanner }} at full capacity for 30+ minutes"
```
