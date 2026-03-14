# MCP Orchestration Server — AI-Driven VAPT Platform

## Model Context Protocol Server for Vulnerability Scan Orchestration

---

## 1. MCP Server Architecture

```
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║                              MCP CLIENT LAYER                                          ║
║                                                                                        ║
║  ┌──────────────────────┐  ┌──────────────────────┐  ┌─────────────────────────────┐   ║
║  │  AI ANALYST AGENT    │  │  CLAUDE DESKTOP /    │  │  CI/CD PIPELINE AGENT       │   ║
║  │  (Autonomous Triage) │  │  ANALYST WORKBENCH   │  │  (Automated Scan Trigger)   │   ║
║  │                      │  │                      │  │                             │   ║
║  │  • Auto-launch scans │  │  • Human-in-loop     │  │  • PR-triggered SAST       │   ║
║  │  • Triage findings   │  │    scan management   │  │  • Scheduled infra scans   │   ║
║  │  • Generate reports  │  │  • Finding review     │  │  • Auto-report on complete │   ║
║  └──────────┬───────────┘  └──────────┬───────────┘  └──────────────┬──────────────┘   ║
║             │ MCP (JSON-RPC 2.0)      │ MCP (JSON-RPC 2.0)         │ MCP (JSON-RPC)   ║
╚═════════════╬═════════════════════════╬═════════════════════════════╬═══════════════════╝
              │                         │                             │
              ▼                         ▼                             ▼
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║                         MCP ORCHESTRATION SERVER                                       ║
║                         (Node.js / TypeScript — @modelcontextprotocol/sdk)             ║
║                                                                                        ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐   ║
║  │                          TRANSPORT LAYER                                        │   ║
║  │  ┌──────────────┐  ┌──────────────────┐  ┌────────────────────────────────┐     │   ║
║  │  │  SSE (HTTP)   │  │  Streamable HTTP │  │  stdio (local dev / testing)  │     │   ║
║  │  │  Port 3100    │  │  Port 3100       │  │  (pipe-based)                 │     │   ║
║  │  └──────────────┘  └──────────────────┘  └────────────────────────────────┘     │   ║
║  └─────────────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                        ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐   ║
║  │                    AUTHENTICATION & AUTHORIZATION                               │   ║
║  │  ┌────────────────┐  ┌───────────────┐  ┌────────────────┐  ┌──────────────┐   │   ║
║  │  │ JWT Validation │  │ RBAC Engine   │  │ Tenant Context │  │ Rate Limiter │   │   ║
║  │  │ (Keycloak OIDC)│  │ (per-tool)    │  │ (RLS binding)  │  │ (per-tenant) │   │   ║
║  │  └────────────────┘  └───────────────┘  └────────────────┘  └──────────────┘   │   ║
║  └─────────────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                        ║
║  ┌──────────────────────────────┐  ┌──────────────────────────────────────────────┐   ║
║  │        MCP TOOLS (9)         │  │            MCP RESOURCES (5)                 │   ║
║  │  ────────────────────────────│  │  ────────────────────────────────────────────│   ║
║  │  • start_burp_scan          │  │  • vapt://engagements/{id}/scope             │   ║
║  │  • start_tenable_scan       │  │  • vapt://engagements/{id}/targets           │   ║
║  │  • start_fortify_scan       │  │  • vapt://engagements/{id}/credentials       │   ║
║  │  • start_mobile_scan        │  │  • vapt://scans/{id}/status                  │   ║
║  │  • get_scan_status          │  │  • vapt://engagements/{id}/findings/summary  │   ║
║  │  • fetch_scan_results       │  │                                              │   ║
║  │  • assign_analyst           │  │  Supports:                                   │   ║
║  │  • generate_report          │  │  • resources/read                            │   ║
║  │  • publish_report           │  │  • resources/subscribe (SSE notifications)   │   ║
║  └──────────────────────────────┘  └──────────────────────────────────────────────┘   ║
║                                                                                        ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐   ║
║  │                     PLATFORM SERVICE ADAPTERS                                   │   ║
║  │  ┌─────────────┐ ┌──────────────┐ ┌───────────┐ ┌────────────┐ ┌────────────┐  │   ║
║  │  │ Engagement  │ │ Scan Orch.   │ │ Findings  │ │ Credential │ │ Reporting  │  │   ║
║  │  │ Service     │ │ Service      │ │ Service   │ │ Vault Svc  │ │ Service    │  │   ║
║  │  │ Adapter     │ │ Adapter      │ │ Adapter   │ │ Adapter    │ │ Adapter    │  │   ║
║  │  └──────┬──────┘ └──────┬───────┘ └─────┬─────┘ └─────┬──────┘ └─────┬──────┘  │   ║
║  └─────────┼───────────────┼───────────────┼─────────────┼──────────────┼──────────┘   ║
╚════════════╬═══════════════╬═══════════════╬═════════════╬══════════════╬══════════════╝
             │ REST/gRPC     │ REST/gRPC     │ REST        │ REST (mTLS)  │ REST
             ▼               ▼               ▼             ▼              ▼
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║                        PLATFORM MICROSERVICES (Kubernetes)                             ║
║                                                                                        ║
║  ┌─────────────┐ ┌──────────────┐ ┌───────────┐ ┌────────────┐ ┌────────────────────┐ ║
║  │ Engagement  │ │ Scan Orch.   │ │ Findings  │ │ Credential │ │ Reporting          │ ║
║  │ Service     │ │ Service      │ │ Service   │ │ Vault      │ │ Service            │ ║
║  │ (Go/Gin)    │ │ (Go/Temporal)│ │(Py/Fast)  │ │ (Go/Vault) │ │ (Py/FastAPI)       │ ║
║  └─────────────┘ └──────┬───────┘ └───────────┘ └────────────┘ └────────────────────┘ ║
║                          │ gRPC                                                        ║
║           ┌──────────────┼──────────────┬────────────────┐                             ║
║           ▼              ▼              ▼                ▼                              ║
║  ┌──────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐                      ║
║  │ Burp Suite   │ │ Tenable    │ │ Fortify    │ │ Mobile/MobSF │                      ║
║  │ Connector    │ │ Connector  │ │ Connector  │ │ Connector    │                      ║
║  └──────────────┘ └────────────┘ └────────────┘ └──────────────┘                      ║
║                                                                                        ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐   ║
║  │                    KAFKA EVENT BUS                                               │   ║
║  │  scan.requested │ scan.completed │ finding.normalized │ report.generated          │   ║
║  └─────────────────────────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════════════════════╝
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| MCP SDK | `@modelcontextprotocol/sdk` v1.x | Protocol implementation |
| Runtime | Node.js 22 LTS / TypeScript 5.5 | Server runtime |
| Transport | SSE + Streamable HTTP | Client communication |
| Auth | Keycloak OIDC + JWT | Identity & access |
| Service Mesh | Istio mTLS | Internal service calls |
| Caching | Redis 7 | Resource caching, rate limiting |
| Event Bus | Apache Kafka | Async event subscription |
| Observability | OpenTelemetry → Jaeger + Prometheus | Tracing & metrics |

---

## 2. Authentication Model

### 2.1 Authentication Flow

```
┌───────────┐     ┌──────────────┐     ┌───────────────┐     ┌─────────────────┐
│ MCP Client│────►│ Keycloak IdP │────►│ MCP Server    │────►│ Platform Service│
│           │     │              │     │ (JWT verify)  │     │ (mTLS + tenant) │
└───────────┘     └──────────────┘     └───────────────┘     └─────────────────┘
     │                   │                    │                       │
     │  1. OIDC Login    │                    │                       │
     │──────────────────►│                    │                       │
     │  2. JWT (access   │                    │                       │
     │     + id token)   │                    │                       │
     │◄──────────────────│                    │                       │
     │                                        │                       │
     │  3. MCP initialize (JWT in header)     │                       │
     │───────────────────────────────────────►│                       │
     │                                        │  4. Validate JWT      │
     │                                        │     (JWKS endpoint)   │
     │                                        │  5. Extract claims:   │
     │                                        │     sub, tenant_id,   │
     │                                        │     roles, permissions│
     │  6. MCP initialized (capabilities)     │                       │
     │◄───────────────────────────────────────│                       │
     │                                        │                       │
     │  7. tools/call (start_burp_scan)       │                       │
     │───────────────────────────────────────►│                       │
     │                                        │  8. Check RBAC        │
     │                                        │  9. Forward with      │
     │                                        │     tenant context    │
     │                                        │──────────────────────►│
     │                                        │  10. Result           │
     │                                        │◄──────────────────────│
     │  11. Tool result                       │                       │
     │◄───────────────────────────────────────│                       │
```

### 2.2 JWT Claims Structure

```json
{
  "iss": "https://auth.vapt-platform.io/realms/vapt",
  "sub": "user-uuid-here",
  "aud": "mcp-orchestration-server",
  "exp": 1711036800,
  "iat": 1711033200,
  "tenant_id": "customer-uuid-here",
  "email": "analyst@mssp.io",
  "name": "Jane Doe",
  "roles": ["lead_analyst"],
  "permissions": [
    "scan:create", "scan:read", "scan:cancel",
    "finding:read", "finding:update",
    "report:create", "report:approve",
    "engagement:read",
    "credential:read"
  ],
  "mfa_verified": true,
  "session_state": "session-uuid"
}
```

### 2.3 RBAC Permission Matrix

| Tool / Resource | platform_admin | lead_analyst | analyst | scanner_operator | customer_admin | customer_user | viewer |
|---|---|---|---|---|---|---|---|
| **start_burp_scan** | Yes | Yes | Yes | Yes | No | No | No |
| **start_tenable_scan** | Yes | Yes | Yes | Yes | No | No | No |
| **start_fortify_scan** | Yes | Yes | Yes | Yes | No | No | No |
| **start_mobile_scan** | Yes | Yes | Yes | Yes | No | No | No |
| **get_scan_status** | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **fetch_scan_results** | Yes | Yes | Yes | Yes | Yes | Yes | No |
| **assign_analyst** | Yes | Yes | No | No | No | No | No |
| **generate_report** | Yes | Yes | Yes | No | Yes | No | No |
| **publish_report** | Yes | Yes | No | No | No | No | No |
| **engagement_scope** | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **targets** | Yes | Yes | Yes | Yes | No | No | No |
| **credential_profiles** | Yes | Yes | Yes (meta) | Yes (meta) | No | No | No |
| **scan_status** | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **findings_summary** | Yes | Yes | Yes | Yes | Yes | Yes | Yes |

### 2.4 Rate Limits

| Role | Tool Calls / min | Resource Reads / min | Max Concurrent Scans |
|------|-----------------|---------------------|---------------------|
| platform_admin | 120 | 300 | Unlimited |
| lead_analyst | 60 | 200 | 20 |
| analyst | 30 | 100 | 10 |
| scanner_operator | 60 | 100 | 15 |
| customer_admin | 20 | 100 | Per subscription |
| customer_user | 10 | 50 | Per subscription |
| viewer | 5 | 30 | 0 |

### 2.5 Service-to-Service Authentication

```
MCP Server → Platform Services:
  • mTLS with X.509 certificates (Istio service mesh)
  • Service account JWT for Kubernetes pod identity
  • Tenant context propagated via X-Tenant-ID header
  • Correlation ID via X-Request-ID header for distributed tracing
```

---

## 3. MCP Tools — Complete Specifications

### 3.1 Tool: `start_burp_scan`

**Description:** Launch a Burp Suite Enterprise DAST scan against a web application or API target. Creates a scan job, checks out credentials from Vault, and dispatches to the Burp Suite connector via Temporal workflow.

**Required Permissions:** `scan:create`
**Allowed Roles:** `platform_admin`, `lead_analyst`, `analyst`, `scanner_operator`
**Rate Limit:** 5 scan launches / minute / tenant

#### Input Schema

```json
{
  "name": "start_burp_scan",
  "description": "Launch a Burp Suite Enterprise DAST scan against a web application or API endpoint. Supports authenticated scanning with credential profiles, custom scan configurations, and exclusion paths.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "engagement_id": {
        "type": "string",
        "format": "uuid",
        "description": "The engagement this scan belongs to. Must be in 'approved' or 'in_progress' status."
      },
      "target_id": {
        "type": "string",
        "format": "uuid",
        "description": "Target endpoint to scan (must be in-scope for the engagement)."
      },
      "scan_profile": {
        "type": "string",
        "enum": ["crawl_and_audit_full", "crawl_and_audit_lightweight", "audit_only", "crawl_only", "api_scan"],
        "default": "crawl_and_audit_full",
        "description": "Burp scan configuration profile."
      },
      "credential_profile_id": {
        "type": "string",
        "format": "uuid",
        "description": "Optional credential profile for authenticated scanning."
      },
      "excluded_paths": {
        "type": "array",
        "items": { "type": "string" },
        "default": [],
        "description": "URL paths to exclude from scanning (e.g., ['/logout', '/admin/delete'])."
      },
      "max_duration_minutes": {
        "type": "integer",
        "minimum": 15,
        "maximum": 480,
        "default": 240,
        "description": "Maximum scan duration in minutes before forced termination."
      },
      "priority": {
        "type": "integer",
        "minimum": 1,
        "maximum": 10,
        "default": 5,
        "description": "Queue priority (1 = highest, 10 = lowest)."
      },
      "custom_config": {
        "type": "object",
        "description": "Advanced Burp-specific configuration overrides.",
        "properties": {
          "custom_headers": {
            "type": "object",
            "additionalProperties": { "type": "string" },
            "description": "Custom HTTP headers to include in all requests."
          },
          "rate_limit_rps": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "description": "Maximum requests per second to the target."
          },
          "scope_includes": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Regex patterns for URLs to include in scope."
          },
          "scope_excludes": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Regex patterns for URLs to exclude from scope."
          }
        }
      }
    },
    "required": ["engagement_id", "target_id"]
  }
}
```

#### Handler Logic

```python
async def handle_start_burp_scan(params, context):
    """
    Handler: start_burp_scan
    Flow: Validate → Create Job → Dispatch Temporal Workflow → Return Job ID
    """
    tenant_id = context.auth.tenant_id
    user_id   = context.auth.sub

    # ── Step 1: Validate engagement exists and is in scannable state ──
    engagement = await engagement_service.get(
        tenant_id=tenant_id,
        engagement_id=params["engagement_id"]
    )
    if engagement.status not in ("approved", "in_progress"):
        raise McpError(
            INVALID_PARAMS,
            f"Engagement {engagement.reference_code} is '{engagement.status}'; "
            f"must be 'approved' or 'in_progress' to launch scans."
        )

    # ── Step 2: Validate target is in-scope for this engagement ──
    target = await asset_service.get_target(
        tenant_id=tenant_id,
        target_id=params["target_id"]
    )
    scope_check = await engagement_service.check_scope(
        engagement_id=params["engagement_id"],
        asset_id=target.asset_id,
        scan_type="dast"
    )
    if not scope_check.in_scope:
        raise McpError(
            INVALID_PARAMS,
            f"Target '{target.host}:{target.port}' is not in-scope for "
            f"engagement {engagement.reference_code} with scan type 'dast'."
        )

    # ── Step 3: Check tenant concurrent scan limits ──
    active_scans = await scan_service.count_active(tenant_id=tenant_id)
    customer = await customer_service.get(tenant_id=tenant_id)
    if active_scans >= customer.max_concurrent_scans:
        raise McpError(
            RESOURCE_EXHAUSTED,
            f"Concurrent scan limit reached ({customer.max_concurrent_scans}). "
            f"Wait for a running scan to complete or upgrade your plan."
        )

    # ── Step 4: Validate credential profile if provided ──
    credential_profile_id = params.get("credential_profile_id")
    if credential_profile_id:
        cred = await credential_vault.get_metadata(
            tenant_id=tenant_id,
            credential_id=credential_profile_id
        )
        if cred.status != "active":
            raise McpError(INVALID_PARAMS, "Credential profile is not active.")

    # ── Step 5: Create scan job record ──
    scan_job = await scan_service.create_job(
        tenant_id=tenant_id,
        engagement_id=params["engagement_id"],
        asset_id=target.asset_id,
        target_id=params["target_id"],
        scan_type="dast",
        scanner_engine="burp_suite",
        priority=params.get("priority", 5),
        credential_profile_id=credential_profile_id,
        initiated_by=user_id,
        scan_config={
            "profile": params.get("scan_profile", "crawl_and_audit_full"),
            "excluded_paths": params.get("excluded_paths", []),
            "max_duration_minutes": params.get("max_duration_minutes", 240),
            **params.get("custom_config", {})
        }
    )

    # ── Step 6: Publish Kafka event ──
    await kafka.publish("scan.requested", {
        "scan_job_id": scan_job.id,
        "tenant_id": tenant_id,
        "engagement_id": params["engagement_id"],
        "scan_type": "dast",
        "scanner_engine": "burp_suite",
        "target_url": target.url,
        "priority": scan_job.priority
    })

    # ── Step 7: Start Temporal workflow ──
    workflow_id = f"scan-burp-{scan_job.id}"
    await temporal.start_workflow(
        workflow="ScanWorkflow",
        workflow_id=workflow_id,
        args={
            "scan_job_id": scan_job.id,
            "scanner": "burp_suite",
            "target": target.to_dict(),
            "config": scan_job.scan_config,
            "credential_profile_id": credential_profile_id
        },
        task_queue="scan-orchestration"
    )

    # ── Step 8: Update scan job with workflow reference ──
    await scan_service.update_job(
        scan_job_id=scan_job.id,
        temporal_workflow_id=workflow_id,
        status="dispatched"
    )

    # ── Step 9: Emit resource change notification ──
    await mcp_server.notify_resource_changed(
        f"vapt://engagements/{params['engagement_id']}/scans"
    )

    # ── Return ──
    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "scan_job_id": str(scan_job.id),
                "status": "dispatched",
                "scanner": "burp_suite",
                "scan_type": "dast",
                "target": target.url,
                "engagement": engagement.reference_code,
                "priority": scan_job.priority,
                "estimated_duration_minutes": params.get("max_duration_minutes", 240),
                "temporal_workflow_id": workflow_id,
                "message": f"Burp Suite DAST scan dispatched against {target.url}. "
                           f"Track progress with get_scan_status or subscribe to "
                           f"vapt://scans/{scan_job.id}/status"
            }, indent=2)
        }]
    }
```

---

### 3.2 Tool: `start_tenable_scan`

**Description:** Launch a Tenable.io / Nessus infrastructure vulnerability scan against network hosts, IP ranges, or CIDRs. Supports credentialed scanning with SSH/WinRM/SNMP credentials.

**Required Permissions:** `scan:create`
**Allowed Roles:** `platform_admin`, `lead_analyst`, `analyst`, `scanner_operator`
**Rate Limit:** 5 scan launches / minute / tenant

#### Input Schema

```json
{
  "name": "start_tenable_scan",
  "description": "Launch a Tenable.io infrastructure vulnerability scan against hosts, IP ranges, or CIDRs. Supports credentialed scanning with SSH, WinRM, and SNMP protocols.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "engagement_id": {
        "type": "string",
        "format": "uuid",
        "description": "The engagement this scan belongs to."
      },
      "target_ids": {
        "type": "array",
        "items": { "type": "string", "format": "uuid" },
        "minItems": 1,
        "maxItems": 50,
        "description": "Target endpoints to scan (IPs, CIDRs, hostnames)."
      },
      "scan_template": {
        "type": "string",
        "enum": ["basic_network", "advanced", "pci_dss", "scap_compliance", "web_app_tests", "malware_scan"],
        "default": "advanced",
        "description": "Tenable scan template."
      },
      "credential_profile_ids": {
        "type": "array",
        "items": { "type": "string", "format": "uuid" },
        "description": "Credential profiles for authenticated scanning (SSH, WinRM, SNMP)."
      },
      "port_range": {
        "type": "string",
        "default": "default",
        "description": "Port specification (e.g., '1-1024', '1-65535', 'default')."
      },
      "max_duration_minutes": {
        "type": "integer",
        "minimum": 30,
        "maximum": 720,
        "default": 480,
        "description": "Maximum scan duration before forced termination."
      },
      "priority": {
        "type": "integer",
        "minimum": 1,
        "maximum": 10,
        "default": 5
      },
      "scan_window": {
        "type": "object",
        "description": "Restrict scan execution to a maintenance window.",
        "properties": {
          "start_time": { "type": "string", "format": "time", "description": "UTC start time (HH:MM)." },
          "end_time": { "type": "string", "format": "time", "description": "UTC end time (HH:MM)." }
        }
      }
    },
    "required": ["engagement_id", "target_ids"]
  }
}
```

#### Handler Logic

```python
async def handle_start_tenable_scan(params, context):
    tenant_id = context.auth.tenant_id
    user_id   = context.auth.sub

    engagement = await engagement_service.get(
        tenant_id=tenant_id,
        engagement_id=params["engagement_id"]
    )
    if engagement.status not in ("approved", "in_progress"):
        raise McpError(INVALID_PARAMS, f"Engagement not in scannable state.")

    # Resolve and validate all targets
    targets = []
    for target_id in params["target_ids"]:
        target = await asset_service.get_target(tenant_id=tenant_id, target_id=target_id)
        scope_check = await engagement_service.check_scope(
            engagement_id=params["engagement_id"],
            asset_id=target.asset_id,
            scan_type="infrastructure"
        )
        if not scope_check.in_scope:
            raise McpError(INVALID_PARAMS, f"Target '{target.host}' is not in-scope.")
        targets.append(target)

    # Check concurrent scan limits
    active_scans = await scan_service.count_active(tenant_id=tenant_id)
    customer = await customer_service.get(tenant_id=tenant_id)
    if active_scans >= customer.max_concurrent_scans:
        raise McpError(RESOURCE_EXHAUSTED, "Concurrent scan limit reached.")

    # Create scan job (one job covers all targets for Tenable)
    scan_job = await scan_service.create_job(
        tenant_id=tenant_id,
        engagement_id=params["engagement_id"],
        asset_id=targets[0].asset_id,  # primary asset
        target_id=targets[0].id,
        scan_type="infrastructure",
        scanner_engine="tenable_io",
        priority=params.get("priority", 5),
        credential_profile_id=(params.get("credential_profile_ids") or [None])[0],
        initiated_by=user_id,
        scan_config={
            "template": params.get("scan_template", "advanced"),
            "target_hosts": [t.host for t in targets],
            "port_range": params.get("port_range", "default"),
            "max_duration_minutes": params.get("max_duration_minutes", 480),
            "scan_window": params.get("scan_window"),
            "credential_profile_ids": params.get("credential_profile_ids", [])
        }
    )

    await kafka.publish("scan.requested", {
        "scan_job_id": scan_job.id,
        "tenant_id": tenant_id,
        "scan_type": "infrastructure",
        "scanner_engine": "tenable_io",
        "target_count": len(targets)
    })

    workflow_id = f"scan-tenable-{scan_job.id}"
    await temporal.start_workflow(
        workflow="ScanWorkflow",
        workflow_id=workflow_id,
        args={
            "scan_job_id": scan_job.id,
            "scanner": "tenable_io",
            "targets": [t.to_dict() for t in targets],
            "config": scan_job.scan_config,
            "credential_profile_ids": params.get("credential_profile_ids", [])
        },
        task_queue="scan-orchestration"
    )

    await scan_service.update_job(scan_job.id, temporal_workflow_id=workflow_id, status="dispatched")
    await mcp_server.notify_resource_changed(f"vapt://engagements/{params['engagement_id']}/scans")

    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "scan_job_id": str(scan_job.id),
                "status": "dispatched",
                "scanner": "tenable_io",
                "scan_type": "infrastructure",
                "targets": [t.host for t in targets],
                "target_count": len(targets),
                "template": params.get("scan_template", "advanced"),
                "engagement": engagement.reference_code,
                "temporal_workflow_id": workflow_id,
                "message": f"Tenable infrastructure scan dispatched against "
                           f"{len(targets)} targets."
            }, indent=2)
        }]
    }
```

---

### 3.3 Tool: `start_fortify_scan`

**Description:** Launch a Fortify SAST (Static Application Security Testing) or SCA (Software Composition Analysis) scan against a source code repository. Dispatches to Fortify ScanCentral for analysis.

**Required Permissions:** `scan:create`
**Allowed Roles:** `platform_admin`, `lead_analyst`, `analyst`, `scanner_operator`
**Rate Limit:** 3 scan launches / minute / tenant

#### Input Schema

```json
{
  "name": "start_fortify_scan",
  "description": "Launch a Fortify SAST or SCA scan against a source code repository. Supports specifying branch, languages, and scan depth.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "engagement_id": {
        "type": "string",
        "format": "uuid",
        "description": "The engagement this scan belongs to."
      },
      "asset_id": {
        "type": "string",
        "format": "uuid",
        "description": "Asset representing the application source code."
      },
      "scan_subtype": {
        "type": "string",
        "enum": ["sast", "sca", "sast_and_sca"],
        "default": "sast_and_sca",
        "description": "Type of code analysis to perform."
      },
      "repo_url": {
        "type": "string",
        "format": "uri",
        "description": "Git repository URL to clone and scan."
      },
      "branch": {
        "type": "string",
        "default": "main",
        "description": "Git branch to scan."
      },
      "commit_sha": {
        "type": "string",
        "description": "Specific commit SHA to scan (optional, defaults to HEAD of branch)."
      },
      "languages": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["java", "csharp", "python", "javascript", "typescript", "go", "c_cpp", "ruby", "php", "swift", "kotlin"]
        },
        "description": "Programming languages present in the codebase."
      },
      "credential_profile_id": {
        "type": "string",
        "format": "uuid",
        "description": "Credential profile for repository access (SSH key or token)."
      },
      "max_duration_minutes": {
        "type": "integer",
        "minimum": 30,
        "maximum": 720,
        "default": 360
      },
      "priority": {
        "type": "integer",
        "minimum": 1,
        "maximum": 10,
        "default": 5
      },
      "exclude_patterns": {
        "type": "array",
        "items": { "type": "string" },
        "description": "File patterns to exclude (e.g., ['**/test/**', '**/vendor/**'])."
      }
    },
    "required": ["engagement_id", "asset_id", "repo_url"]
  }
}
```

#### Handler Logic

```python
async def handle_start_fortify_scan(params, context):
    tenant_id = context.auth.tenant_id
    user_id   = context.auth.sub

    engagement = await engagement_service.get(tenant_id=tenant_id, engagement_id=params["engagement_id"])
    if engagement.status not in ("approved", "in_progress"):
        raise McpError(INVALID_PARAMS, "Engagement not in scannable state.")

    asset = await asset_service.get(tenant_id=tenant_id, asset_id=params["asset_id"])
    scope_check = await engagement_service.check_scope(
        engagement_id=params["engagement_id"],
        asset_id=params["asset_id"],
        scan_type="sast"
    )
    if not scope_check.in_scope:
        raise McpError(INVALID_PARAMS, f"Asset '{asset.name}' not in-scope for SAST scanning.")

    scan_subtype = params.get("scan_subtype", "sast_and_sca")
    scan_types = {
        "sast": ["sast"],
        "sca": ["sca"],
        "sast_and_sca": ["sast", "sca"]
    }[scan_subtype]

    scan_jobs = []
    for st in scan_types:
        scan_job = await scan_service.create_job(
            tenant_id=tenant_id,
            engagement_id=params["engagement_id"],
            asset_id=params["asset_id"],
            scan_type=st,
            scanner_engine="fortify_sast" if st == "sast" else "fortify_sca",
            priority=params.get("priority", 5),
            credential_profile_id=params.get("credential_profile_id"),
            initiated_by=user_id,
            scan_config={
                "repo_url": params["repo_url"],
                "branch": params.get("branch", "main"),
                "commit_sha": params.get("commit_sha"),
                "languages": params.get("languages", []),
                "exclude_patterns": params.get("exclude_patterns", []),
                "max_duration_minutes": params.get("max_duration_minutes", 360)
            }
        )

        workflow_id = f"scan-fortify-{st}-{scan_job.id}"
        await temporal.start_workflow(
            workflow="ScanWorkflow",
            workflow_id=workflow_id,
            args={
                "scan_job_id": scan_job.id,
                "scanner": f"fortify_{st}",
                "config": scan_job.scan_config,
                "credential_profile_id": params.get("credential_profile_id")
            },
            task_queue="scan-orchestration"
        )
        await scan_service.update_job(scan_job.id, temporal_workflow_id=workflow_id, status="dispatched")
        scan_jobs.append({"scan_job_id": str(scan_job.id), "scan_type": st, "workflow_id": workflow_id})

    await kafka.publish("scan.requested", {
        "scan_job_ids": [sj["scan_job_id"] for sj in scan_jobs],
        "tenant_id": tenant_id,
        "scan_types": scan_types,
        "scanner_engine": "fortify"
    })

    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "scan_jobs": scan_jobs,
                "status": "dispatched",
                "scanner": "fortify",
                "repo": params["repo_url"],
                "branch": params.get("branch", "main"),
                "engagement": engagement.reference_code,
                "message": f"Fortify {scan_subtype.upper()} scan dispatched for "
                           f"{params['repo_url']} ({params.get('branch', 'main')})."
            }, indent=2)
        }]
    }
```

---

### 3.4 Tool: `start_mobile_scan`

**Description:** Launch a mobile application security scan using MobSF. Supports both static analysis (decompilation, manifest review) and dynamic analysis (runtime instrumentation) for Android APK and iOS IPA binaries.

**Required Permissions:** `scan:create`
**Allowed Roles:** `platform_admin`, `lead_analyst`, `analyst`, `scanner_operator`
**Rate Limit:** 3 scan launches / minute / tenant

#### Input Schema

```json
{
  "name": "start_mobile_scan",
  "description": "Launch a mobile security scan (static and/or dynamic) against an Android APK or iOS IPA binary using MobSF.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "engagement_id": {
        "type": "string",
        "format": "uuid",
        "description": "The engagement this scan belongs to."
      },
      "asset_id": {
        "type": "string",
        "format": "uuid",
        "description": "Asset representing the mobile application."
      },
      "platform": {
        "type": "string",
        "enum": ["android", "ios"],
        "description": "Mobile platform."
      },
      "binary_reference": {
        "type": "string",
        "description": "MinIO object key or upload reference for the APK/IPA binary."
      },
      "analysis_type": {
        "type": "string",
        "enum": ["static", "dynamic", "static_and_dynamic"],
        "default": "static_and_dynamic",
        "description": "Type of mobile analysis to perform."
      },
      "credential_profile_id": {
        "type": "string",
        "format": "uuid",
        "description": "Credential profile for app login (dynamic analysis only)."
      },
      "max_duration_minutes": {
        "type": "integer",
        "minimum": 15,
        "maximum": 360,
        "default": 120
      },
      "priority": {
        "type": "integer",
        "minimum": 1,
        "maximum": 10,
        "default": 5
      }
    },
    "required": ["engagement_id", "asset_id", "platform", "binary_reference"]
  }
}
```

#### Handler Logic

```python
async def handle_start_mobile_scan(params, context):
    tenant_id = context.auth.tenant_id
    user_id   = context.auth.sub

    engagement = await engagement_service.get(tenant_id=tenant_id, engagement_id=params["engagement_id"])
    if engagement.status not in ("approved", "in_progress"):
        raise McpError(INVALID_PARAMS, "Engagement not in scannable state.")

    asset = await asset_service.get(tenant_id=tenant_id, asset_id=params["asset_id"])
    expected_type = f"mobile_app_{params['platform']}"
    if asset.asset_type != expected_type:
        raise McpError(INVALID_PARAMS, f"Asset type mismatch: expected '{expected_type}', got '{asset.asset_type}'.")

    # Verify binary exists in MinIO
    binary_exists = await object_storage.exists(
        bucket=f"tenant-{tenant_id}-mobile-binaries",
        key=params["binary_reference"]
    )
    if not binary_exists:
        raise McpError(INVALID_PARAMS, "Binary not found. Upload the APK/IPA first.")

    analysis_types = {
        "static": ["mobile_static"],
        "dynamic": ["mobile_dynamic"],
        "static_and_dynamic": ["mobile_static", "mobile_dynamic"]
    }[params.get("analysis_type", "static_and_dynamic")]

    scan_jobs = []
    for scan_type in analysis_types:
        scan_job = await scan_service.create_job(
            tenant_id=tenant_id,
            engagement_id=params["engagement_id"],
            asset_id=params["asset_id"],
            scan_type=scan_type,
            scanner_engine="mobsf",
            priority=params.get("priority", 5),
            credential_profile_id=params.get("credential_profile_id") if scan_type == "mobile_dynamic" else None,
            initiated_by=user_id,
            scan_config={
                "platform": params["platform"],
                "binary_reference": params["binary_reference"],
                "analysis_type": scan_type.replace("mobile_", ""),
                "max_duration_minutes": params.get("max_duration_minutes", 120)
            }
        )

        workflow_id = f"scan-mobile-{scan_type.split('_')[1]}-{scan_job.id}"
        await temporal.start_workflow(
            workflow="ScanWorkflow",
            workflow_id=workflow_id,
            args={
                "scan_job_id": scan_job.id,
                "scanner": "mobsf",
                "config": scan_job.scan_config,
                "credential_profile_id": params.get("credential_profile_id")
            },
            task_queue="scan-orchestration-mobile"
        )
        await scan_service.update_job(scan_job.id, temporal_workflow_id=workflow_id, status="dispatched")
        scan_jobs.append({"scan_job_id": str(scan_job.id), "scan_type": scan_type, "workflow_id": workflow_id})

    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "scan_jobs": scan_jobs,
                "status": "dispatched",
                "scanner": "mobsf",
                "platform": params["platform"],
                "analysis_type": params.get("analysis_type", "static_and_dynamic"),
                "engagement": engagement.reference_code,
                "message": f"MobSF {params['platform']} scan dispatched "
                           f"({params.get('analysis_type', 'static_and_dynamic')})."
            }, indent=2)
        }]
    }
```

---

### 3.5 Tool: `get_scan_status`

**Description:** Retrieve the current status and progress of one or more scan jobs. Returns lifecycle state, progress percentage, timing data, and summary counts if the scan is complete.

**Required Permissions:** `scan:read`
**Allowed Roles:** All roles
**Rate Limit:** 30 reads / minute / tenant

#### Input Schema

```json
{
  "name": "get_scan_status",
  "description": "Get the current status and progress of scan job(s). Supports querying a single scan or all scans for an engagement.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "scan_job_id": {
        "type": "string",
        "format": "uuid",
        "description": "Specific scan job ID to query."
      },
      "engagement_id": {
        "type": "string",
        "format": "uuid",
        "description": "Get status of all scans for an engagement."
      },
      "include_logs": {
        "type": "boolean",
        "default": false,
        "description": "Include recent execution logs (last 20 entries)."
      }
    },
    "oneOf": [
      { "required": ["scan_job_id"] },
      { "required": ["engagement_id"] }
    ]
  }
}
```

#### Handler Logic

```python
async def handle_get_scan_status(params, context):
    tenant_id = context.auth.tenant_id

    if "scan_job_id" in params:
        scan = await scan_service.get_job(
            tenant_id=tenant_id,
            scan_job_id=params["scan_job_id"]
        )
        if not scan:
            raise McpError(INVALID_PARAMS, "Scan job not found.")

        result = {
            "scan_job_id": str(scan.id),
            "status": scan.status,
            "scan_type": scan.scan_type,
            "scanner_engine": scan.scanner_engine,
            "progress_percent": scan.progress_percent,
            "priority": scan.priority,
            "queued_at": scan.queued_at.isoformat(),
            "started_at": scan.started_at.isoformat() if scan.started_at else None,
            "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
            "duration_seconds": scan.duration_seconds,
            "attempt_number": scan.attempt_number,
            "max_attempts": scan.max_attempts,
            "last_error": scan.last_error
        }

        if scan.status == "completed":
            result["finding_summary"] = {
                "critical": scan.findings_critical,
                "high": scan.findings_high,
                "medium": scan.findings_medium,
                "low": scan.findings_low,
                "info": scan.findings_info,
                "total": scan.total_findings
            }

        if params.get("include_logs"):
            logs = await scan_service.get_logs(scan_job_id=scan.id, limit=20)
            result["recent_logs"] = [
                {"level": l.level, "message": l.message, "timestamp": l.created_at.isoformat()}
                for l in logs
            ]

        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

    elif "engagement_id" in params:
        scans = await scan_service.list_by_engagement(
            tenant_id=tenant_id,
            engagement_id=params["engagement_id"]
        )
        summary = {
            "engagement_id": params["engagement_id"],
            "total_scans": len(scans),
            "by_status": {},
            "scans": []
        }
        for scan in scans:
            status = scan.status
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            summary["scans"].append({
                "scan_job_id": str(scan.id),
                "scan_type": scan.scan_type,
                "scanner_engine": scan.scanner_engine,
                "status": scan.status,
                "progress_percent": scan.progress_percent,
                "total_findings": scan.total_findings
            })

        overall_progress = (
            sum(s.progress_percent for s in scans) / len(scans)
            if scans else 0
        )
        summary["overall_progress_percent"] = round(overall_progress, 1)

        return {"content": [{"type": "text", "text": json.dumps(summary, indent=2)}]}
```

---

### 3.6 Tool: `fetch_scan_results`

**Description:** Retrieve normalised findings from a completed scan job. Returns deduplicated, AI-enriched vulnerability findings with evidence, remediation guidance, and compliance mappings.

**Required Permissions:** `finding:read`
**Allowed Roles:** `platform_admin`, `lead_analyst`, `analyst`, `scanner_operator`, `customer_admin`, `customer_user`
**Rate Limit:** 20 reads / minute / tenant

#### Input Schema

```json
{
  "name": "fetch_scan_results",
  "description": "Retrieve normalised vulnerability findings from a completed scan. Supports filtering by severity, status, and category.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "scan_job_id": {
        "type": "string",
        "format": "uuid",
        "description": "The completed scan job to fetch results from."
      },
      "severity_filter": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["critical", "high", "medium", "low", "informational"]
        },
        "description": "Filter findings by severity. If omitted, returns all."
      },
      "status_filter": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["new", "confirmed", "false_positive", "accepted_risk", "remediated", "reopened", "duplicate"]
        },
        "description": "Filter findings by status."
      },
      "include_evidence": {
        "type": "boolean",
        "default": false,
        "description": "Include full evidence payloads (HTTP requests/responses, screenshots)."
      },
      "include_ai_analysis": {
        "type": "boolean",
        "default": true,
        "description": "Include AI-generated severity validation and remediation."
      },
      "page": {
        "type": "integer",
        "minimum": 1,
        "default": 1
      },
      "page_size": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "default": 25
      }
    },
    "required": ["scan_job_id"]
  }
}
```

#### Handler Logic

```python
async def handle_fetch_scan_results(params, context):
    tenant_id = context.auth.tenant_id

    scan = await scan_service.get_job(tenant_id=tenant_id, scan_job_id=params["scan_job_id"])
    if not scan:
        raise McpError(INVALID_PARAMS, "Scan job not found.")
    if scan.status != "completed":
        raise McpError(
            INVALID_PARAMS,
            f"Scan is '{scan.status}'. Results available only after completion."
        )

    filters = {
        "scan_job_id": params["scan_job_id"],
        "tenant_id": tenant_id,
        "is_primary": True  # only primary findings (not duplicates)
    }
    if params.get("severity_filter"):
        filters["severity__in"] = params["severity_filter"]
    if params.get("status_filter"):
        filters["status__in"] = params["status_filter"]

    page = params.get("page", 1)
    page_size = params.get("page_size", 25)

    findings_page = await findings_service.list(
        filters=filters,
        page=page,
        page_size=page_size,
        order_by=["-severity_rank", "-cvss_score"]
    )

    results = {
        "scan_job_id": str(scan.id),
        "scanner": scan.scanner_engine,
        "scan_type": scan.scan_type,
        "total_findings": findings_page.total,
        "page": page,
        "page_size": page_size,
        "total_pages": findings_page.total_pages,
        "summary": {
            "critical": scan.findings_critical,
            "high": scan.findings_high,
            "medium": scan.findings_medium,
            "low": scan.findings_low,
            "info": scan.findings_info
        },
        "findings": []
    }

    for f in findings_page.items:
        finding = {
            "finding_id": str(f.id),
            "title": f.title,
            "category": f.category,
            "severity": f.severity,
            "confidence": f.confidence,
            "status": f.status,
            "cvss_score": float(f.cvss_score) if f.cvss_score else None,
            "cvss_vector": f.cvss_vector,
            "cwe_id": f.cwe_id,
            "cve_ids": f.cve_ids,
            "owasp_category": f.owasp_category,
            "affected_url": f.affected_url,
            "affected_host": f.affected_host,
            "affected_port": f.affected_port,
            "affected_component": f.affected_component,
            "remediation": f.remediation,
            "remediation_effort": f.remediation_effort
        }

        if params.get("include_evidence"):
            finding["evidence"] = f.evidence

        if params.get("include_ai_analysis") and f.ai_analysis_at:
            finding["ai_analysis"] = {
                "severity_score": float(f.ai_severity_score) if f.ai_severity_score else None,
                "exploitability_score": float(f.ai_exploitability) if f.ai_exploitability else None,
                "false_positive_probability": float(f.ai_false_positive_prob) if f.ai_false_positive_prob else None,
                "ai_remediation": f.ai_remediation,
                "analyzed_at": f.ai_analysis_at.isoformat()
            }

        results["findings"].append(finding)

    return {"content": [{"type": "text", "text": json.dumps(results, indent=2)}]}
```

---

### 3.7 Tool: `assign_analyst`

**Description:** Assign a security analyst to an engagement or specific finding for triage and validation. Creates work items and triggers SLA tracking.

**Required Permissions:** `engagement:assign` or `finding:assign`
**Allowed Roles:** `platform_admin`, `lead_analyst`
**Rate Limit:** 30 calls / minute / tenant

#### Input Schema

```json
{
  "name": "assign_analyst",
  "description": "Assign a security analyst to an engagement (as lead) or to specific findings for triage and validation.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "analyst_id": {
        "type": "string",
        "format": "uuid",
        "description": "User ID of the analyst to assign."
      },
      "engagement_id": {
        "type": "string",
        "format": "uuid",
        "description": "Assign analyst as engagement lead."
      },
      "finding_ids": {
        "type": "array",
        "items": { "type": "string", "format": "uuid" },
        "minItems": 1,
        "maxItems": 100,
        "description": "Assign analyst to specific findings for triage."
      },
      "assignment_type": {
        "type": "string",
        "enum": ["engagement_lead", "finding_triage", "finding_validation", "finding_retest"],
        "description": "Type of assignment."
      },
      "notes": {
        "type": "string",
        "maxLength": 1000,
        "description": "Optional notes for the analyst."
      },
      "priority_override": {
        "type": "string",
        "enum": ["critical", "high", "medium", "low"],
        "description": "Override priority for SLA calculation."
      }
    },
    "required": ["analyst_id"],
    "anyOf": [
      { "required": ["engagement_id"] },
      { "required": ["finding_ids"] }
    ]
  }
}
```

#### Handler Logic

```python
async def handle_assign_analyst(params, context):
    tenant_id = context.auth.tenant_id
    assigner_id = context.auth.sub

    # Validate analyst exists and has analyst role
    analyst = await user_service.get(tenant_id=tenant_id, user_id=params["analyst_id"])
    if not analyst:
        raise McpError(INVALID_PARAMS, "Analyst user not found.")
    if analyst.role not in ("analyst", "lead_analyst", "platform_admin"):
        raise McpError(INVALID_PARAMS, f"User '{analyst.display_name}' does not have an analyst role.")
    if not analyst.is_active:
        raise McpError(INVALID_PARAMS, f"User '{analyst.display_name}' is inactive.")

    results = {"analyst": analyst.display_name, "assignments": []}

    # ── Engagement lead assignment ──
    if "engagement_id" in params:
        engagement = await engagement_service.get(
            tenant_id=tenant_id,
            engagement_id=params["engagement_id"]
        )
        await engagement_service.update(
            engagement_id=engagement.id,
            assigned_lead=params["analyst_id"]
        )
        results["assignments"].append({
            "type": "engagement_lead",
            "engagement": engagement.reference_code,
            "status": "assigned"
        })

        await kafka.publish("notification.dispatch", {
            "type": "assignment",
            "recipient_id": params["analyst_id"],
            "title": f"Assigned as lead analyst for {engagement.reference_code}",
            "body": params.get("notes", f"You have been assigned as lead analyst."),
            "link": f"/engagements/{engagement.id}"
        })

    # ── Finding-level assignment ──
    if "finding_ids" in params:
        assignment_type = params.get("assignment_type", "finding_triage")
        work_items_created = 0

        for finding_id in params["finding_ids"]:
            finding = await findings_service.get(tenant_id=tenant_id, finding_id=finding_id)
            if not finding:
                continue

            await findings_service.update(finding_id=finding_id, assigned_to=params["analyst_id"])

            sla_policy = await analyst_workflow.get_sla_policy(
                tenant_id=tenant_id,
                severity=params.get("priority_override") or finding.severity
            )

            await analyst_workflow.create_work_item(
                tenant_id=tenant_id,
                finding_id=finding_id,
                engagement_id=finding.engagement_id,
                item_type=assignment_type.replace("finding_", ""),
                assigned_to=params["analyst_id"],
                priority=sla_policy.calculated_priority,
                sla_deadline=sla_policy.deadline
            )
            work_items_created += 1

        results["assignments"].append({
            "type": assignment_type,
            "findings_assigned": work_items_created,
            "status": "assigned"
        })

        await kafka.publish("notification.dispatch", {
            "type": "assignment",
            "recipient_id": params["analyst_id"],
            "title": f"{work_items_created} findings assigned for {assignment_type}",
            "body": params.get("notes", ""),
            "finding_count": work_items_created
        })

    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                **results,
                "message": f"Successfully assigned {analyst.display_name}."
            }, indent=2)
        }]
    }
```

---

### 3.8 Tool: `generate_report`

**Description:** Trigger generation of a VAPT report for an engagement. Supports multiple report types (executive summary, full technical, compliance, delta/retest) and output formats (PDF, DOCX, HTML, JSON).

**Required Permissions:** `report:create`
**Allowed Roles:** `platform_admin`, `lead_analyst`, `analyst`, `customer_admin`
**Rate Limit:** 5 reports / minute / tenant

#### Input Schema

```json
{
  "name": "generate_report",
  "description": "Generate a VAPT report for an engagement. Supports executive summary, full technical, compliance, and delta report types in PDF, DOCX, HTML, or JSON format.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "engagement_id": {
        "type": "string",
        "format": "uuid",
        "description": "The engagement to generate the report for."
      },
      "report_type": {
        "type": "string",
        "enum": ["executive_summary", "full_technical", "compliance", "delta_retest", "custom"],
        "default": "full_technical",
        "description": "Type of report to generate."
      },
      "format": {
        "type": "string",
        "enum": ["pdf", "docx", "html", "json", "csv"],
        "default": "pdf",
        "description": "Output file format."
      },
      "title": {
        "type": "string",
        "maxLength": 500,
        "description": "Custom report title. Auto-generated if omitted."
      },
      "template_id": {
        "type": "string",
        "format": "uuid",
        "description": "Custom report template to use."
      },
      "include_sections": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": [
            "cover_page", "executive_summary", "scope_methodology",
            "finding_summary", "detailed_findings", "compliance_mapping",
            "asset_inventory", "appendix_raw_output", "appendix_glossary"
          ]
        },
        "description": "Sections to include. All included if omitted."
      },
      "severity_filter": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["critical", "high", "medium", "low", "informational"]
        },
        "description": "Only include findings at these severity levels."
      },
      "compliance_frameworks": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["owasp_top10_2021", "pci_dss_4", "iso27001", "soc2", "hipaa", "nist_csf"]
        },
        "description": "Compliance frameworks to map against."
      },
      "previous_report_id": {
        "type": "string",
        "format": "uuid",
        "description": "For delta reports: the previous report to compare against."
      }
    },
    "required": ["engagement_id"]
  }
}
```

#### Handler Logic

```python
async def handle_generate_report(params, context):
    tenant_id = context.auth.tenant_id
    user_id   = context.auth.sub

    engagement = await engagement_service.get(
        tenant_id=tenant_id,
        engagement_id=params["engagement_id"]
    )
    if engagement.status not in ("in_progress", "review", "closed"):
        raise McpError(INVALID_PARAMS, "Engagement must be in 'in_progress', 'review', or 'closed' state.")

    report_type = params.get("report_type", "full_technical")
    format = params.get("format", "pdf")

    # Auto-generate title if not provided
    title = params.get("title") or (
        f"{engagement.name} — "
        f"{'Executive Summary' if report_type == 'executive_summary' else ''}"
        f"{'Full Technical Report' if report_type == 'full_technical' else ''}"
        f"{'Compliance Report' if report_type == 'compliance' else ''}"
        f"{'Delta / Retest Report' if report_type == 'delta_retest' else ''}"
        f"{'Custom Report' if report_type == 'custom' else ''}"
    )

    # Snapshot current finding state
    findings_stats = await findings_service.get_stats(
        tenant_id=tenant_id,
        engagement_id=params["engagement_id"],
        severity_filter=params.get("severity_filter"),
        status_filter=["confirmed", "accepted_risk"]
    )

    finding_snapshot = {
        "total": findings_stats.total,
        "by_severity": findings_stats.by_severity,
        "by_status": findings_stats.by_status,
        "generated_at": datetime.utcnow().isoformat()
    }

    report = await reporting_service.create_report(
        tenant_id=tenant_id,
        engagement_id=params["engagement_id"],
        title=title,
        report_type=report_type,
        format=format,
        template_id=params.get("template_id"),
        generated_by=user_id,
        finding_snapshot=finding_snapshot,
        config={
            "include_sections": params.get("include_sections"),
            "severity_filter": params.get("severity_filter"),
            "compliance_frameworks": params.get("compliance_frameworks"),
            "previous_report_id": params.get("previous_report_id")
        }
    )

    # Trigger async report generation
    await kafka.publish("report.generation_requested", {
        "report_id": str(report.id),
        "tenant_id": tenant_id,
        "engagement_id": params["engagement_id"],
        "report_type": report_type,
        "format": format
    })

    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "report_id": str(report.id),
                "status": "queued",
                "title": title,
                "report_type": report_type,
                "format": format,
                "engagement": engagement.reference_code,
                "finding_snapshot": finding_snapshot,
                "message": f"Report generation queued. Track progress with "
                           f"get_scan_status or poll report status."
            }, indent=2)
        }]
    }
```

---

### 3.9 Tool: `publish_report`

**Description:** Approve and deliver a generated report to the customer. Verifies the report has been reviewed, marks it as approved, and triggers delivery via the configured channel (portal download, email, Teams, API webhook).

**Required Permissions:** `report:approve`
**Allowed Roles:** `platform_admin`, `lead_analyst`
**Rate Limit:** 10 calls / minute / tenant

#### Input Schema

```json
{
  "name": "publish_report",
  "description": "Approve a generated report and deliver it to the customer via configured delivery channel (portal, email, Teams, or API webhook).",
  "inputSchema": {
    "type": "object",
    "properties": {
      "report_id": {
        "type": "string",
        "format": "uuid",
        "description": "The report to approve and publish."
      },
      "delivery_method": {
        "type": "string",
        "enum": ["portal_download", "email", "teams", "api_webhook"],
        "default": "portal_download",
        "description": "How to deliver the report to the customer."
      },
      "recipient_emails": {
        "type": "array",
        "items": { "type": "string", "format": "email" },
        "description": "Email recipients (required when delivery_method is 'email')."
      },
      "approval_notes": {
        "type": "string",
        "maxLength": 2000,
        "description": "Notes from the approver."
      },
      "notify_customer": {
        "type": "boolean",
        "default": true,
        "description": "Send notification to customer upon delivery."
      },
      "set_engagement_status": {
        "type": "string",
        "enum": ["review", "closed"],
        "description": "Optionally transition the engagement status after publishing."
      }
    },
    "required": ["report_id"]
  }
}
```

#### Handler Logic

```python
async def handle_publish_report(params, context):
    tenant_id = context.auth.tenant_id
    user_id   = context.auth.sub

    report = await reporting_service.get_report(
        tenant_id=tenant_id,
        report_id=params["report_id"]
    )
    if not report:
        raise McpError(INVALID_PARAMS, "Report not found.")
    if report.status not in ("generated", "under_review"):
        raise McpError(
            INVALID_PARAMS,
            f"Report is '{report.status}'. Only 'generated' or 'under_review' "
            f"reports can be published."
        )
    if not report.file_path:
        raise McpError(INTERNAL_ERROR, "Report file not found in storage.")

    delivery_method = params.get("delivery_method", "portal_download")

    if delivery_method == "email" and not params.get("recipient_emails"):
        raise McpError(INVALID_PARAMS, "recipient_emails required for email delivery.")

    # Mark report as approved
    await reporting_service.update_report(
        report_id=report.id,
        status="approved",
        approved_by=user_id,
        approved_at=datetime.utcnow(),
        delivery_method=delivery_method
    )

    # Deliver based on method
    delivery_result = {}
    if delivery_method == "portal_download":
        download_url = await reporting_service.generate_download_url(
            report_id=report.id,
            expires_hours=72
        )
        delivery_result = {"download_url": download_url, "expires_in_hours": 72}

    elif delivery_method == "email":
        await notification_service.send_report_email(
            recipients=params["recipient_emails"],
            report=report,
            notes=params.get("approval_notes")
        )
        delivery_result = {"emailed_to": params["recipient_emails"]}

    elif delivery_method == "teams":
        await notification_service.send_teams_notification(
            tenant_id=tenant_id,
            report=report,
            notes=params.get("approval_notes")
        )
        delivery_result = {"teams_notification": "sent"}

    elif delivery_method == "api_webhook":
        await notification_service.trigger_webhook(
            tenant_id=tenant_id,
            event="report.published",
            payload={"report_id": str(report.id), "download_url": download_url}
        )
        delivery_result = {"webhook": "triggered"}

    # Update delivery timestamp
    await reporting_service.update_report(
        report_id=report.id,
        status="delivered",
        delivered_at=datetime.utcnow()
    )

    # Optionally update engagement status
    if params.get("set_engagement_status"):
        engagement = await engagement_service.get(
            tenant_id=tenant_id,
            engagement_id=report.engagement_id
        )
        await engagement_service.update(
            engagement_id=engagement.id,
            status=params["set_engagement_status"]
        )

    # Publish events
    await kafka.publish("report.approved", {
        "report_id": str(report.id),
        "tenant_id": tenant_id,
        "engagement_id": str(report.engagement_id),
        "approved_by": user_id,
        "delivery_method": delivery_method
    })

    if params.get("notify_customer", True):
        await kafka.publish("notification.dispatch", {
            "type": "report_published",
            "tenant_id": tenant_id,
            "title": f"VAPT Report Available: {report.title}",
            "body": "Your vulnerability assessment report is ready for download.",
            "link": f"/reports/{report.id}"
        })

    return {
        "content": [{
            "type": "text",
            "text": json.dumps({
                "report_id": str(report.id),
                "status": "delivered",
                "title": report.title,
                "delivery_method": delivery_method,
                "delivery_result": delivery_result,
                "approved_by": context.auth.name,
                "message": f"Report '{report.title}' published via {delivery_method}."
            }, indent=2)
        }]
    }
```

---

## 4. MCP Resources — Complete Specifications

### 4.1 Resource: `engagement_scope`

**URI Template:** `vapt://engagements/{engagement_id}/scope`
**Description:** Returns the full scope definition for an engagement — included assets, authorised scan types, exclusions, testing windows, and rules of engagement.

**Supports Subscription:** Yes — notifies when scope is modified.
**Cache TTL:** 60 seconds (Redis)
**Required Permission:** `engagement:read`

#### Response Schema

```json
{
  "uri": "vapt://engagements/550e8400-e29b-41d4-a716-446655440001/scope",
  "mimeType": "application/json",
  "text": {
    "engagement_id": "550e8400-e29b-41d4-a716-446655440001",
    "reference_code": "ENG-2026-0042",
    "name": "Acme Corp Q1 Full VAPT",
    "status": "in_progress",
    "engagement_type": "full_vapt",
    "scheduled_start": "2026-03-01T00:00:00Z",
    "scheduled_end": "2026-03-31T23:59:59Z",
    "scope": {
      "assets_in_scope": [
        {
          "asset_id": "a1b2c3d4-...",
          "name": "Acme Customer Portal",
          "asset_type": "web_application",
          "identifier": "https://portal.acme.com",
          "environment": "production",
          "criticality": "critical",
          "scan_types_allowed": ["dast", "sast", "sca"],
          "excluded_paths": ["/admin/debug", "/health"],
          "target_count": 3
        },
        {
          "asset_id": "b2c3d4e5-...",
          "name": "Acme Internal Network",
          "asset_type": "network_range",
          "identifier": "10.0.0.0/16",
          "environment": "production",
          "criticality": "high",
          "scan_types_allowed": ["infrastructure"],
          "excluded_paths": [],
          "target_count": 254
        }
      ],
      "total_assets": 2,
      "scan_types_summary": ["dast", "sast", "sca", "infrastructure"],
      "testing_window": {
        "start": "02:00Z",
        "end": "06:00Z",
        "timezone": "UTC",
        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
      },
      "rate_limits": {
        "max_requests_per_second": 50,
        "max_concurrent_scans": 5
      },
      "rules_of_engagement": "No DoS testing. No data exfiltration. Production rate limiting enforced. Emergency contact: security@acme.com (+1-555-0123)."
    },
    "compliance_frameworks": ["pci_dss_4", "owasp_top10_2021"],
    "assigned_lead": {
      "user_id": "analyst-uuid",
      "display_name": "Jane Doe"
    }
  }
}
```

#### Subscription Notification

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/resources/updated",
  "params": {
    "uri": "vapt://engagements/550e8400-e29b-41d4-a716-446655440001/scope"
  }
}
```

---

### 4.2 Resource: `targets`

**URI Template:** `vapt://engagements/{engagement_id}/targets`
**Description:** Returns all concrete network-level targets for an engagement — the specific hosts, ports, URLs, and protocols that scanners will point at.

**Supports Subscription:** Yes — notifies when targets are added, removed, or reachability changes.
**Cache TTL:** 30 seconds
**Required Permission:** `engagement:read`, `asset:read`

#### Response Schema

```json
{
  "uri": "vapt://engagements/550e8400-e29b-41d4-a716-446655440001/targets",
  "mimeType": "application/json",
  "text": {
    "engagement_id": "550e8400-e29b-41d4-a716-446655440001",
    "total_targets": 5,
    "targets": [
      {
        "target_id": "t1-uuid",
        "asset_id": "a1b2c3d4-...",
        "asset_name": "Acme Customer Portal",
        "host": "portal.acme.com",
        "port": 443,
        "protocol": "https",
        "url": "https://portal.acme.com",
        "requires_auth": true,
        "credential_profile_id": "cred-uuid-1",
        "is_reachable": true,
        "last_reachability_check": "2026-03-14T08:00:00Z",
        "max_requests_per_second": 50,
        "scan_window": { "start": "02:00", "end": "06:00" }
      },
      {
        "target_id": "t2-uuid",
        "asset_id": "a1b2c3d4-...",
        "asset_name": "Acme Customer Portal",
        "host": "api.acme.com",
        "port": 443,
        "protocol": "https",
        "url": "https://api.acme.com/v2",
        "requires_auth": true,
        "credential_profile_id": "cred-uuid-2",
        "is_reachable": true,
        "last_reachability_check": "2026-03-14T08:00:00Z",
        "max_requests_per_second": 30,
        "scan_window": null
      },
      {
        "target_id": "t3-uuid",
        "asset_id": "b2c3d4e5-...",
        "asset_name": "Acme Internal Network",
        "host": "10.0.1.0/24",
        "port": null,
        "protocol": "tcp_custom",
        "url": null,
        "requires_auth": true,
        "credential_profile_id": "cred-uuid-3",
        "is_reachable": true,
        "last_reachability_check": "2026-03-14T07:55:00Z",
        "max_requests_per_second": 100,
        "scan_window": { "start": "02:00", "end": "06:00" }
      }
    ],
    "reachability_summary": {
      "reachable": 4,
      "unreachable": 1,
      "unknown": 0
    }
  }
}
```

---

### 4.3 Resource: `credential_profiles`

**URI Template:** `vapt://engagements/{engagement_id}/credentials`
**Description:** Returns metadata for all credential profiles linked to an engagement's in-scope assets. Never exposes actual secrets — only Vault references, types, scope, rotation status, and validity.

**Supports Subscription:** Yes — notifies on expiry, rotation, or checkout state changes.
**Cache TTL:** 30 seconds
**Required Permission:** `credential:read` (metadata only)

#### Response Schema

```json
{
  "uri": "vapt://engagements/550e8400-e29b-41d4-a716-446655440001/credentials",
  "mimeType": "application/json",
  "text": {
    "engagement_id": "550e8400-e29b-41d4-a716-446655440001",
    "total_credential_profiles": 3,
    "credential_profiles": [
      {
        "credential_profile_id": "cred-uuid-1",
        "name": "Acme Portal - Admin Login",
        "credential_type": "username_password",
        "scope": "target_auth",
        "status": "active",
        "linked_targets": ["t1-uuid"],
        "is_checked_out": false,
        "last_tested_at": "2026-03-13T14:00:00Z",
        "last_test_passed": true,
        "rotation_enabled": false,
        "expires_at": null
      },
      {
        "credential_profile_id": "cred-uuid-2",
        "name": "Acme API - OAuth2 Service Account",
        "credential_type": "oauth2_token",
        "scope": "target_auth",
        "status": "active",
        "linked_targets": ["t2-uuid"],
        "is_checked_out": true,
        "checked_out_by": "scan-orchestration:scan-job-uuid",
        "checkout_expires_at": "2026-03-14T16:00:00Z",
        "last_tested_at": "2026-03-14T08:30:00Z",
        "last_test_passed": true,
        "rotation_enabled": true,
        "last_rotated_at": "2026-03-10T00:00:00Z",
        "expires_at": "2026-04-10T00:00:00Z"
      },
      {
        "credential_profile_id": "cred-uuid-3",
        "name": "Acme Network - SSH Root",
        "credential_type": "ssh_keypair",
        "scope": "scanner_auth",
        "status": "active",
        "linked_targets": ["t3-uuid", "t4-uuid", "t5-uuid"],
        "is_checked_out": false,
        "last_tested_at": "2026-03-14T07:00:00Z",
        "last_test_passed": true,
        "rotation_enabled": true,
        "last_rotated_at": "2026-03-01T00:00:00Z",
        "expires_at": "2026-06-01T00:00:00Z"
      }
    ],
    "warnings": [
      {
        "credential_profile_id": "cred-uuid-2",
        "warning": "credential_checked_out",
        "message": "Credential is currently checked out by an active scan."
      }
    ]
  }
}
```

---

### 4.4 Resource: `scan_status`

**URI Templates:**
- `vapt://scans/{scan_id}/status` — single scan status
- `vapt://engagements/{engagement_id}/scans` — all scans for an engagement

**Description:** Real-time scan status and progress. Subscriptions deliver updates on every state transition and every 10% progress increment.

**Supports Subscription:** Yes — real-time updates on state transitions and progress.
**Cache TTL:** 10 seconds (frequently changing)
**Required Permission:** `scan:read`

#### Response Schema (Single Scan)

```json
{
  "uri": "vapt://scans/scan-job-uuid-1/status",
  "mimeType": "application/json",
  "text": {
    "scan_job_id": "scan-job-uuid-1",
    "engagement_id": "550e8400-e29b-41d4-a716-446655440001",
    "scan_type": "dast",
    "scanner_engine": "burp_suite",
    "status": "running",
    "progress_percent": 65,
    "priority": 3,
    "target": {
      "host": "portal.acme.com",
      "port": 443,
      "url": "https://portal.acme.com"
    },
    "timing": {
      "queued_at": "2026-03-14T02:00:00Z",
      "started_at": "2026-03-14T02:01:30Z",
      "elapsed_seconds": 5670,
      "estimated_remaining_seconds": 3060,
      "max_duration_seconds": 14400
    },
    "attempt": {
      "current": 1,
      "max": 3
    },
    "temporal_workflow_id": "scan-burp-scan-job-uuid-1",
    "findings_so_far": {
      "critical": 1,
      "high": 3,
      "medium": 8,
      "low": 5,
      "info": 12,
      "total": 29
    }
  }
}
```

#### Response Schema (Engagement Scans)

```json
{
  "uri": "vapt://engagements/550e8400-e29b-41d4-a716-446655440001/scans",
  "mimeType": "application/json",
  "text": {
    "engagement_id": "550e8400-e29b-41d4-a716-446655440001",
    "total_scans": 4,
    "overall_progress_percent": 58.75,
    "by_status": {
      "completed": 1,
      "running": 2,
      "queued": 1
    },
    "scans": [
      {
        "scan_job_id": "scan-job-uuid-1",
        "scan_type": "dast",
        "scanner": "burp_suite",
        "status": "running",
        "progress": 65,
        "target": "portal.acme.com:443",
        "findings": 29
      },
      {
        "scan_job_id": "scan-job-uuid-2",
        "scan_type": "infrastructure",
        "scanner": "tenable_io",
        "status": "running",
        "progress": 40,
        "target": "10.0.1.0/24 (254 hosts)",
        "findings": 15
      },
      {
        "scan_job_id": "scan-job-uuid-3",
        "scan_type": "sast",
        "scanner": "fortify_sast",
        "status": "completed",
        "progress": 100,
        "target": "github.com/acme/portal (main)",
        "findings": 42
      },
      {
        "scan_job_id": "scan-job-uuid-4",
        "scan_type": "sca",
        "scanner": "fortify_sca",
        "status": "queued",
        "progress": 0,
        "target": "github.com/acme/portal (main)",
        "findings": 0
      }
    ]
  }
}
```

#### Subscription Notification (Progress Update)

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/resources/updated",
  "params": {
    "uri": "vapt://scans/scan-job-uuid-1/status"
  }
}
```

---

### 4.5 Resource: `findings_summary`

**URI Template:** `vapt://engagements/{engagement_id}/findings/summary`
**Description:** Aggregated findings summary for an engagement — severity breakdown, status distribution, top vulnerability categories, compliance coverage, and risk score.

**Supports Subscription:** Yes — notifies when findings are normalised, validated, or status changes.
**Cache TTL:** 30 seconds
**Required Permission:** `finding:read`

#### Response Schema

```json
{
  "uri": "vapt://engagements/550e8400-e29b-41d4-a716-446655440001/findings/summary",
  "mimeType": "application/json",
  "text": {
    "engagement_id": "550e8400-e29b-41d4-a716-446655440001",
    "reference_code": "ENG-2026-0042",
    "generated_at": "2026-03-14T12:00:00Z",
    "total_findings": 86,
    "by_severity": {
      "critical": 3,
      "high": 12,
      "medium": 28,
      "low": 25,
      "informational": 18
    },
    "by_status": {
      "new": 15,
      "confirmed": 45,
      "false_positive": 8,
      "accepted_risk": 3,
      "remediated": 12,
      "reopened": 2,
      "duplicate": 1
    },
    "by_scan_type": {
      "dast": 29,
      "sast": 32,
      "sca": 10,
      "infrastructure": 15
    },
    "by_scanner": {
      "burp_suite": 29,
      "fortify_sast": 32,
      "fortify_sca": 10,
      "tenable_io": 15
    },
    "top_categories": [
      { "category": "SQL Injection", "count": 5, "max_severity": "critical" },
      { "category": "Cross-Site Scripting (XSS)", "count": 8, "max_severity": "high" },
      { "category": "Insecure Deserialization", "count": 3, "max_severity": "critical" },
      { "category": "Outdated Component", "count": 10, "max_severity": "high" },
      { "category": "SSH Weak Cipher", "count": 6, "max_severity": "medium" }
    ],
    "top_affected_assets": [
      { "asset_name": "Acme Customer Portal", "finding_count": 42, "critical": 2, "high": 7 },
      { "asset_name": "Acme Internal Network", "finding_count": 15, "critical": 0, "high": 3 },
      { "asset_name": "Acme API Gateway", "finding_count": 29, "critical": 1, "high": 2 }
    ],
    "risk_score": 78,
    "risk_trend": "increasing",
    "compliance_coverage": {
      "owasp_top10_2021": {
        "controls_tested": 10,
        "controls_passed": 6,
        "controls_failed": 4,
        "coverage_percent": 60.0
      },
      "pci_dss_4": {
        "controls_tested": 42,
        "controls_passed": 35,
        "controls_failed": 7,
        "coverage_percent": 83.3
      }
    },
    "validation_progress": {
      "total_requiring_validation": 60,
      "validated": 45,
      "pending": 15,
      "percent_complete": 75.0
    },
    "ai_insights": {
      "likely_false_positives": 5,
      "high_exploitability_count": 8,
      "estimated_remediation_hours": 120,
      "most_urgent": "3 critical SQL injection findings on production portal require immediate attention."
    }
  }
}
```

---

## 5. Example Tool Calls — JSON-RPC 2.0

### 5.1 start_burp_scan

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "method": "tools/call",
  "params": {
    "name": "start_burp_scan",
    "arguments": {
      "engagement_id": "550e8400-e29b-41d4-a716-446655440001",
      "target_id": "660f9500-f39c-52e5-b827-557766550002",
      "scan_profile": "crawl_and_audit_full",
      "credential_profile_id": "770a0600-a40d-63f6-c938-668877660003",
      "excluded_paths": ["/logout", "/admin/debug", "/health"],
      "max_duration_minutes": 240,
      "priority": 3,
      "custom_config": {
        "rate_limit_rps": 30,
        "custom_headers": {
          "X-Custom-Tenant": "acme"
        }
      }
    }
  }
}
```

**Success Response:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"scan_job_id\": \"880b1700-b51e-74g7-d049-779988770004\", \"status\": \"dispatched\", \"scanner\": \"burp_suite\", \"scan_type\": \"dast\", \"target\": \"https://portal.acme.com\", \"engagement\": \"ENG-2026-0042\", \"priority\": 3, \"estimated_duration_minutes\": 240, \"temporal_workflow_id\": \"scan-burp-880b1700-b51e-74g7-d049-779988770004\", \"message\": \"Burp Suite DAST scan dispatched against https://portal.acme.com. Track progress with get_scan_status or subscribe to vapt://scans/880b1700-b51e-74g7-d049-779988770004/status\"}"
    }]
  }
}
```

**Error Response (Engagement not in scannable state):**

```json
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "error": {
    "code": -32602,
    "message": "Engagement ENG-2026-0042 is 'draft'; must be 'approved' or 'in_progress' to launch scans."
  }
}
```

---

### 5.2 start_tenable_scan

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-002",
  "method": "tools/call",
  "params": {
    "name": "start_tenable_scan",
    "arguments": {
      "engagement_id": "550e8400-e29b-41d4-a716-446655440001",
      "target_ids": [
        "t3-uuid-001",
        "t4-uuid-002"
      ],
      "scan_template": "advanced",
      "credential_profile_ids": ["cred-uuid-3"],
      "port_range": "1-65535",
      "max_duration_minutes": 480,
      "priority": 5,
      "scan_window": {
        "start_time": "02:00",
        "end_time": "06:00"
      }
    }
  }
}
```

**Success Response:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-002",
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"scan_job_id\": \"990c2800-c62f-85h8-e150-880099880005\", \"status\": \"dispatched\", \"scanner\": \"tenable_io\", \"scan_type\": \"infrastructure\", \"targets\": [\"10.0.1.0/24\", \"10.0.2.0/24\"], \"target_count\": 2, \"template\": \"advanced\", \"engagement\": \"ENG-2026-0042\", \"temporal_workflow_id\": \"scan-tenable-990c2800-c62f-85h8-e150-880099880005\", \"message\": \"Tenable infrastructure scan dispatched against 2 targets.\"}"
    }]
  }
}
```

---

### 5.3 start_fortify_scan

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-003",
  "method": "tools/call",
  "params": {
    "name": "start_fortify_scan",
    "arguments": {
      "engagement_id": "550e8400-e29b-41d4-a716-446655440001",
      "asset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "scan_subtype": "sast_and_sca",
      "repo_url": "https://github.com/acme-corp/customer-portal.git",
      "branch": "main",
      "languages": ["java", "javascript", "typescript"],
      "credential_profile_id": "cred-repo-uuid",
      "exclude_patterns": ["**/test/**", "**/node_modules/**"]
    }
  }
}
```

**Success Response:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-003",
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"scan_jobs\": [{\"scan_job_id\": \"sast-job-uuid\", \"scan_type\": \"sast\", \"workflow_id\": \"scan-fortify-sast-sast-job-uuid\"}, {\"scan_job_id\": \"sca-job-uuid\", \"scan_type\": \"sca\", \"workflow_id\": \"scan-fortify-sca-sca-job-uuid\"}], \"status\": \"dispatched\", \"scanner\": \"fortify\", \"repo\": \"https://github.com/acme-corp/customer-portal.git\", \"branch\": \"main\", \"engagement\": \"ENG-2026-0042\", \"message\": \"Fortify SAST_AND_SCA scan dispatched for https://github.com/acme-corp/customer-portal.git (main).\"}"
    }]
  }
}
```

---

### 5.4 start_mobile_scan

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-004",
  "method": "tools/call",
  "params": {
    "name": "start_mobile_scan",
    "arguments": {
      "engagement_id": "550e8400-e29b-41d4-a716-446655440001",
      "asset_id": "mobile-asset-uuid",
      "platform": "android",
      "binary_reference": "uploads/acme-portal-v3.2.1.apk",
      "analysis_type": "static_and_dynamic",
      "credential_profile_id": "cred-mobile-login-uuid",
      "max_duration_minutes": 120,
      "priority": 5
    }
  }
}
```

**Success Response:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-004",
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"scan_jobs\": [{\"scan_job_id\": \"mobile-static-uuid\", \"scan_type\": \"mobile_static\", \"workflow_id\": \"scan-mobile-static-mobile-static-uuid\"}, {\"scan_job_id\": \"mobile-dynamic-uuid\", \"scan_type\": \"mobile_dynamic\", \"workflow_id\": \"scan-mobile-dynamic-mobile-dynamic-uuid\"}], \"status\": \"dispatched\", \"scanner\": \"mobsf\", \"platform\": \"android\", \"analysis_type\": \"static_and_dynamic\", \"engagement\": \"ENG-2026-0042\", \"message\": \"MobSF android scan dispatched (static_and_dynamic).\"}"
    }]
  }
}
```

---

### 5.5 get_scan_status

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-005",
  "method": "tools/call",
  "params": {
    "name": "get_scan_status",
    "arguments": {
      "scan_job_id": "880b1700-b51e-74g7-d049-779988770004",
      "include_logs": true
    }
  }
}
```

**Success Response:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-005",
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"scan_job_id\": \"880b1700-b51e-74g7-d049-779988770004\", \"status\": \"running\", \"scan_type\": \"dast\", \"scanner_engine\": \"burp_suite\", \"progress_percent\": 65, \"priority\": 3, \"queued_at\": \"2026-03-14T02:00:00Z\", \"started_at\": \"2026-03-14T02:01:30Z\", \"completed_at\": null, \"duration_seconds\": 5670, \"attempt_number\": 1, \"max_attempts\": 3, \"last_error\": null, \"recent_logs\": [{\"level\": \"info\", \"message\": \"Crawl phase complete: 1,247 URLs discovered\", \"timestamp\": \"2026-03-14T02:45:00Z\"}, {\"level\": \"info\", \"message\": \"Audit phase: 65% complete (823/1,247 URLs audited)\", \"timestamp\": \"2026-03-14T03:35:00Z\"}, {\"level\": \"warn\", \"message\": \"Rate limited by target: backing off to 20 req/s\", \"timestamp\": \"2026-03-14T03:12:00Z\"}]}"
    }]
  }
}
```

---

### 5.6 fetch_scan_results

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-006",
  "method": "tools/call",
  "params": {
    "name": "fetch_scan_results",
    "arguments": {
      "scan_job_id": "sast-job-uuid",
      "severity_filter": ["critical", "high"],
      "include_evidence": true,
      "include_ai_analysis": true,
      "page": 1,
      "page_size": 10
    }
  }
}
```

**Success Response:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-006",
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"scan_job_id\": \"sast-job-uuid\", \"scanner\": \"fortify_sast\", \"scan_type\": \"sast\", \"total_findings\": 15, \"page\": 1, \"page_size\": 10, \"total_pages\": 2, \"summary\": {\"critical\": 3, \"high\": 12, \"medium\": 0, \"low\": 0, \"info\": 0}, \"findings\": [{\"finding_id\": \"f1-uuid\", \"title\": \"SQL Injection in UserDAO.findByEmail()\", \"category\": \"SQL Injection\", \"severity\": \"critical\", \"confidence\": \"confirmed\", \"status\": \"new\", \"cvss_score\": 9.8, \"cvss_vector\": \"CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H\", \"cwe_id\": \"CWE-89\", \"cve_ids\": [], \"owasp_category\": \"A03:2021\", \"affected_file\": \"src/main/java/com/acme/dao/UserDAO.java\", \"affected_line\": 142, \"affected_component\": null, \"remediation\": \"Use parameterized queries or PreparedStatement instead of string concatenation.\", \"remediation_effort\": \"low\", \"evidence\": [{\"type\": \"code_snippet\", \"content\": \"String query = \\\"SELECT * FROM users WHERE email = '\\\" + email + \\\"'\\\"; // VULNERABLE\", \"file\": \"src/main/java/com/acme/dao/UserDAO.java\", \"line\": 142}, {\"type\": \"data_flow\", \"content\": \"Source: HttpServletRequest.getParameter(\\\"email\\\") → Sink: Statement.executeQuery()\"}], \"ai_analysis\": {\"severity_score\": 9.8, \"exploitability_score\": 9.5, \"false_positive_probability\": 0.02, \"ai_remediation\": \"Replace string concatenation with PreparedStatement: PreparedStatement ps = conn.prepareStatement(\\\"SELECT * FROM users WHERE email = ?\\\"); ps.setString(1, email);\", \"analyzed_at\": \"2026-03-14T10:30:00Z\"}}]}"
    }]
  }
}
```

---

### 5.7 assign_analyst

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-007",
  "method": "tools/call",
  "params": {
    "name": "assign_analyst",
    "arguments": {
      "analyst_id": "analyst-jane-uuid",
      "finding_ids": ["f1-uuid", "f2-uuid", "f3-uuid"],
      "assignment_type": "finding_validation",
      "notes": "Critical SQL injection findings — please validate with manual testing and confirm exploitability.",
      "priority_override": "critical"
    }
  }
}
```

**Success Response:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-007",
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"analyst\": \"Jane Doe\", \"assignments\": [{\"type\": \"finding_validation\", \"findings_assigned\": 3, \"status\": \"assigned\"}], \"message\": \"Successfully assigned Jane Doe.\"}"
    }]
  }
}
```

---

### 5.8 generate_report

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-008",
  "method": "tools/call",
  "params": {
    "name": "generate_report",
    "arguments": {
      "engagement_id": "550e8400-e29b-41d4-a716-446655440001",
      "report_type": "full_technical",
      "format": "pdf",
      "title": "Acme Corp — Q1 2026 Full VAPT Report",
      "compliance_frameworks": ["owasp_top10_2021", "pci_dss_4"],
      "severity_filter": ["critical", "high", "medium"]
    }
  }
}
```

**Success Response:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-008",
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"report_id\": \"rpt-uuid-001\", \"status\": \"queued\", \"title\": \"Acme Corp \\u2014 Q1 2026 Full VAPT Report\", \"report_type\": \"full_technical\", \"format\": \"pdf\", \"engagement\": \"ENG-2026-0042\", \"finding_snapshot\": {\"total\": 43, \"by_severity\": {\"critical\": 3, \"high\": 12, \"medium\": 28}, \"by_status\": {\"confirmed\": 38, \"accepted_risk\": 5}}, \"message\": \"Report generation queued. Track progress with get_scan_status or poll report status.\"}"
    }]
  }
}
```

---

### 5.9 publish_report

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-009",
  "method": "tools/call",
  "params": {
    "name": "publish_report",
    "arguments": {
      "report_id": "rpt-uuid-001",
      "delivery_method": "email",
      "recipient_emails": ["ciso@acme.com", "security-team@acme.com"],
      "approval_notes": "Report reviewed and approved. All critical findings confirmed with manual validation.",
      "notify_customer": true,
      "set_engagement_status": "closed"
    }
  }
}
```

**Success Response:**

```json
{
  "jsonrpc": "2.0",
  "id": "req-009",
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"report_id\": \"rpt-uuid-001\", \"status\": \"delivered\", \"title\": \"Acme Corp \\u2014 Q1 2026 Full VAPT Report\", \"delivery_method\": \"email\", \"delivery_result\": {\"emailed_to\": [\"ciso@acme.com\", \"security-team@acme.com\"]}, \"approved_by\": \"Jane Doe\", \"message\": \"Report 'Acme Corp \\u2014 Q1 2026 Full VAPT Report' published via email.\"}"
    }]
  }
}
```

---

## 6. Event Workflow — End-to-End Sequence

### 6.1 Full Engagement Lifecycle

```
Timeline ──────────────────────────────────────────────────────────────────────────────►

 AI Agent / Analyst                MCP Server                Platform Services           Kafka
 ═══════════════                   ══════════                 ═════════════════           ═════
       │                               │                           │                       │
       │  ┌─────────────────────┐      │                           │                       │
       │  │ PHASE 1: SCOPE      │      │                           │                       │
       │  └─────────────────────┘      │                           │                       │
       │                               │                           │                       │
       │  resources/read               │                           │                       │
       │  engagement_scope ───────────►│                           │                       │
       │                               │──► Engagement Service     │                       │
       │                               │    GET /engagements/{id}  │                       │
       │                               │◄── scope + assets         │                       │
       │  ◄── scope definition ────────│                           │                       │
       │                               │                           │                       │
       │  resources/read               │                           │                       │
       │  targets ────────────────────►│                           │                       │
       │                               │──► Asset Service          │                       │
       │                               │    GET /targets?eng={id}  │                       │
       │                               │◄── target list            │                       │
       │  ◄── target details ──────────│                           │                       │
       │                               │                           │                       │
       │  resources/read               │                           │                       │
       │  credential_profiles ────────►│                           │                       │
       │                               │──► Credential Vault       │                       │
       │                               │    GET /credentials       │                       │
       │                               │◄── metadata (no secrets)  │                       │
       │  ◄── credential metadata ─────│                           │                       │
       │                               │                           │                       │
       │  resources/subscribe          │                           │                       │
       │  scan_status ────────────────►│  (register subscription)  │                       │
       │                               │                           │                       │
       │  ┌─────────────────────┐      │                           │                       │
       │  │ PHASE 2: SCAN       │      │                           │                       │
       │  └─────────────────────┘      │                           │                       │
       │                               │                           │                       │
       │  tools/call                   │                           │                       │
       │  start_burp_scan ────────────►│                           │                       │
       │                               │──► Engagement Svc         │                       │
       │                               │    (validate status)      │                       │
       │                               │──► Asset Svc              │                       │
       │                               │    (validate scope)       │                       │
       │                               │──► Scan Orch Svc          │                       │
       │                               │    POST /scans            │                       │
       │                               │                           │──► scan.requested ───►│
       │                               │                           │                       │
       │                               │    Temporal: ScanWorkflow │                       │
       │                               │    ┌─ ValidateRequest     │                       │
       │                               │    ├─ CheckoutCredential ─┼──► Vault Svc          │
       │                               │    ├─ DispatchToScanner ──┼──► Burp Connector     │
       │                               │    │  (gRPC StartScan)    │    (Burp Enterprise)  │
       │  ◄── scan_job_id + status ────│    │                      │                       │
       │                               │    │                      │                       │
       │                               │    ├─ MonitorProgress ────┤  (poll every 30s)     │
       │                               │    │  ┌──────────┐        │                       │
       │  ◄── SSE: resource updated ───│    │  │ 10% ───► │  notify│                       │
       │  ◄── SSE: resource updated ───│    │  │ 20% ───► │  notify│                       │
       │  ◄── SSE: resource updated ───│    │  │ ... ───► │  notify│                       │
       │  ◄── SSE: resource updated ───│    │  │ 100% ──► │  notify│                       │
       │                               │    │  └──────────┘        │                       │
       │                               │    ├─ CollectResults ─────┼──► Burp Connector     │
       │                               │    │  (gRPC GetResults)   │    (stream findings)  │
       │                               │    ├─ PublishResults      │                       │
       │                               │    │                      │──► scan.completed ───►│
       │                               │    ├─ CheckinCredential ──┼──► Vault Svc          │
       │                               │    └─ UpdateStatus        │                       │
       │                               │                           │                       │
       │                               │                           │   Kafka Consumer:      │
       │                               │                           │   Findings Service     │
       │                               │                           │   ├─ Parse raw output  │
       │                               │                           │   ├─ Normalize schema  │
       │                               │                           │   ├─ Deduplicate       │
       │                               │                           │   ├─ AI enrichment     │
       │                               │                           │──► finding.normalized ►│
       │                               │                           │                       │
       │  ◄── SSE: findings_summary ───│  (resource notification)  │                       │
       │      updated                  │                           │                       │
       │                               │                           │                       │
       │  tools/call                   │                           │                       │
       │  start_tenable_scan ─────────►│  (same flow as above)     │                       │
       │                               │                           │                       │
       │  tools/call                   │                           │                       │
       │  start_fortify_scan ─────────►│  (same flow as above)     │                       │
       │                               │                           │                       │
       │  ┌─────────────────────┐      │                           │                       │
       │  │ PHASE 3: TRIAGE     │      │                           │                       │
       │  └─────────────────────┘      │                           │                       │
       │                               │                           │                       │
       │  tools/call                   │                           │                       │
       │  fetch_scan_results ─────────►│                           │                       │
       │                               │──► Findings Service       │                       │
       │                               │    GET /findings          │                       │
       │  ◄── normalised findings ─────│                           │                       │
       │                               │                           │                       │
       │  tools/call                   │                           │                       │
       │  assign_analyst ─────────────►│                           │                       │
       │                               │──► Analyst Workflow Svc   │                       │
       │                               │    POST /assignments      │                       │
       │                               │                           │──► notification ──────►│
       │  ◄── assignment confirmed ────│                           │    .dispatch           │
       │                               │                           │                       │
       │                               │                           │   Analyst validates    │
       │                               │                           │   findings manually    │
       │                               │                           │──► finding.validated ─►│
       │                               │                           │                       │
       │  ◄── SSE: findings_summary ───│  (resource notification)  │                       │
       │      updated                  │                           │                       │
       │                               │                           │                       │
       │  ┌─────────────────────┐      │                           │                       │
       │  │ PHASE 4: REPORT     │      │                           │                       │
       │  └─────────────────────┘      │                           │                       │
       │                               │                           │                       │
       │  tools/call                   │                           │                       │
       │  generate_report ────────────►│                           │                       │
       │                               │──► Reporting Service      │                       │
       │                               │    POST /reports          │                       │
       │                               │                           │   (async generation)   │
       │  ◄── report_id + queued ──────│                           │                       │
       │                               │                           │──► report.generated ──►│
       │                               │                           │                       │
       │  ◄── SSE: report ready ───────│  (resource notification)  │                       │
       │                               │                           │                       │
       │  tools/call                   │                           │                       │
       │  publish_report ─────────────►│                           │                       │
       │                               │──► Reporting Service      │                       │
       │                               │    POST /reports/{id}/    │                       │
       │                               │         approve           │                       │
       │                               │──► Notification Service   │                       │
       │                               │    (email delivery)       │                       │
       │                               │──► Engagement Service     │                       │
       │                               │    (status → closed)      │                       │
       │                               │                           │──► report.approved ───►│
       │  ◄── delivered confirmation ──│                           │                       │
       │                               │                           │                       │
       ▼                               ▼                           ▼                       ▼
```

### 6.2 Event-to-Resource Subscription Mapping

| Kafka Event | Triggers Resource Notification | Description |
|---|---|---|
| `scan.requested` | `vapt://engagements/{id}/scans` | New scan added to engagement |
| `scan.progress` | `vapt://scans/{id}/status` | Progress update (every 10%) |
| `scan.completed` | `vapt://scans/{id}/status`, `vapt://engagements/{id}/scans` | Scan finished |
| `scan.failed` | `vapt://scans/{id}/status`, `vapt://engagements/{id}/scans` | Scan failed |
| `finding.normalized` | `vapt://engagements/{id}/findings/summary` | New findings added |
| `finding.validated` | `vapt://engagements/{id}/findings/summary` | Finding triage completed |
| `report.generated` | (notified via tool polling) | Report ready for review |
| `engagement.scope_changed` | `vapt://engagements/{id}/scope`, `vapt://engagements/{id}/targets` | Scope modified |
| `credential.rotated` | `vapt://engagements/{id}/credentials` | Credential rotated |
| `credential.expired` | `vapt://engagements/{id}/credentials` | Credential expired |

### 6.3 Kafka Consumer Integration

The MCP server runs a Kafka consumer group that maps events to resource notifications:

```typescript
// MCP Server — Kafka consumer for resource subscriptions
class McpKafkaConsumer {
  private subscriptions: Map<string, Set<string>> = new Map();  // uri → client IDs

  async consume(event: KafkaEvent): Promise<void> {
    const affectedUris = this.mapEventToUris(event);

    for (const uri of affectedUris) {
      if (this.subscriptions.has(uri)) {
        // Invalidate cache
        await redis.del(`resource:${uri}`);

        // Notify all subscribed clients via SSE
        for (const clientId of this.subscriptions.get(uri)!) {
          await this.notifyClient(clientId, {
            jsonrpc: "2.0",
            method: "notifications/resources/updated",
            params: { uri }
          });
        }
      }
    }
  }

  private mapEventToUris(event: KafkaEvent): string[] {
    switch (event.topic) {
      case "scan.progress":
      case "scan.completed":
      case "scan.failed":
        return [
          `vapt://scans/${event.payload.scan_job_id}/status`,
          `vapt://engagements/${event.payload.engagement_id}/scans`
        ];
      case "finding.normalized":
      case "finding.validated":
        return [
          `vapt://engagements/${event.payload.engagement_id}/findings/summary`
        ];
      case "credential.rotated":
      case "credential.expired":
        return [
          `vapt://engagements/${event.payload.engagement_id}/credentials`
        ];
      default:
        return [];
    }
  }
}
```

---

## 7. Server Configuration

### 7.1 Environment Variables

```bash
# ── Server ──
MCP_SERVER_PORT=3100
MCP_SERVER_HOST=0.0.0.0
MCP_TRANSPORT=sse                          # 'sse' | 'streamable-http' | 'stdio'
MCP_LOG_LEVEL=info                         # 'debug' | 'info' | 'warn' | 'error'
MCP_CORS_ORIGINS=https://analyst.vapt-platform.io,https://portal.vapt-platform.io

# ── Authentication ──
KEYCLOAK_ISSUER=https://auth.vapt-platform.io/realms/vapt
KEYCLOAK_JWKS_URI=https://auth.vapt-platform.io/realms/vapt/protocol/openid-connect/certs
KEYCLOAK_AUDIENCE=mcp-orchestration-server
JWT_CLOCK_TOLERANCE_SECONDS=30

# ── Platform Services ──
ENGAGEMENT_SERVICE_URL=http://engagement-service.vapt-platform.svc:8080
ASSET_SERVICE_URL=http://asset-service.vapt-platform.svc:8080
SCAN_ORCHESTRATION_URL=http://scan-orchestration.vapt-platform.svc:8080
FINDINGS_SERVICE_URL=http://findings-service.vapt-platform.svc:8080
CREDENTIAL_VAULT_URL=http://credential-vault.vapt-platform.svc:8080
REPORTING_SERVICE_URL=http://reporting-service.vapt-platform.svc:8080
ANALYST_WORKFLOW_URL=http://analyst-workflow.vapt-platform.svc:8080
NOTIFICATION_SERVICE_URL=http://notification-service.vapt-platform.svc:8080

# ── Kafka ──
KAFKA_BROKERS=kafka-0.kafka.vapt-platform.svc:9092,kafka-1.kafka.vapt-platform.svc:9092
KAFKA_CONSUMER_GROUP=mcp-orchestration-server
KAFKA_TOPICS=scan.requested,scan.progress,scan.completed,scan.failed,finding.normalized,finding.validated,credential.rotated,credential.expired

# ── Redis ──
REDIS_URL=redis://redis.vapt-platform.svc:6379/0
REDIS_CACHE_TTL_SECONDS=30

# ── Observability ──
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector.monitoring.svc:4317
OTEL_SERVICE_NAME=mcp-orchestration-server
PROMETHEUS_METRICS_PORT=9090

# ── Rate Limiting ──
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_DEFAULT_MAX=30
```

### 7.2 Health Checks

```
GET /health/live     → 200 { "status": "ok" }                    (Kubernetes liveness)
GET /health/ready    → 200 { "status": "ok", "checks": {...} }   (Kubernetes readiness)
GET /health/startup  → 200 { "status": "ok" }                    (Kubernetes startup)

Readiness checks:
  • PostgreSQL connection
  • Redis connection
  • Kafka consumer group active
  • Keycloak JWKS endpoint reachable
  • All platform service URLs responding to /health
```

### 7.3 Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-orchestration-server
  namespace: vapt-platform
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    spec:
      containers:
        - name: mcp-server
          image: vapt-platform/mcp-orchestration-server:1.0.0
          ports:
            - containerPort: 3100   # MCP SSE
              name: mcp
            - containerPort: 9090   # Prometheus metrics
              name: metrics
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: 1000m
              memory: 1Gi
          livenessProbe:
            httpGet:
              path: /health/live
              port: 3100
            initialDelaySeconds: 10
            periodSeconds: 15
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 3100
            initialDelaySeconds: 5
            periodSeconds: 10
          startupProbe:
            httpGet:
              path: /health/startup
              port: 3100
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 12
          env:
            - name: MCP_SERVER_PORT
              value: "3100"
            - name: MCP_TRANSPORT
              value: "sse"
          envFrom:
            - configMapRef:
                name: mcp-server-config
            - secretRef:
                name: mcp-server-secrets
      serviceAccountName: mcp-orchestration-server
```

### 7.4 Graceful Shutdown

```typescript
// Graceful shutdown sequence
process.on("SIGTERM", async () => {
  logger.info("SIGTERM received — initiating graceful shutdown");

  // 1. Stop accepting new MCP connections
  await sseTransport.stopAcceptingConnections();

  // 2. Disconnect Kafka consumer (stop processing events)
  await kafkaConsumer.disconnect();

  // 3. Wait for in-flight tool calls to complete (max 30s)
  await toolHandler.drainInFlight({ timeoutMs: 30_000 });

  // 4. Notify connected clients of shutdown
  for (const client of connectedClients) {
    await client.sendNotification("server/shutdown", {
      reason: "Server is shutting down for maintenance.",
      reconnectAfterMs: 5000
    });
  }

  // 5. Close SSE connections
  await sseTransport.close();

  // 6. Close Redis and database connections
  await redis.quit();
  await db.end();

  logger.info("Graceful shutdown complete");
  process.exit(0);
});
```

---

## 8. MCP Server Implementation — Core Structure

### 8.1 Server Initialisation

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";

const server = new McpServer({
  name: "vapt-orchestration-server",
  version: "1.0.0",
  capabilities: {
    tools: {},
    resources: { subscribe: true }
  }
});

// ── Register Tools ──
server.tool(
  "start_burp_scan",
  "Launch a Burp Suite DAST scan against a web target",
  START_BURP_SCAN_SCHEMA,
  async (params, extra) => handleStartBurpScan(params, extra)
);

server.tool(
  "start_tenable_scan",
  "Launch a Tenable.io infrastructure vulnerability scan",
  START_TENABLE_SCAN_SCHEMA,
  async (params, extra) => handleStartTenableScan(params, extra)
);

server.tool(
  "start_fortify_scan",
  "Launch a Fortify SAST/SCA code scan",
  START_FORTIFY_SCAN_SCHEMA,
  async (params, extra) => handleStartFortifyScan(params, extra)
);

server.tool(
  "start_mobile_scan",
  "Launch a MobSF mobile security scan",
  START_MOBILE_SCAN_SCHEMA,
  async (params, extra) => handleStartMobileScan(params, extra)
);

server.tool(
  "get_scan_status",
  "Get current scan status and progress",
  GET_SCAN_STATUS_SCHEMA,
  async (params, extra) => handleGetScanStatus(params, extra)
);

server.tool(
  "fetch_scan_results",
  "Retrieve normalised findings from a completed scan",
  FETCH_SCAN_RESULTS_SCHEMA,
  async (params, extra) => handleFetchScanResults(params, extra)
);

server.tool(
  "assign_analyst",
  "Assign analyst to engagement or findings",
  ASSIGN_ANALYST_SCHEMA,
  async (params, extra) => handleAssignAnalyst(params, extra)
);

server.tool(
  "generate_report",
  "Generate a VAPT report",
  GENERATE_REPORT_SCHEMA,
  async (params, extra) => handleGenerateReport(params, extra)
);

server.tool(
  "publish_report",
  "Approve and deliver a report",
  PUBLISH_REPORT_SCHEMA,
  async (params, extra) => handlePublishReport(params, extra)
);

// ── Register Resources ──
server.resource(
  "engagement_scope",
  new ResourceTemplate("vapt://engagements/{engagement_id}/scope", { list: undefined }),
  async (uri, params) => readEngagementScope(params.engagement_id)
);

server.resource(
  "targets",
  new ResourceTemplate("vapt://engagements/{engagement_id}/targets", { list: undefined }),
  async (uri, params) => readTargets(params.engagement_id)
);

server.resource(
  "credential_profiles",
  new ResourceTemplate("vapt://engagements/{engagement_id}/credentials", { list: undefined }),
  async (uri, params) => readCredentialProfiles(params.engagement_id)
);

server.resource(
  "scan_status",
  new ResourceTemplate("vapt://scans/{scan_id}/status", { list: undefined }),
  async (uri, params) => readScanStatus(params.scan_id)
);

server.resource(
  "findings_summary",
  new ResourceTemplate("vapt://engagements/{engagement_id}/findings/summary", { list: undefined }),
  async (uri, params) => readFindingsSummary(params.engagement_id)
);

// ── Start Server ──
const transport = new SSEServerTransport("/mcp/sse", response);
await server.connect(transport);
```

---

## 9. Error Handling Reference

| Error Code | Constant | Trigger |
|---|---|---|
| -32600 | `INVALID_REQUEST` | Malformed JSON-RPC |
| -32601 | `METHOD_NOT_FOUND` | Unknown tool name |
| -32602 | `INVALID_PARAMS` | Validation failure (bad UUID, scope violation, wrong state) |
| -32603 | `INTERNAL_ERROR` | Platform service unavailable, Temporal failure |
| -32000 | `AUTHENTICATION_REQUIRED` | Missing or expired JWT |
| -32001 | `PERMISSION_DENIED` | Role lacks required permission |
| -32002 | `RATE_LIMITED` | Tenant or role rate limit exceeded |
| -32003 | `RESOURCE_EXHAUSTED` | Concurrent scan limit, storage quota exceeded |
| -32004 | `TENANT_SUSPENDED` | Customer account deactivated |

### Error Response Format

```json
{
  "jsonrpc": "2.0",
  "id": "req-010",
  "error": {
    "code": -32001,
    "message": "Permission denied: role 'viewer' cannot invoke 'start_burp_scan'. Required permission: 'scan:create'.",
    "data": {
      "required_permission": "scan:create",
      "user_role": "viewer",
      "tool": "start_burp_scan"
    }
  }
}
```

---

## 10. Observability

### 10.1 Key Metrics (Prometheus)

```
# Tool call latency by tool name
mcp_tool_call_duration_seconds{tool="start_burp_scan", status="success"}

# Tool call count by tool and outcome
mcp_tool_calls_total{tool="start_burp_scan", status="success|error"}

# Resource read latency
mcp_resource_read_duration_seconds{resource="engagement_scope"}

# Active SSE connections
mcp_sse_connections_active{tenant_id="..."}

# Kafka consumer lag
mcp_kafka_consumer_lag{topic="scan.completed", partition="0"}

# Rate limit rejections
mcp_rate_limit_rejections_total{tenant_id="...", tool="start_burp_scan"}

# Authentication failures
mcp_auth_failures_total{reason="expired_token|invalid_signature|missing_token"}
```

### 10.2 Distributed Tracing

Every MCP tool call generates a trace propagated through all downstream service calls:

```
Trace: mcp-tool-call-start_burp_scan
  └─ Span: jwt-validation (2ms)
  └─ Span: rbac-check (1ms)
  └─ Span: engagement-service.get (15ms)
  └─ Span: asset-service.get-target (12ms)
  └─ Span: engagement-service.check-scope (8ms)
  └─ Span: scan-service.create-job (25ms)
  └─ Span: kafka.publish-scan-requested (5ms)
  └─ Span: temporal.start-workflow (30ms)
  └─ Span: scan-service.update-job (10ms)
  └─ Span: mcp.notify-resource-changed (3ms)
  Total: 111ms
```
