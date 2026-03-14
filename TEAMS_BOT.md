# Microsoft Teams Bot — AI-Driven VAPT Platform

## Conversational Interface for Cybersecurity Analysts via Teams + MCP

---

## 1. Teams Bot Architecture

```
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                 MICROSOFT TEAMS ENVIRONMENT                                   ║
║                                                                                                ║
║  ┌──────────────────────────────────────────────────────────────────────────────────────────┐  ║
║  │                            TEAMS CHANNELS & CHATS                                        │  ║
║  │                                                                                          │  ║
║  │  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────────────┐   │  ║
║  │  │ #vapt-operations     │  │ #acme-engagement     │  │ Direct Chat with @vapt-bot   │   │  ║
║  │  │ (MSSP internal)      │  │ (per-customer)       │  │ (1:1 analyst workflow)       │   │  ║
║  │  │                      │  │                      │  │                              │   │  ║
║  │  │ • All critical alerts│  │ • Engagement updates │  │ • Sensitive queries          │   │  ║
║  │  │ • SLA breach alerts  │  │ • Scan completions   │  │ • Credential operations      │   │  ║
║  │  │ • Team assignments   │  │ • Report delivery    │  │ • Approval workflows         │   │  ║
║  │  └──────────┬───────────┘  └──────────┬───────────┘  └──────────────┬───────────────┘   │  ║
║  │             │ Bot Framework Activity   │ Bot Framework Activity     │                    │  ║
║  └─────────────┼──────────────────────────┼───────────────────────────┼────────────────────┘  ║
║                │                          │                           │                       ║
╚════════════════╬══════════════════════════╬═══════════════════════════╬═══════════════════════╝
                 │          HTTPS/TLS 1.3   │                           │
                 ▼                          ▼                           ▼
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                           AZURE BOT SERVICE (Bot Framework)                                   ║
║                           ──────────────────────────────────                                  ║
║                           • Message routing                                                   ║
║                           • Authentication (Azure AD)                                         ║
║                           • Activity delivery                                                 ║
╚════════════════════════════════════════════════════╦══════════════════════════════════════════╝
                                                     │
                                                     ▼ HTTPS POST /api/messages
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                             VAPT TEAMS BOT SERVICE                                            ║
║                             (Node.js 22 · Bot Framework SDK v4 · TypeScript 5.5)              ║
║                                                                                                ║
║  ┌─────────────────────────────────────────────────────────────────────────────────────────┐   ║
║  │                              INBOUND PIPELINE                                           │   ║
║  │                                                                                         │   ║
║  │  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  ┌───────────────────┐  │   ║
║  │  │ Bot Framework   │  │ Identity         │  │ Command        │  │ Confirmation      │  │   ║
║  │  │ Adapter         │  │ Resolution       │  │ Parser / NLU   │  │ Guard             │  │   ║
║  │  │                 │  │                  │  │                │  │                   │  │   ║
║  │  │ • Deserialize   │→│ • Azure AD →     │→│ • Regex match  │→│ • Destructive     │  │   ║
║  │  │   Activity      │  │   Platform user  │  │ • Intent       │  │   actions need    │  │   ║
║  │  │ • Validate      │  │ • Resolve tenant │  │   classification│ │   explicit "yes"  │  │   ║
║  │  │   Bot token     │  │ • Check MFA      │  │ • Entity       │  │ • Rate-limit      │  │   ║
║  │  │ • Rate limit    │  │ • Load RBAC role │  │   extraction   │  │   enforcement     │  │   ║
║  │  └─────────────────┘  └──────────────────┘  └────────────────┘  └───────────────────┘  │   ║
║  └─────────────────────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                                ║
║  ┌─────────────────────────────────────────────────────────────────────────────────────────┐   ║
║  │                              COMMAND HANDLERS                                           │   ║
║  │                                                                                         │   ║
║  │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐               │   ║
║  │  │ ScanHandler   │ │ TargetHandler │ │ ResultHandler │ │ AssignHandler │               │   ║
║  │  │               │ │               │ │               │ │               │               │   ║
║  │  │ start_scan    │ │ show_targets  │ │ fetch_results │ │ assign_analyst│               │   ║
║  │  │ scan_status   │ │ show_scope    │ │ show_findings │ │ assign_review │               │   ║
║  │  │ cancel_scan   │ │ show_creds    │ │ finding_detail│ │ approve       │               │   ║
║  │  └───────┬───────┘ └───────┬───────┘ └───────┬───────┘ └───────┬───────┘               │   ║
║  │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                                 │   ║
║  │  │ ReportHandler │ │ StatusHandler │ │ HelpHandler   │                                 │   ║
║  │  │               │ │               │ │               │                                 │   ║
║  │  │ generate_rpt  │ │ engagement    │ │ help          │                                 │   ║
║  │  │ publish_rpt   │ │ dashboard     │ │ command list  │                                 │   ║
║  │  │ report_status │ │ subscribe     │ │ usage guide   │                                 │   ║
║  │  └───────┬───────┘ └───────┬───────┘ └───────────────┘                                 │   ║
║  └──────────┼─────────────────┼──────────────────────────────────────────────────────────────┘  ║
║             │                 │                                                                 ║
║  ┌──────────┼─────────────────┼──────────────────────────────────────────────────────────────┐  ║
║  │          ▼                 ▼                                                               │  ║
║  │  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │  ║
║  │  │                         MCP CLIENT ADAPTER                                          │  │  ║
║  │  │                                                                                     │  │  ║
║  │  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────────────┐  │  │  ║
║  │  │  │ Tool Invoker     │  │ Resource Reader  │  │ Subscription Manager            │  │  │  ║
║  │  │  │                  │  │                  │  │                                  │  │  │  ║
║  │  │  │ tools/call       │  │ resources/read   │  │ resources/subscribe              │  │  │  ║
║  │  │  │ → JSON-RPC 2.0  │  │ → JSON-RPC 2.0  │  │ → SSE event stream              │  │  │  ║
║  │  │  └──────────────────┘  └──────────────────┘  └──────────────────────────────────┘  │  │  ║
║  │  │                                                                                     │  │  ║
║  │  │  Connection: SSE (Streamable HTTP) to MCP Server on port 3100                      │  │  ║
║  │  │  Auth: Service-account JWT with per-user impersonation (X-On-Behalf-Of header)     │  │  ║
║  │  └─────────────────────────────────────────────────────────────────────────────────────┘  │  ║
║  │                                                                                           │  ║
║  │  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │  ║
║  │  │                         OUTBOUND PIPELINE                                           │  │  ║
║  │  │                                                                                     │  │  ║
║  │  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────────────┐  │  │  ║
║  │  │  │ Adaptive Card    │  │ Conversation     │  │ Proactive Message               │  │  │  ║
║  │  │  │ Renderer         │  │ State Manager    │  │ Engine (Kafka consumer)          │  │  │  ║
║  │  │  │                  │  │                  │  │                                  │  │  │  ║
║  │  │  │ • Finding cards  │  │ • Session state  │  │ • scan.completed → card         │  │  │  ║
║  │  │  │ • Scan status    │  │ • Dialog stacks  │  │ • finding.normalized → alert    │  │  │  ║
║  │  │  │ • Report preview │  │ • Confirmation   │  │ • sla.breach → escalation       │  │  │  ║
║  │  │  │ • Approval forms │  │   pending states │  │ • report.generated → download   │  │  │  ║
║  │  │  └──────────────────┘  └──────────────────┘  └──────────────────────────────────┘  │  │  ║
║  │  └─────────────────────────────────────────────────────────────────────────────────────┘  │  ║
║  └───────────────────────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                                ║
║  ┌─────────────────────────────────────────────────────────────────────────────────────────┐   ║
║  │                              DATA STORES                                                │   ║
║  │                                                                                         │   ║
║  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────────────────┐  │   ║
║  │  │ PostgreSQL 16    │  │ Redis 7          │  │ Azure Blob (Conversation logs)      │  │   ║
║  │  │                  │  │                  │  │                                      │  │   ║
║  │  │ • teams_users    │  │ • Session state  │  │ • Audit trail of all bot commands   │  │   ║
║  │  │ • subscriptions  │  │ • Rate counters  │  │ • Compliance-grade retention        │  │   ║
║  │  │ • conversations  │  │ • MCP conn pool  │  │ • 7-year retention policy           │  │   ║
║  │  │ • audit_log      │  │ • Card cache     │  │                                      │  │   ║
║  │  └──────────────────┘  └──────────────────┘  └──────────────────────────────────────┘  │   ║
║  └─────────────────────────────────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
          │                                                          ▲
          │ SSE / Streamable HTTP                                    │ Kafka Consumer
          ▼                                                          │
╔═══════════════════════╗                               ╔═══════════════════════════╗
║  MCP ORCHESTRATION    ║                               ║  KAFKA EVENT BUS          ║
║  SERVER (Port 3100)   ║                               ║                           ║
║                       ║                               ║  scan.completed           ║
║  • 9 MCP Tools        ║                               ║  finding.normalized       ║
║  • 5 MCP Resources    ║                               ║  sla.breach               ║
║  • JWT auth           ║                               ║  report.generated         ║
║  • Tenant isolation   ║                               ║  notification.dispatch    ║
╚═══════════════════════╝                               ╚═══════════════════════════╝
```

---

## 2. Security Model

### 2.1 Identity Chain: Teams User → Platform User → Tenant

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│                              IDENTITY RESOLUTION CHAIN                                        │
│                                                                                               │
│  Step 1: Teams Authentication (handled by Azure Bot Service)                                 │
│  ──────────────────────────────────────────────────────────                                   │
│  • Azure Bot Service validates the Teams Activity token                                       │
│  • Extracts Azure AD Object ID (aadObjectId) from Activity.from                              │
│  • Guarantees the message came from a genuine Teams user                                      │
│                                                                                               │
│  Step 2: Platform Identity Resolution (handled by Teams Bot Service)                          │
│  ──────────────────────────────────────────────────────────────────                           │
│  • Bot looks up aadObjectId in teams_user_mappings table                                      │
│  • Resolves to platform user_id + tenant_id                                                   │
│  • If not found → prompt user to run /vapt link (one-time setup)                              │
│                                                                                               │
│  Step 3: RBAC Enforcement (before every MCP call)                                             │
│  ──────────────────────────────────────────────                                               │
│  • Load user's platform role from users table                                                 │
│  • Check command against permission matrix                                                    │
│  • Reject with "Permission denied" Adaptive Card if insufficient                              │
│                                                                                               │
│  Step 4: MCP Call with Impersonation                                                          │
│  ───────────────────────────────────                                                          │
│  • Bot uses its service-account JWT to connect to MCP Server                                  │
│  • Passes X-On-Behalf-Of: {user_id} and X-Tenant-ID: {tenant_id}                             │
│  • MCP Server enforces RLS + RBAC as if the user called directly                              │
│                                                                                               │
│  ┌──────────────┐     ┌──────────────────┐     ┌────────────────┐     ┌─────────────────┐    │
│  │ Teams User   │────►│ Azure AD         │────►│ teams_user_    │────►│ Platform users  │    │
│  │ (aadObjectId)│     │ (email, UPN)     │     │ mappings       │     │ (user_id,       │    │
│  │              │     │                  │     │ (aad_id →      │     │  tenant_id,     │    │
│  │              │     │                  │     │  user_id)      │     │  role)          │    │
│  └──────────────┘     └──────────────────┘     └────────────────┘     └─────────────────┘    │
│                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 User Linking (One-Time Setup)

```typescript
// When a user first interacts with the bot and no mapping exists:

interface TeamUserMapping {
    id: string;              // UUID
    aad_object_id: string;   // Azure AD Object ID from Teams
    aad_upn: string;         // user@company.com (User Principal Name)
    platform_user_id: string;// UUID → users.id
    tenant_id: string;       // UUID → customers.id
    platform_role: string;   // cached role for quick checks
    linked_at: Date;
    last_verified_at: Date;  // re-verified every 24h
    is_active: boolean;
}

// Linking flow:
// 1. User sends any command → bot detects no mapping
// 2. Bot presents Adaptive Card with "Link Your Account" button
// 3. Button opens OAuth2 flow → Keycloak login
// 4. On success → bot receives platform JWT
// 5. Extract sub, tenant_id, roles from JWT
// 6. INSERT teams_user_mappings record
// 7. User can now issue commands

async function resolveIdentity(activity: Activity): Promise<PlatformIdentity> {
    const aadObjectId = activity.from.aadObjectId;

    // Fast path: cached in Redis (5-minute TTL)
    const cached = await redis.get(`teams:identity:${aadObjectId}`);
    if (cached) return JSON.parse(cached);

    // DB lookup
    const mapping = await db.teamsUserMappings.findOne({
        where: { aad_object_id: aadObjectId, is_active: true }
    });

    if (!mapping) {
        throw new UnlinkedUserError(aadObjectId);
    }

    // Periodic re-verification (every 24h)
    if (hoursAgo(mapping.last_verified_at) > 24) {
        const platformUser = await platformApi.getUser(mapping.platform_user_id);
        if (!platformUser || !platformUser.is_active) {
            await db.teamsUserMappings.update(mapping.id, { is_active: false });
            throw new DeactivatedUserError(aadObjectId);
        }
        mapping.platform_role = platformUser.role;
        mapping.last_verified_at = new Date();
        await db.teamsUserMappings.save(mapping);
    }

    const identity: PlatformIdentity = {
        userId: mapping.platform_user_id,
        tenantId: mapping.tenant_id,
        role: mapping.platform_role,
        email: mapping.aad_upn,
        displayName: activity.from.name,
    };

    await redis.set(`teams:identity:${aadObjectId}`, JSON.stringify(identity), "EX", 300);
    return identity;
}
```

### 2.3 RBAC Enforcement per Command

```typescript
// Permission matrix: which platform roles can execute which bot commands

const COMMAND_PERMISSIONS: Record<string, {
    requiredPermissions: string[];
    allowedRoles: string[];
    sensitiveChannel: "any" | "direct_only";
    requiresConfirmation: boolean;
}> = {
    "start_scan": {
        requiredPermissions: ["scan:create"],
        allowedRoles: ["platform_admin", "lead_analyst", "analyst", "scanner_operator"],
        sensitiveChannel: "any",
        requiresConfirmation: true,
    },
    "show_targets": {
        requiredPermissions: ["engagement:read", "asset:read"],
        allowedRoles: ["platform_admin", "lead_analyst", "analyst", "scanner_operator"],
        sensitiveChannel: "any",
        requiresConfirmation: false,
    },
    "show_credentials": {
        requiredPermissions: ["credential:read"],
        allowedRoles: ["platform_admin", "lead_analyst", "analyst", "scanner_operator"],
        sensitiveChannel: "direct_only",  // Never show in group channels
        requiresConfirmation: false,
    },
    "fetch_results": {
        requiredPermissions: ["finding:read"],
        allowedRoles: ["platform_admin", "lead_analyst", "analyst", "scanner_operator", "customer_admin", "customer_user"],
        sensitiveChannel: "any",
        requiresConfirmation: false,
    },
    "assign_analyst": {
        requiredPermissions: ["engagement:assign"],
        allowedRoles: ["platform_admin", "lead_analyst"],
        sensitiveChannel: "any",
        requiresConfirmation: true,
    },
    "generate_report": {
        requiredPermissions: ["report:create"],
        allowedRoles: ["platform_admin", "lead_analyst", "analyst", "customer_admin"],
        sensitiveChannel: "any",
        requiresConfirmation: true,
    },
    "publish_report": {
        requiredPermissions: ["report:approve"],
        allowedRoles: ["platform_admin", "lead_analyst"],
        sensitiveChannel: "any",
        requiresConfirmation: true,
    },
    "scan_status": {
        requiredPermissions: ["scan:read"],
        allowedRoles: ["platform_admin", "lead_analyst", "analyst", "scanner_operator", "customer_admin", "customer_user", "viewer"],
        sensitiveChannel: "any",
        requiresConfirmation: false,
    },
    "findings_summary": {
        requiredPermissions: ["finding:read"],
        allowedRoles: ["platform_admin", "lead_analyst", "analyst", "scanner_operator", "customer_admin", "customer_user", "viewer"],
        sensitiveChannel: "any",
        requiresConfirmation: false,
    },
    "subscribe": {
        requiredPermissions: ["engagement:read"],
        allowedRoles: ["platform_admin", "lead_analyst", "analyst", "scanner_operator", "customer_admin", "customer_user"],
        sensitiveChannel: "any",
        requiresConfirmation: false,
    },
};

async function enforcePermissions(
    command: string,
    identity: PlatformIdentity,
    conversationType: "personal" | "groupChat" | "channel"
): Promise<void> {
    const config = COMMAND_PERMISSIONS[command];
    if (!config) throw new UnknownCommandError(command);

    // Role check
    if (!config.allowedRoles.includes(identity.role)) {
        throw new PermissionDeniedError(
            `Your role '${identity.role}' cannot execute '${command}'. ` +
            `Required: ${config.allowedRoles.join(", ")}.`
        );
    }

    // Sensitive channel check
    if (config.sensitiveChannel === "direct_only" && conversationType !== "personal") {
        throw new ChannelRestrictionError(
            `'${command}' contains sensitive data and can only be used in a direct chat ` +
            `with the bot. Please DM @vapt-bot instead.`
        );
    }
}
```

### 2.4 Audit Logging

Every bot interaction is logged for compliance:

```typescript
interface BotAuditEntry {
    id: string;
    timestamp: Date;
    // Teams context
    teams_user_id: string;
    teams_channel_id: string | null;
    conversation_type: "personal" | "groupChat" | "channel";
    // Platform context
    platform_user_id: string;
    tenant_id: string;
    role: string;
    // Command
    raw_input: string;
    parsed_command: string;
    parsed_args: Record<string, any>;
    // Execution
    mcp_tool_called: string | null;
    mcp_resource_read: string | null;
    execution_time_ms: number;
    // Outcome
    status: "success" | "permission_denied" | "validation_error" | "mcp_error" | "internal_error";
    error_message: string | null;
    // Redaction
    contains_sensitive: boolean;   // if true, raw_input is redacted
}

// All entries written to PostgreSQL + Azure Blob (7-year retention)
```

### 2.5 Rate Limiting

```typescript
// Per-user rate limits (enforced via Redis sliding window)
const RATE_LIMITS = {
    commands_per_minute:        10,     // any command
    scan_launches_per_hour:     5,      // start_scan specifically
    report_generations_per_hour: 3,     // generate_report
    api_calls_per_minute:       30,     // total MCP calls
};

async function checkRateLimit(userId: string, action: string): Promise<void> {
    const key = `ratelimit:${userId}:${action}`;
    const window = RATE_WINDOWS[action];  // 60s or 3600s
    const limit = RATE_LIMITS[action];

    const current = await redis.incr(key);
    if (current === 1) {
        await redis.expire(key, window);
    }

    if (current > limit) {
        throw new RateLimitError(
            `Rate limit exceeded: ${limit} ${action} per ${window}s. ` +
            `Try again in ${await redis.ttl(key)} seconds.`
        );
    }
}
```

---

## 3. Command Parsing & NLU Engine

### 3.1 Parser Architecture

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│                              COMMAND PARSING PIPELINE                                         │
│                                                                                               │
│  User Input: "Start scan for engagement 102"                                                 │
│       │                                                                                       │
│       ▼                                                                                       │
│  ┌─────────────────────────────────────────────┐                                             │
│  │  Stage 1: PREPROCESSOR                       │                                             │
│  │                                               │                                             │
│  │  • Strip @vapt-bot mention prefix             │                                             │
│  │  • Normalise whitespace                       │                                             │
│  │  • Convert to lowercase for matching          │                                             │
│  │  • Preserve original case for display         │                                             │
│  │                                               │                                             │
│  │  Output: "start scan for engagement 102"     │                                             │
│  └──────────────────────┬──────────────────────┘                                             │
│                         │                                                                     │
│                         ▼                                                                     │
│  ┌─────────────────────────────────────────────┐                                             │
│  │  Stage 2: REGEX PATTERN MATCHER (fast path) │                                             │
│  │                                               │                                             │
│  │  Try deterministic regex patterns first:      │                                             │
│  │                                               │                                             │
│  │  /^start\s+scan\s+(?:for\s+)?engagement      │ → intent: start_scan                       │
│  │   \s+(?<ref>\S+)/i                            │   entity: engagement_ref = "102"            │
│  │                                               │                                             │
│  │  /^show\s+targets\s+(?:for\s+)?engagement     │ → intent: show_targets                     │
│  │   \s+(?<ref>\S+)/i                            │   entity: engagement_ref = "102"            │
│  │                                               │                                             │
│  │  /^(?:fetch|show|get)\s+(?:burp\s+)?results   │ → intent: fetch_results                    │
│  │   (?:\s+(?:for\s+)?(?:scan\s+)?(?<id>\S+))?/i│   entity: scan_ref (optional)              │
│  │                                               │                                             │
│  │  /^assign\s+(?:manual\s+)?validation\s+to     │ → intent: assign_analyst                   │
│  │   \s+(?<analyst>\S+.*)/i                      │   entity: analyst_name                      │
│  │                                               │                                             │
│  │  /^generate\s+(?:draft\s+)?report             │ → intent: generate_report                  │
│  │   (?:\s+(?:for\s+)?engagement\s+(?<ref>\S+))? │   entity: engagement_ref (optional)         │
│  │   /i                                          │                                             │
│  │                                               │                                             │
│  │  If matched → skip NLU, proceed to handler   │                                             │
│  └──────────────────────┬──────────────────────┘                                             │
│                         │ No match                                                            │
│                         ▼                                                                     │
│  ┌─────────────────────────────────────────────┐                                             │
│  │  Stage 3: LLM INTENT CLASSIFIER (slow path) │                                             │
│  │                                               │                                             │
│  │  Claude API call with structured output:      │                                             │
│  │                                               │                                             │
│  │  System: "You are a command parser for a      │                                             │
│  │  cybersecurity VAPT platform. Classify user   │                                             │
│  │  input into an intent and extract entities.   │                                             │
│  │  Valid intents: start_scan, show_targets,     │                                             │
│  │  show_scope, fetch_results, scan_status,      │                                             │
│  │  assign_analyst, generate_report,             │                                             │
│  │  publish_report, findings_summary, subscribe, │                                             │
│  │  help, unknown."                              │                                             │
│  │                                               │                                             │
│  │  Output (tool_use / structured):              │                                             │
│  │  {                                            │                                             │
│  │    "intent": "start_scan",                    │                                             │
│  │    "confidence": 0.95,                        │                                             │
│  │    "entities": {                              │                                             │
│  │      "engagement_ref": "102",                 │                                             │
│  │      "scan_type": "all"                       │                                             │
│  │    },                                         │                                             │
│  │    "clarification_needed": false              │                                             │
│  │  }                                            │                                             │
│  │                                               │                                             │
│  │  If confidence < 0.7 → ask user to clarify   │                                             │
│  │  If intent = "unknown" → show help card      │                                             │
│  └──────────────────────┬──────────────────────┘                                             │
│                         │                                                                     │
│                         ▼                                                                     │
│  ┌─────────────────────────────────────────────┐                                             │
│  │  Stage 4: ENTITY RESOLVER                    │                                             │
│  │                                               │                                             │
│  │  Resolve human references to platform UUIDs:  │                                             │
│  │                                               │                                             │
│  │  "engagement 102"                             │                                             │
│  │    → query engagements WHERE                  │                                             │
│  │      reference_code LIKE '%102%'              │                                             │
│  │      AND tenant_id = current_tenant           │                                             │
│  │    → resolved: ENG-2026-0102                  │                                             │
│  │    → engagement_id: UUID                      │                                             │
│  │                                               │                                             │
│  │  "Jane" or "jane.doe"                         │                                             │
│  │    → query users WHERE                        │                                             │
│  │      (display_name ILIKE '%Jane%'             │                                             │
│  │       OR email ILIKE '%jane%')                │                                             │
│  │      AND tenant_id = current_tenant           │                                             │
│  │      AND role IN ('analyst', 'lead_analyst')  │                                             │
│  │    → If ambiguous → show disambiguation card  │                                             │
│  │                                               │                                             │
│  │  "latest burp scan" or "last scan"            │                                             │
│  │    → query scan_jobs WHERE                    │                                             │
│  │      engagement_id = context.engagement       │                                             │
│  │      AND scanner_engine = 'burp_suite'        │                                             │
│  │      ORDER BY created_at DESC LIMIT 1         │                                             │
│  │    → resolved: scan_job_id UUID               │                                             │
│  └──────────────────────┬──────────────────────┘                                             │
│                         │                                                                     │
│                         ▼                                                                     │
│  ┌─────────────────────────────────────────────┐                                             │
│  │  Stage 5: PARSED COMMAND                     │                                             │
│  │                                               │                                             │
│  │  ParsedCommand {                              │                                             │
│  │    intent: "start_scan",                      │                                             │
│  │    confidence: 1.0,     // regex = 1.0        │                                             │
│  │    source: "regex",     // or "llm"           │                                             │
│  │    entities: {                                │                                             │
│  │      engagement_id: "uuid-here",              │                                             │
│  │      engagement_ref: "ENG-2026-0102",         │                                             │
│  │      scan_type: "all",                        │                                             │
│  │    },                                         │                                             │
│  │    raw_input: "Start scan for engagement 102",│                                             │
│  │    requires_confirmation: true,               │                                             │
│  │  }                                            │                                             │
│  └─────────────────────────────────────────────┘                                             │
│                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Regex Pattern Registry

```typescript
interface CommandPattern {
    intent: string;
    patterns: RegExp[];
    entities: string[];        // named capture groups to extract
    examples: string[];        // for help text
}

const COMMAND_PATTERNS: CommandPattern[] = [
    // ── Scan Operations ──
    {
        intent: "start_scan",
        patterns: [
            /^(?:start|launch|run|begin|kick\s*off)\s+(?:a\s+)?(?:(?<type>burp|tenable|fortify|mobile|infra|dast|sast|sca|full)\s+)?scan(?:s)?\s+(?:for|on|against)\s+(?:engagement\s+)?(?<ref>\S+)/i,
            /^scan\s+(?:engagement\s+)?(?<ref>\S+)(?:\s+(?:with|using)\s+(?<type>burp|tenable|fortify|mobsf))?/i,
        ],
        entities: ["ref", "type"],
        examples: [
            "Start scan for engagement 102",
            "Launch burp scan for ENG-2026-0042",
            "Run full scan on engagement 102",
            "Scan engagement 102 with tenable",
        ],
    },
    {
        intent: "scan_status",
        patterns: [
            /^(?:show|get|check|what(?:'s|\s+is))\s+(?:the\s+)?(?:scan\s+)?status\s+(?:of|for)\s+(?:engagement\s+)?(?<ref>\S+)/i,
            /^(?:scan\s+)?status\s+(?:engagement\s+)?(?<ref>\S+)/i,
            /^(?:how(?:'s|\s+is))\s+(?:the\s+)?scan\s+(?:for\s+)?(?:engagement\s+)?(?<ref>\S+)\s*(?:going|doing|progressing)?/i,
        ],
        entities: ["ref"],
        examples: [
            "Show scan status for engagement 102",
            "How's the scan for engagement 102 going?",
        ],
    },

    // ── Target & Scope Queries ──
    {
        intent: "show_targets",
        patterns: [
            /^(?:show|list|get|display)\s+(?:the\s+)?targets?\s+(?:for|of|in)\s+(?:engagement\s+)?(?<ref>\S+)/i,
            /^(?:what(?:'s|\s+are))\s+(?:the\s+)?targets?\s+(?:for|in)\s+(?:engagement\s+)?(?<ref>\S+)/i,
        ],
        entities: ["ref"],
        examples: [
            "Show targets for engagement 102",
            "What are the targets in ENG-2026-0042?",
        ],
    },
    {
        intent: "show_scope",
        patterns: [
            /^(?:show|get|display)\s+(?:the\s+)?scope\s+(?:for|of)\s+(?:engagement\s+)?(?<ref>\S+)/i,
        ],
        entities: ["ref"],
        examples: ["Show scope for engagement 102"],
    },

    // ── Results & Findings ──
    {
        intent: "fetch_results",
        patterns: [
            /^(?:fetch|get|show|pull|retrieve)\s+(?:the\s+)?(?:(?<scanner>burp|tenable|fortify|mobile|mobsf)\s+)?results?\s*(?:(?:for|of|from)\s+(?:(?:scan|engagement)\s+)?(?<ref>\S+))?/i,
            /^(?:what\s+did)\s+(?:the\s+)?(?<scanner>burp|tenable|fortify)\s+(?:scan\s+)?find/i,
        ],
        entities: ["scanner", "ref"],
        examples: [
            "Fetch Burp results",
            "Get results for engagement 102",
            "Show tenable results for ENG-2026-0042",
            "What did the burp scan find?",
        ],
    },
    {
        intent: "findings_summary",
        patterns: [
            /^(?:show|get|display)\s+(?:the\s+)?findings?\s+(?:summary|overview|breakdown|stats)\s+(?:for|of)\s+(?:engagement\s+)?(?<ref>\S+)/i,
            /^(?:how\s+many)\s+(?:findings?|vulns?|vulnerabilities)\s+(?:in|for)\s+(?:engagement\s+)?(?<ref>\S+)/i,
        ],
        entities: ["ref"],
        examples: [
            "Show findings summary for engagement 102",
            "How many vulns in engagement 102?",
        ],
    },

    // ── Analyst Assignment ──
    {
        intent: "assign_analyst",
        patterns: [
            /^assign\s+(?:manual\s+)?(?:validation|triage|review|testing)\s+(?:to|for)\s+(?:analyst\s+)?(?<analyst>.+?)(?:\s+(?:for|on)\s+(?:engagement\s+)?(?<ref>\S+))?$/i,
            /^assign\s+(?<analyst>.+?)\s+(?:to|for)\s+(?:engagement\s+)?(?<ref>\S+)/i,
            /^(?<analyst>.+?)\s+(?:should|needs?\s+to|please)\s+(?:validate|triage|review)\s+(?:the\s+)?(?:findings?\s+)?(?:for\s+)?(?:engagement\s+)?(?<ref>\S+)/i,
        ],
        entities: ["analyst", "ref"],
        examples: [
            "Assign manual validation to analyst Jane",
            "Assign Jane Doe to engagement 102",
            "Jane should validate the findings for 102",
        ],
    },

    // ── Reports ──
    {
        intent: "generate_report",
        patterns: [
            /^(?:generate|create|build|make)\s+(?:a\s+)?(?:(?<type>draft|executive|full|technical|compliance|delta)\s+)?report\s*(?:(?:for|of)\s+(?:engagement\s+)?(?<ref>\S+))?/i,
            /^(?:draft|write)\s+(?:a\s+)?(?:(?<type>executive|full|technical|compliance)\s+)?report\s*(?:(?:for|of)\s+(?:engagement\s+)?(?<ref>\S+))?/i,
        ],
        entities: ["type", "ref"],
        examples: [
            "Generate draft report",
            "Create full technical report for engagement 102",
            "Draft executive report for ENG-2026-0042",
        ],
    },
    {
        intent: "publish_report",
        patterns: [
            /^(?:publish|deliver|send|approve)\s+(?:the\s+)?report\s+(?<report_ref>\S+)\s*(?:(?:to|via)\s+(?<method>email|portal|teams))?/i,
        ],
        entities: ["report_ref", "method"],
        examples: [
            "Publish report RPT-001 to email",
            "Deliver the report via portal",
        ],
    },

    // ── Subscriptions & Help ──
    {
        intent: "subscribe",
        patterns: [
            /^(?:subscribe|watch|follow|monitor)\s+(?:to\s+)?(?:engagement\s+)?(?<ref>\S+)/i,
        ],
        entities: ["ref"],
        examples: ["Subscribe to engagement 102"],
    },
    {
        intent: "unsubscribe",
        patterns: [
            /^(?:unsubscribe|unwatch|unfollow|stop\s+watching)\s+(?:from\s+)?(?:engagement\s+)?(?<ref>\S+)/i,
        ],
        entities: ["ref"],
        examples: ["Unsubscribe from engagement 102"],
    },
    {
        intent: "help",
        patterns: [
            /^(?:help|commands|usage|what\s+can\s+you\s+do|\?)/i,
        ],
        entities: [],
        examples: ["help", "What can you do?"],
    },
];
```

### 3.3 LLM Intent Classifier (Fallback)

```typescript
async function classifyWithLLM(input: string): Promise<ParsedCommand> {
    const response = await anthropic.messages.create({
        model: "claude-sonnet-4-6",
        max_tokens: 256,
        system: `You are a command parser for a cybersecurity VAPT (Vulnerability Assessment & Penetration Testing) platform bot.
Classify the user's natural language input into a structured command.

Valid intents:
- start_scan: Launch vulnerability scans
- scan_status: Check scan progress
- show_targets: List scan targets for an engagement
- show_scope: Show engagement scope definition
- fetch_results: Get scan results/findings
- findings_summary: Get aggregated finding statistics
- assign_analyst: Assign an analyst to findings/engagement
- generate_report: Create a VAPT report
- publish_report: Approve and deliver a report
- subscribe: Subscribe to engagement notifications
- unsubscribe: Unsubscribe from notifications
- help: Show help information
- unknown: Cannot determine intent

Extract entities:
- engagement_ref: engagement ID or reference code (e.g., "102", "ENG-2026-0042")
- scan_type: scanner type (burp, tenable, fortify, mobile, all)
- scanner: specific scanner name
- analyst: analyst name or identifier
- report_type: report type (draft, executive, full, technical, compliance, delta)
- severity: severity filter (critical, high, medium, low)
- report_ref: report ID or reference

Respond with ONLY valid JSON.`,
        messages: [{ role: "user", content: input }],
        tools: [{
            name: "parse_command",
            description: "Parse a natural language command",
            input_schema: {
                type: "object",
                properties: {
                    intent: { type: "string", enum: [
                        "start_scan", "scan_status", "show_targets", "show_scope",
                        "fetch_results", "findings_summary", "assign_analyst",
                        "generate_report", "publish_report", "subscribe",
                        "unsubscribe", "help", "unknown"
                    ]},
                    confidence: { type: "number", minimum: 0, maximum: 1 },
                    entities: { type: "object" },
                    clarification_needed: { type: "boolean" },
                    clarification_question: { type: "string" }
                },
                required: ["intent", "confidence", "entities", "clarification_needed"]
            }
        }],
        tool_choice: { type: "tool", name: "parse_command" }
    });

    const toolUse = response.content.find(c => c.type === "tool_use");
    const parsed = toolUse.input as LLMParseResult;

    if (parsed.confidence < 0.7 || parsed.clarification_needed) {
        return {
            intent: "clarification_needed",
            confidence: parsed.confidence,
            source: "llm",
            clarificationQuestion: parsed.clarification_question
                || "I'm not sure what you mean. Could you rephrase? Type 'help' for available commands.",
            entities: parsed.entities,
            rawInput: input,
            requiresConfirmation: false,
        };
    }

    return {
        intent: parsed.intent,
        confidence: parsed.confidence,
        source: "llm",
        entities: parsed.entities,
        rawInput: input,
        requiresConfirmation: COMMAND_PERMISSIONS[parsed.intent]?.requiresConfirmation ?? false,
    };
}
```

---

## 5. Command Handlers & MCP Communication

### 5.1 MCP Client Adapter

The MCP Client Adapter manages the connection to the VAPT MCP Server, providing typed wrappers around MCP tool calls and resource reads.

```
┌─────────────────────────────────────────────────────────────────────┐
│                      MCP Client Adapter                             │
│                                                                     │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────────────┐  │
│  │ Connection   │  │ Request       │  │ Response                │  │
│  │ Manager      │  │ Builder       │  │ Deserialiser            │  │
│  │              │  │               │  │                         │  │
│  │ - SSE pool   │  │ - JSON-RPC    │  │ - Type-safe results    │  │
│  │ - Reconnect  │  │   2.0 framing │  │ - Error mapping        │  │
│  │ - Health     │  │ - Auth header │  │ - Streaming support    │  │
│  │   checks     │  │ - Request ID  │  │ - Progress extraction  │  │
│  └──────────────┘  └───────────────┘  └─────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Tool / Resource Registry                   │   │
│  │                                                              │   │
│  │  Tools:     start_burp_scan, start_tenable_scan,             │   │
│  │             start_fortify_scan, start_mobile_scan,           │   │
│  │             get_scan_status, fetch_scan_results,             │   │
│  │             assign_analyst, generate_report, publish_report  │   │
│  │                                                              │   │
│  │  Resources: engagement_scope, targets, credential_profiles,  │   │
│  │             scan_status, findings_summary                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

```typescript
// src/mcp/mcp-client-adapter.ts

import { EventSource } from "eventsource";

interface MCPToolCall {
    jsonrpc: "2.0";
    id: string;
    method: "tools/call";
    params: {
        name: string;
        arguments: Record<string, unknown>;
    };
}

interface MCPResourceRead {
    jsonrpc: "2.0";
    id: string;
    method: "resources/read";
    params: {
        uri: string;
    };
}

interface MCPResponse<T = unknown> {
    jsonrpc: "2.0";
    id: string;
    result?: T;
    error?: {
        code: number;
        message: string;
        data?: unknown;
    };
}

interface MCPClientConfig {
    serverUrl: string;          // e.g. https://mcp.vapt-platform.internal
    sseEndpoint: string;        // /sse
    messagesEndpoint: string;   // /messages
    healthEndpoint: string;     // /health
    reconnectIntervalMs: number;
    maxReconnectAttempts: number;
    requestTimeoutMs: number;
}

class MCPClientAdapter {
    private config: MCPClientConfig;
    private eventSource: EventSource | null = null;
    private pendingRequests: Map<string, {
        resolve: (value: MCPResponse) => void;
        reject: (error: Error) => void;
        timer: NodeJS.Timeout;
    }> = new Map();
    private messagesUrl: string | null = null;
    private reconnectAttempts = 0;
    private logger: Logger;

    constructor(config: MCPClientConfig, logger: Logger) {
        this.config = config;
        this.logger = logger;
    }

    // ── Connection Lifecycle ──────────────────────────────────────

    async connect(jwtToken: string): Promise<void> {
        return new Promise((resolve, reject) => {
            const sseUrl = `${this.config.serverUrl}${this.config.sseEndpoint}`;

            this.eventSource = new EventSource(sseUrl, {
                headers: { Authorization: `Bearer ${jwtToken}` },
            });

            this.eventSource.addEventListener("endpoint", (event) => {
                // Server sends the messages endpoint URL
                this.messagesUrl = `${this.config.serverUrl}${event.data}`;
                this.reconnectAttempts = 0;
                this.logger.info("MCP SSE connected", { messagesUrl: this.messagesUrl });
                resolve();
            });

            this.eventSource.addEventListener("message", (event) => {
                const response: MCPResponse = JSON.parse(event.data);
                const pending = this.pendingRequests.get(response.id);
                if (pending) {
                    clearTimeout(pending.timer);
                    this.pendingRequests.delete(response.id);
                    pending.resolve(response);
                }
            });

            this.eventSource.onerror = (err) => {
                this.logger.error("MCP SSE error", { error: err });
                if (this.reconnectAttempts < this.config.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    const backoff = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
                    setTimeout(() => this.connect(jwtToken), backoff);
                } else {
                    reject(new Error("MCP SSE connection failed after max retries"));
                }
            };
        });
    }

    disconnect(): void {
        this.eventSource?.close();
        this.eventSource = null;
        for (const [id, pending] of this.pendingRequests) {
            clearTimeout(pending.timer);
            pending.reject(new Error("Connection closed"));
        }
        this.pendingRequests.clear();
    }

    // ── Core Request Methods ──────────────────────────────────────

    private async sendRequest<T>(request: MCPToolCall | MCPResourceRead): Promise<T> {
        if (!this.messagesUrl) {
            throw new Error("MCP client not connected");
        }

        return new Promise<T>((resolve, reject) => {
            const timer = setTimeout(() => {
                this.pendingRequests.delete(request.id);
                reject(new Error(`MCP request timeout: ${request.id}`));
            }, this.config.requestTimeoutMs);

            this.pendingRequests.set(request.id, {
                resolve: (response: MCPResponse) => {
                    if (response.error) {
                        reject(new MCPError(response.error.code, response.error.message, response.error.data));
                    } else {
                        resolve(response.result as T);
                    }
                },
                reject,
                timer,
            });

            // POST the JSON-RPC request to the messages endpoint
            fetch(this.messagesUrl!, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(request),
            }).catch((err) => {
                clearTimeout(timer);
                this.pendingRequests.delete(request.id);
                reject(err);
            });
        });
    }

    async callTool<T>(name: string, args: Record<string, unknown>): Promise<T> {
        const request: MCPToolCall = {
            jsonrpc: "2.0",
            id: `tool-${name}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
            method: "tools/call",
            params: { name, arguments: args },
        };
        this.logger.info("MCP tool call", { tool: name, requestId: request.id });
        return this.sendRequest<T>(request);
    }

    async readResource<T>(uri: string): Promise<T> {
        const request: MCPResourceRead = {
            jsonrpc: "2.0",
            id: `res-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
            method: "resources/read",
            params: { uri },
        };
        this.logger.info("MCP resource read", { uri, requestId: request.id });
        return this.sendRequest<T>(request);
    }
}
```

### 5.2 MCP Error Handling

```typescript
// src/mcp/mcp-errors.ts

class MCPError extends Error {
    constructor(
        public readonly code: number,
        message: string,
        public readonly data?: unknown,
    ) {
        super(message);
        this.name = "MCPError";
    }
}

// Map MCP error codes to user-friendly Teams messages
const MCP_ERROR_MAP: Record<number, { title: string; message: string; retryable: boolean }> = {
    [-32600]: { title: "Invalid Request",     message: "The request was malformed. Please try again.",                retryable: false },
    [-32601]: { title: "Unknown Tool",        message: "That operation is not available.",                            retryable: false },
    [-32602]: { title: "Invalid Parameters",  message: "Some parameters were invalid. Please check and retry.",      retryable: false },
    [-32603]: { title: "Internal Error",      message: "The server encountered an error. Our team has been notified.", retryable: true },
    [4001]:   { title: "Authentication Error", message: "Your session has expired. Please re-authenticate.",         retryable: false },
    [4003]:   { title: "Permission Denied",   message: "You don't have permission for this operation.",              retryable: false },
    [4004]:   { title: "Not Found",           message: "The requested resource was not found.",                      retryable: false },
    [4009]:   { title: "Conflict",            message: "A conflicting operation is already in progress.",            retryable: true },
    [4029]:   { title: "Rate Limited",        message: "Too many requests. Please wait a moment and try again.",     retryable: true },
    [5003]:   { title: "Scanner Unavailable", message: "The scanner is temporarily unavailable. Retrying...",        retryable: true },
};

function mapMCPErrorToCard(error: MCPError): Partial<AdaptiveCard> {
    const mapped = MCP_ERROR_MAP[error.code] || {
        title: "Error",
        message: error.message,
        retryable: false,
    };

    return {
        type: "AdaptiveCard",
        body: [
            {
                type: "TextBlock",
                text: `⚠️ ${mapped.title}`,
                weight: "Bolder",
                color: "Attention",
            },
            {
                type: "TextBlock",
                text: mapped.message,
                wrap: true,
            },
        ],
        actions: mapped.retryable
            ? [{ type: "Action.Submit", title: "Retry", data: { action: "retry" } }]
            : [],
    };
}
```

### 5.3 Command Handler Interface

```typescript
// src/handlers/base-handler.ts

interface CommandContext {
    turnContext: TurnContext;
    parsedCommand: ParsedCommand;
    user: PlatformUser;
    mcpClient: MCPClientAdapter;
    conversationState: ConversationState;
    logger: Logger;
}

interface CommandResult {
    card?: AdaptiveCard;
    text?: string;
    suggestions?: string[];
    subscribeToUpdates?: {
        topic: string;
        key: string;
        conversationRef: Partial<ConversationReference>;
    };
}

interface CommandHandler {
    intent: string;
    handle(ctx: CommandContext): Promise<CommandResult>;
    validate(ctx: CommandContext): Promise<ValidationResult>;
}

interface ValidationResult {
    valid: boolean;
    missingEntities?: string[];
    clarificationPrompt?: string;
}

abstract class BaseCommandHandler implements CommandHandler {
    abstract intent: string;

    async handle(ctx: CommandContext): Promise<CommandResult> {
        // 1. Validate entities
        const validation = await this.validate(ctx);
        if (!validation.valid) {
            return {
                text: validation.clarificationPrompt,
                suggestions: this.getSuggestions(ctx),
            };
        }

        // 2. Show typing indicator
        await ctx.turnContext.sendActivity({ type: "typing" });

        // 3. Execute handler logic
        try {
            return await this.execute(ctx);
        } catch (error) {
            if (error instanceof MCPError) {
                return { card: mapMCPErrorToCard(error) as AdaptiveCard };
            }
            ctx.logger.error(`Handler error: ${this.intent}`, { error });
            throw error;
        }
    }

    abstract execute(ctx: CommandContext): Promise<CommandResult>;
    abstract validate(ctx: CommandContext): Promise<ValidationResult>;
    protected abstract getSuggestions(ctx: CommandContext): string[];
}
```

### 5.4 Start Scan Handler

```typescript
// src/handlers/start-scan-handler.ts

class StartScanHandler extends BaseCommandHandler {
    intent = "start_scan";

    async validate(ctx: CommandContext): Promise<ValidationResult> {
        const { entities } = ctx.parsedCommand;

        if (!entities.engagement_id) {
            return {
                valid: false,
                missingEntities: ["engagement_id"],
                clarificationPrompt: "Which engagement should I start the scan for? "
                    + "Please provide the engagement ID (e.g., 'Start scan for engagement 102').",
            };
        }

        if (!entities.scan_type) {
            return {
                valid: false,
                missingEntities: ["scan_type"],
                clarificationPrompt: "What type of scan would you like to run?\n\n"
                    + "• **web** — Web application scan (Burp Suite DAST)\n"
                    + "• **api** — API scan (Burp Suite API)\n"
                    + "• **infra** — Infrastructure scan (Tenable)\n"
                    + "• **code** — Source code scan (Fortify SAST)\n"
                    + "• **mobile** — Mobile app scan (MobSF)\n"
                    + "• **all** — Full engagement scan (all applicable types)",
            };
        }

        return { valid: true };
    }

    async execute(ctx: CommandContext): Promise<CommandResult> {
        const { entities } = ctx.parsedCommand;
        const engagementId = entities.engagement_id as number;
        const scanType = entities.scan_type as string;

        // Step 1: Read engagement scope from MCP resource
        const scope = await ctx.mcpClient.readResource<EngagementScope>(
            `vapt://engagements/${engagementId}/scope`
        );

        // Step 2: Read targets for the engagement
        const targets = await ctx.mcpClient.readResource<TargetList>(
            `vapt://engagements/${engagementId}/targets`
        );

        if (targets.items.length === 0) {
            return {
                text: `No targets defined for engagement ${engagementId}. `
                    + "Please add targets before starting a scan.",
                suggestions: [`Show targets for engagement ${engagementId}`],
            };
        }

        // Step 3: Determine which MCP tool(s) to call
        const scanTools = this.resolveScanTools(scanType, targets.items);

        // Step 4: If confirmation required, show confirmation card
        if (ctx.parsedCommand.requiresConfirmation) {
            return {
                card: this.buildConfirmationCard(engagementId, scanType, scope, targets, scanTools),
                subscribeToUpdates: {
                    topic: "scan.status",
                    key: `engagement:${engagementId}`,
                    conversationRef: TurnContext.getConversationReference(ctx.turnContext.activity),
                },
            };
        }

        // Step 5: Execute scan(s)
        const results: ScanInitResult[] = [];
        for (const tool of scanTools) {
            const result = await ctx.mcpClient.callTool<ScanInitResult>(tool.name, {
                engagement_id: engagementId,
                target_ids: tool.targetIds,
                priority: entities.priority || "medium",
                notify_on_complete: true,
                requested_by: ctx.user.id,
            });
            results.push(result);
        }

        // Step 6: Build response card
        return {
            card: this.buildScanStartedCard(engagementId, results),
            subscribeToUpdates: {
                topic: "scan.status",
                key: `engagement:${engagementId}`,
                conversationRef: TurnContext.getConversationReference(ctx.turnContext.activity),
            },
        };
    }

    private resolveScanTools(
        scanType: string,
        targets: Target[],
    ): { name: string; targetIds: number[] }[] {
        const toolMap: Record<string, { tool: string; targetTypes: string[] }> = {
            web:    { tool: "start_burp_scan",    targetTypes: ["web_application"] },
            api:    { tool: "start_burp_scan",    targetTypes: ["api_endpoint"] },
            infra:  { tool: "start_tenable_scan", targetTypes: ["ip_range", "hostname", "cidr_block"] },
            code:   { tool: "start_fortify_scan", targetTypes: ["source_repository"] },
            mobile: { tool: "start_mobile_scan",  targetTypes: ["mobile_application"] },
        };

        if (scanType === "all") {
            // Fan out to all applicable scan types based on available targets
            const tools: { name: string; targetIds: number[] }[] = [];
            for (const [, config] of Object.entries(toolMap)) {
                const matching = targets
                    .filter(t => config.targetTypes.includes(t.target_type))
                    .map(t => t.id);
                if (matching.length > 0) {
                    tools.push({ name: config.tool, targetIds: matching });
                }
            }
            return tools;
        }

        const config = toolMap[scanType];
        if (!config) {
            throw new Error(`Unknown scan type: ${scanType}`);
        }

        const matchingTargets = targets
            .filter(t => config.targetTypes.includes(t.target_type))
            .map(t => t.id);

        return [{ name: config.tool, targetIds: matchingTargets }];
    }

    private buildConfirmationCard(
        engagementId: number,
        scanType: string,
        scope: EngagementScope,
        targets: TargetList,
        scanTools: { name: string; targetIds: number[] }[],
    ): AdaptiveCard {
        const totalTargets = scanTools.reduce((sum, t) => sum + t.targetIds.length, 0);

        return {
            type: "AdaptiveCard",
            version: "1.5",
            body: [
                {
                    type: "TextBlock",
                    text: "🔒 Confirm Scan Initiation",
                    weight: "Bolder",
                    size: "Large",
                },
                {
                    type: "FactSet",
                    facts: [
                        { title: "Engagement",   value: `#${engagementId} — ${scope.engagement_name}` },
                        { title: "Customer",      value: scope.customer_name },
                        { title: "Scan Type",     value: scanType.toUpperCase() },
                        { title: "Targets",       value: `${totalTargets} target(s)` },
                        { title: "Scan Window",   value: scope.scan_window || "No restriction" },
                        { title: "Scanner Tools", value: scanTools.map(t => t.name).join(", ") },
                    ],
                },
                {
                    type: "TextBlock",
                    text: "⚠️ This will initiate active scanning against the targets listed above.",
                    color: "Warning",
                    wrap: true,
                },
            ],
            actions: [
                {
                    type: "Action.Submit",
                    title: "✅ Confirm & Start",
                    style: "positive",
                    data: {
                        action: "confirm_scan",
                        engagement_id: engagementId,
                        scan_type: scanType,
                        tools: scanTools,
                    },
                },
                {
                    type: "Action.Submit",
                    title: "❌ Cancel",
                    style: "destructive",
                    data: { action: "cancel" },
                },
            ],
        };
    }

    private buildScanStartedCard(
        engagementId: number,
        results: ScanInitResult[],
    ): AdaptiveCard {
        return {
            type: "AdaptiveCard",
            version: "1.5",
            body: [
                {
                    type: "TextBlock",
                    text: "✅ Scans Initiated",
                    weight: "Bolder",
                    size: "Large",
                    color: "Good",
                },
                {
                    type: "TextBlock",
                    text: `Engagement #${engagementId}`,
                    isSubtle: true,
                },
                {
                    type: "Container",
                    items: results.map(r => ({
                        type: "ColumnSet",
                        columns: [
                            {
                                type: "Column",
                                width: "stretch",
                                items: [
                                    { type: "TextBlock", text: r.scanner_type, weight: "Bolder" },
                                    { type: "TextBlock", text: `Job ID: ${r.job_id}`, isSubtle: true, size: "Small" },
                                ],
                            },
                            {
                                type: "Column",
                                width: "auto",
                                items: [
                                    {
                                        type: "TextBlock",
                                        text: r.status === "queued" ? "⏳ Queued" : "▶️ Running",
                                        color: r.status === "queued" ? "Warning" : "Good",
                                    },
                                ],
                            },
                        ],
                    })),
                },
                {
                    type: "TextBlock",
                    text: "You'll receive notifications as scans progress.",
                    isSubtle: true,
                    size: "Small",
                },
            ],
            actions: [
                {
                    type: "Action.Submit",
                    title: "📊 Check Status",
                    data: { action: "check_status", engagement_id: engagementId },
                },
            ],
        };
    }

    protected getSuggestions(ctx: CommandContext): string[] {
        const eid = ctx.parsedCommand.entities.engagement_id;
        if (eid) {
            return [
                `Start web scan for engagement ${eid}`,
                `Start infra scan for engagement ${eid}`,
                `Start all scans for engagement ${eid}`,
                `Show targets for engagement ${eid}`,
            ];
        }
        return ["Start scan for engagement <ID>", "List my engagements"];
    }
}
```

### 5.5 Show Targets Handler

```typescript
// src/handlers/show-targets-handler.ts

class ShowTargetsHandler extends BaseCommandHandler {
    intent = "show_targets";

    async validate(ctx: CommandContext): Promise<ValidationResult> {
        if (!ctx.parsedCommand.entities.engagement_id) {
            return {
                valid: false,
                missingEntities: ["engagement_id"],
                clarificationPrompt: "Which engagement's targets would you like to see? "
                    + "Please provide the engagement ID.",
            };
        }
        return { valid: true };
    }

    async execute(ctx: CommandContext): Promise<CommandResult> {
        const engagementId = ctx.parsedCommand.entities.engagement_id as number;

        // Read targets resource from MCP
        const targets = await ctx.mcpClient.readResource<TargetList>(
            `vapt://engagements/${engagementId}/targets`
        );

        // Read engagement scope for context
        const scope = await ctx.mcpClient.readResource<EngagementScope>(
            `vapt://engagements/${engagementId}/scope`
        );

        if (targets.items.length === 0) {
            return {
                text: `No targets defined for engagement #${engagementId} (${scope.engagement_name}).`,
                suggestions: [`Show scope for engagement ${engagementId}`],
            };
        }

        // Group targets by type
        const grouped = this.groupByType(targets.items);

        return {
            card: this.buildTargetsCard(engagementId, scope, grouped),
        };
    }

    private groupByType(targets: Target[]): Map<string, Target[]> {
        const map = new Map<string, Target[]>();
        for (const t of targets) {
            const group = map.get(t.target_type) || [];
            group.push(t);
            map.set(t.target_type, group);
        }
        return map;
    }

    private buildTargetsCard(
        engagementId: number,
        scope: EngagementScope,
        grouped: Map<string, Target[]>,
    ): AdaptiveCard {
        const typeIcons: Record<string, string> = {
            web_application:    "🌐",
            api_endpoint:       "🔌",
            ip_range:           "🖥️",
            hostname:           "🏷️",
            cidr_block:         "📡",
            source_repository:  "📦",
            mobile_application: "📱",
        };

        const sections: any[] = [];
        for (const [type, targets] of grouped) {
            sections.push({
                type: "TextBlock",
                text: `${typeIcons[type] || "🎯"} ${type.replace(/_/g, " ").toUpperCase()} (${targets.length})`,
                weight: "Bolder",
                spacing: "Medium",
            });

            for (const target of targets) {
                sections.push({
                    type: "ColumnSet",
                    columns: [
                        {
                            type: "Column",
                            width: "stretch",
                            items: [
                                { type: "TextBlock", text: target.value, weight: "Bolder", size: "Small" },
                                {
                                    type: "TextBlock",
                                    text: target.notes || "No notes",
                                    isSubtle: true,
                                    size: "Small",
                                    wrap: true,
                                },
                            ],
                        },
                        {
                            type: "Column",
                            width: "auto",
                            items: [
                                {
                                    type: "TextBlock",
                                    text: target.in_scope ? "✅ In Scope" : "⛔ Out of Scope",
                                    size: "Small",
                                },
                            ],
                        },
                    ],
                });
            }
        }

        return {
            type: "AdaptiveCard",
            version: "1.5",
            body: [
                {
                    type: "TextBlock",
                    text: `🎯 Targets — Engagement #${engagementId}`,
                    weight: "Bolder",
                    size: "Large",
                },
                {
                    type: "TextBlock",
                    text: `${scope.engagement_name} | ${scope.customer_name}`,
                    isSubtle: true,
                },
                ...sections,
            ],
            actions: [
                {
                    type: "Action.Submit",
                    title: "▶️ Start Scan",
                    data: { action: "start_scan_prompt", engagement_id: engagementId },
                },
                {
                    type: "Action.Submit",
                    title: "📋 View Scope",
                    data: { action: "view_scope", engagement_id: engagementId },
                },
            ],
        };
    }

    protected getSuggestions(): string[] {
        return ["Show targets for engagement <ID>", "List my engagements"];
    }
}
```

### 5.6 Fetch Scan Results Handler

```typescript
// src/handlers/fetch-results-handler.ts

class FetchResultsHandler extends BaseCommandHandler {
    intent = "fetch_results";

    async validate(ctx: CommandContext): Promise<ValidationResult> {
        const { entities } = ctx.parsedCommand;

        // Need either engagement_id + scanner_type, or job_id
        if (!entities.job_id && !entities.engagement_id) {
            return {
                valid: false,
                missingEntities: ["engagement_id"],
                clarificationPrompt: "Which scan results would you like to fetch? "
                    + "Provide an engagement ID or a specific job ID.",
            };
        }
        return { valid: true };
    }

    async execute(ctx: CommandContext): Promise<CommandResult> {
        const { entities } = ctx.parsedCommand;

        if (entities.job_id) {
            // Direct job result fetch
            const results = await ctx.mcpClient.callTool<ScanResults>("fetch_scan_results", {
                job_id: entities.job_id,
                include_raw: false,
            });
            return { card: this.buildResultsCard(results) };
        }

        // Engagement-level: read findings summary resource
        const engagementId = entities.engagement_id as number;
        const scannerFilter = entities.scanner_type as string | undefined;

        const summary = await ctx.mcpClient.readResource<FindingsSummary>(
            `vapt://engagements/${engagementId}/findings/summary`
            + (scannerFilter ? `?scanner=${scannerFilter}` : "")
        );

        return { card: this.buildFindingsSummaryCard(engagementId, summary) };
    }

    private buildResultsCard(results: ScanResults): AdaptiveCard {
        const severityCounts = {
            critical: results.findings.filter(f => f.severity === "critical").length,
            high:     results.findings.filter(f => f.severity === "high").length,
            medium:   results.findings.filter(f => f.severity === "medium").length,
            low:      results.findings.filter(f => f.severity === "low").length,
            info:     results.findings.filter(f => f.severity === "informational").length,
        };

        return {
            type: "AdaptiveCard",
            version: "1.5",
            body: [
                {
                    type: "TextBlock",
                    text: `📊 Scan Results — Job ${results.job_id}`,
                    weight: "Bolder",
                    size: "Large",
                },
                {
                    type: "FactSet",
                    facts: [
                        { title: "Scanner",    value: results.scanner_type },
                        { title: "Status",     value: results.status },
                        { title: "Duration",   value: results.duration_formatted },
                        { title: "Total",      value: `${results.findings.length} findings` },
                    ],
                },
                {
                    type: "ColumnSet",
                    columns: [
                        this.severityColumn("🔴", "Critical", severityCounts.critical),
                        this.severityColumn("🟠", "High",     severityCounts.high),
                        this.severityColumn("🟡", "Medium",   severityCounts.medium),
                        this.severityColumn("🔵", "Low",      severityCounts.low),
                        this.severityColumn("⚪", "Info",     severityCounts.info),
                    ],
                },
                // Top 5 critical/high findings
                {
                    type: "TextBlock",
                    text: "Top Findings",
                    weight: "Bolder",
                    spacing: "Large",
                },
                ...results.findings
                    .filter(f => f.severity === "critical" || f.severity === "high")
                    .slice(0, 5)
                    .map(f => ({
                        type: "ColumnSet",
                        columns: [
                            {
                                type: "Column",
                                width: "auto",
                                items: [{
                                    type: "TextBlock",
                                    text: f.severity === "critical" ? "🔴" : "🟠",
                                }],
                            },
                            {
                                type: "Column",
                                width: "stretch",
                                items: [
                                    { type: "TextBlock", text: f.title, weight: "Bolder", size: "Small" },
                                    { type: "TextBlock", text: f.location || "", isSubtle: true, size: "Small" },
                                ],
                            },
                            {
                                type: "Column",
                                width: "auto",
                                items: [{
                                    type: "TextBlock",
                                    text: `CVSS ${f.cvss_score?.toFixed(1) || "N/A"}`,
                                    size: "Small",
                                }],
                            },
                        ],
                    })),
            ],
            actions: [
                {
                    type: "Action.OpenUrl",
                    title: "📄 Full Report",
                    url: `${process.env.PORTAL_URL}/findings?job_id=${results.job_id}`,
                },
                {
                    type: "Action.Submit",
                    title: "👤 Assign Analyst",
                    data: { action: "assign_analyst_prompt", job_id: results.job_id },
                },
            ],
        };
    }

    private buildFindingsSummaryCard(engagementId: number, summary: FindingsSummary): AdaptiveCard {
        return {
            type: "AdaptiveCard",
            version: "1.5",
            body: [
                {
                    type: "TextBlock",
                    text: `📊 Findings Summary — Engagement #${engagementId}`,
                    weight: "Bolder",
                    size: "Large",
                },
                {
                    type: "ColumnSet",
                    columns: [
                        this.severityColumn("🔴", "Critical", summary.by_severity.critical),
                        this.severityColumn("🟠", "High",     summary.by_severity.high),
                        this.severityColumn("🟡", "Medium",   summary.by_severity.medium),
                        this.severityColumn("🔵", "Low",      summary.by_severity.low),
                    ],
                },
                {
                    type: "FactSet",
                    facts: [
                        { title: "Total Findings",  value: String(summary.total_findings) },
                        { title: "Confirmed",       value: String(summary.confirmed) },
                        { title: "False Positives",  value: String(summary.false_positives) },
                        { title: "Pending Review",   value: String(summary.pending_review) },
                        { title: "Scanners Run",     value: summary.scanners_completed.join(", ") },
                    ],
                },
            ],
            actions: [
                {
                    type: "Action.Submit",
                    title: "🔍 View Details",
                    data: { action: "view_findings", engagement_id: engagementId },
                },
                {
                    type: "Action.Submit",
                    title: "📝 Generate Report",
                    data: { action: "generate_report", engagement_id: engagementId },
                },
            ],
        };
    }

    private severityColumn(icon: string, label: string, count: number) {
        return {
            type: "Column",
            width: "auto",
            items: [
                { type: "TextBlock", text: icon, horizontalAlignment: "Center" },
                { type: "TextBlock", text: String(count), weight: "Bolder", horizontalAlignment: "Center" },
                { type: "TextBlock", text: label, size: "Small", isSubtle: true, horizontalAlignment: "Center" },
            ],
        };
    }

    protected getSuggestions(): string[] {
        return [
            "Fetch results for engagement <ID>",
            "Fetch Burp results for engagement <ID>",
            "Show findings for job <JOB_ID>",
        ];
    }
}
```

### 5.7 Scan Status Handler

```typescript
// src/handlers/scan-status-handler.ts

class ScanStatusHandler extends BaseCommandHandler {
    intent = "scan_status";

    async validate(ctx: CommandContext): Promise<ValidationResult> {
        const { entities } = ctx.parsedCommand;
        if (!entities.engagement_id && !entities.job_id) {
            return {
                valid: false,
                missingEntities: ["engagement_id"],
                clarificationPrompt: "Which engagement or job ID would you like status for?",
            };
        }
        return { valid: true };
    }

    async execute(ctx: CommandContext): Promise<CommandResult> {
        const { entities } = ctx.parsedCommand;

        if (entities.job_id) {
            const status = await ctx.mcpClient.callTool<ScanJobStatus>("get_scan_status", {
                job_id: entities.job_id,
            });
            return { card: this.buildJobStatusCard(status) };
        }

        const engagementId = entities.engagement_id as number;
        const scanStatus = await ctx.mcpClient.readResource<EngagementScanStatus>(
            `vapt://engagements/${engagementId}/scans/status`
        );

        return { card: this.buildEngagementStatusCard(engagementId, scanStatus) };
    }

    private buildJobStatusCard(status: ScanJobStatus): AdaptiveCard {
        const statusIcons: Record<string, string> = {
            queued: "⏳", initialising: "🔄", running: "▶️",
            paused: "⏸️", completed: "✅", failed: "❌",
            cancelled: "🚫", retrying: "🔁",
        };

        const progressBar = status.progress_pct !== undefined
            ? this.renderProgressBar(status.progress_pct)
            : null;

        const body: any[] = [
            {
                type: "TextBlock",
                text: `${statusIcons[status.status] || "❓"} Scan Job ${status.job_id}`,
                weight: "Bolder",
                size: "Large",
            },
            {
                type: "FactSet",
                facts: [
                    { title: "Scanner",    value: status.scanner_type },
                    { title: "Status",     value: status.status },
                    { title: "Started",    value: status.started_at || "Not yet" },
                    { title: "Elapsed",    value: status.elapsed_formatted || "—" },
                    { title: "Targets",    value: `${status.targets_completed}/${status.targets_total}` },
                ],
            },
        ];

        if (progressBar) {
            body.push({
                type: "TextBlock",
                text: progressBar,
                fontType: "Monospace",
                size: "Small",
            });
        }

        if (status.current_phase) {
            body.push({
                type: "TextBlock",
                text: `Current phase: ${status.current_phase}`,
                isSubtle: true,
                size: "Small",
            });
        }

        return {
            type: "AdaptiveCard",
            version: "1.5",
            body,
            actions: status.status === "running"
                ? [{ type: "Action.Submit", title: "⏸️ Pause", data: { action: "pause_scan", job_id: status.job_id } }]
                : status.status === "completed"
                    ? [{ type: "Action.Submit", title: "📊 View Results", data: { action: "fetch_results", job_id: status.job_id } }]
                    : [],
        };
    }

    private buildEngagementStatusCard(engagementId: number, status: EngagementScanStatus): AdaptiveCard {
        return {
            type: "AdaptiveCard",
            version: "1.5",
            body: [
                {
                    type: "TextBlock",
                    text: `📊 Scan Status — Engagement #${engagementId}`,
                    weight: "Bolder",
                    size: "Large",
                },
                ...status.jobs.map(job => ({
                    type: "ColumnSet",
                    separator: true,
                    columns: [
                        {
                            type: "Column",
                            width: "auto",
                            items: [{ type: "TextBlock", text: this.statusIcon(job.status) }],
                        },
                        {
                            type: "Column",
                            width: "stretch",
                            items: [
                                { type: "TextBlock", text: `${job.scanner_type} — Job ${job.job_id}`, weight: "Bolder", size: "Small" },
                                { type: "TextBlock", text: `${job.progress_pct || 0}% complete`, isSubtle: true, size: "Small" },
                            ],
                        },
                        {
                            type: "Column",
                            width: "auto",
                            items: [{ type: "TextBlock", text: job.status, size: "Small" }],
                        },
                    ],
                })),
            ],
            actions: [
                {
                    type: "Action.Submit",
                    title: "🔄 Refresh",
                    data: { action: "scan_status", engagement_id: engagementId },
                },
            ],
        };
    }

    private renderProgressBar(pct: number): string {
        const filled = Math.round(pct / 5);
        const empty = 20 - filled;
        return `[${"█".repeat(filled)}${"░".repeat(empty)}] ${pct}%`;
    }

    private statusIcon(status: string): string {
        const icons: Record<string, string> = {
            queued: "⏳", running: "▶️", completed: "✅",
            failed: "❌", paused: "⏸️", retrying: "🔁",
        };
        return icons[status] || "❓";
    }

    protected getSuggestions(): string[] {
        return ["Check status for engagement <ID>", "Status of job <JOB_ID>"];
    }
}
```

### 5.8 Assign Analyst Handler

```typescript
// src/handlers/assign-analyst-handler.ts

class AssignAnalystHandler extends BaseCommandHandler {
    intent = "assign_analyst";

    async validate(ctx: CommandContext): Promise<ValidationResult> {
        const { entities } = ctx.parsedCommand;

        if (!entities.engagement_id) {
            return {
                valid: false,
                missingEntities: ["engagement_id"],
                clarificationPrompt: "Which engagement needs analyst assignment?",
            };
        }

        if (!entities.analyst_identifier) {
            return {
                valid: false,
                missingEntities: ["analyst_identifier"],
                clarificationPrompt: "Which analyst should be assigned? "
                    + "Provide an analyst name or email (e.g., 'Assign @jane.doe to engagement 102').",
            };
        }

        return { valid: true };
    }

    async execute(ctx: CommandContext): Promise<CommandResult> {
        const { entities } = ctx.parsedCommand;
        const engagementId = entities.engagement_id as number;
        const analystIdentifier = entities.analyst_identifier as string;

        // Determine assignment scope — specific findings or full engagement
        const scope = entities.finding_ids
            ? { type: "findings" as const, finding_ids: entities.finding_ids as number[] }
            : { type: "engagement" as const };

        const result = await ctx.mcpClient.callTool<AssignmentResult>("assign_analyst", {
            engagement_id: engagementId,
            analyst_identifier: analystIdentifier,
            scope: scope.type,
            finding_ids: scope.type === "findings" ? scope.finding_ids : undefined,
            task_type: entities.task_type || "manual_validation",
            priority: entities.priority || "medium",
            notes: entities.notes || undefined,
        });

        return {
            card: {
                type: "AdaptiveCard",
                version: "1.5",
                body: [
                    {
                        type: "TextBlock",
                        text: "✅ Analyst Assigned",
                        weight: "Bolder",
                        size: "Large",
                        color: "Good",
                    },
                    {
                        type: "FactSet",
                        facts: [
                            { title: "Analyst",     value: result.analyst_name },
                            { title: "Engagement",  value: `#${engagementId}` },
                            { title: "Task",        value: result.task_type },
                            { title: "Scope",       value: scope.type === "findings"
                                ? `${(scope as any).finding_ids.length} specific findings`
                                : "Full engagement" },
                            { title: "Priority",    value: result.priority },
                            { title: "Due Date",    value: result.due_date || "Not set" },
                        ],
                    },
                    {
                        type: "TextBlock",
                        text: `${result.analyst_name} has been notified via Teams and email.`,
                        isSubtle: true,
                        size: "Small",
                    },
                ],
                actions: [
                    {
                        type: "Action.Submit",
                        title: "📊 View Assignment",
                        data: { action: "view_assignment", assignment_id: result.assignment_id },
                    },
                ],
            },
        };
    }

    protected getSuggestions(): string[] {
        return [
            "Assign @analyst to engagement <ID>",
            "Assign manual validation for engagement <ID>",
        ];
    }
}
```

### 5.9 Generate Report Handler

```typescript
// src/handlers/generate-report-handler.ts

class GenerateReportHandler extends BaseCommandHandler {
    intent = "generate_report";

    async validate(ctx: CommandContext): Promise<ValidationResult> {
        if (!ctx.parsedCommand.entities.engagement_id) {
            return {
                valid: false,
                missingEntities: ["engagement_id"],
                clarificationPrompt: "Which engagement should I generate a report for?",
            };
        }
        return { valid: true };
    }

    async execute(ctx: CommandContext): Promise<CommandResult> {
        const { entities } = ctx.parsedCommand;
        const engagementId = entities.engagement_id as number;
        const reportFormat = (entities.format as string) || "pdf";
        const reportType = (entities.report_type as string) || "executive_summary";

        // Check if there are completed scans
        const scanStatus = await ctx.mcpClient.readResource<EngagementScanStatus>(
            `vapt://engagements/${engagementId}/scans/status`
        );

        const completedScans = scanStatus.jobs.filter(j => j.status === "completed");
        const runningScans = scanStatus.jobs.filter(j => j.status === "running");

        if (completedScans.length === 0) {
            return {
                text: `No completed scans for engagement #${engagementId}. `
                    + (runningScans.length > 0
                        ? `There are ${runningScans.length} scan(s) still running.`
                        : "Please start scans first."),
                suggestions: [
                    `Check status for engagement ${engagementId}`,
                    `Start scan for engagement ${engagementId}`,
                ],
            };
        }

        // Call MCP generate_report tool (async — returns immediately with report_id)
        const result = await ctx.mcpClient.callTool<ReportInitResult>("generate_report", {
            engagement_id: engagementId,
            format: reportFormat,
            report_type: reportType,
            include_executive_summary: true,
            include_methodology: true,
            include_detailed_findings: true,
            include_remediation_roadmap: true,
            include_appendices: true,
            requested_by: ctx.user.id,
        });

        return {
            card: {
                type: "AdaptiveCard",
                version: "1.5",
                body: [
                    {
                        type: "TextBlock",
                        text: "📝 Report Generation Started",
                        weight: "Bolder",
                        size: "Large",
                    },
                    {
                        type: "FactSet",
                        facts: [
                            { title: "Report ID",    value: result.report_id },
                            { title: "Engagement",   value: `#${engagementId}` },
                            { title: "Type",         value: reportType.replace(/_/g, " ") },
                            { title: "Format",       value: reportFormat.toUpperCase() },
                            { title: "Scans Included", value: `${completedScans.length} completed scans` },
                            { title: "Est. Time",    value: result.estimated_duration || "5-10 minutes" },
                        ],
                    },
                    {
                        type: "TextBlock",
                        text: "AI-powered report generation is in progress. "
                            + "You'll be notified when the draft is ready for review.",
                        isSubtle: true,
                        wrap: true,
                    },
                ],
                actions: [
                    {
                        type: "Action.Submit",
                        title: "📊 Check Progress",
                        data: { action: "report_status", report_id: result.report_id },
                    },
                ],
            },
            subscribeToUpdates: {
                topic: "report.status",
                key: `report:${result.report_id}`,
                conversationRef: TurnContext.getConversationReference(ctx.turnContext.activity),
            },
        };
    }

    protected getSuggestions(): string[] {
        return [
            "Generate report for engagement <ID>",
            "Generate PDF report for engagement <ID>",
            "Generate executive summary for engagement <ID>",
        ];
    }
}
```

### 5.10 Publish Report Handler

```typescript
// src/handlers/publish-report-handler.ts

class PublishReportHandler extends BaseCommandHandler {
    intent = "publish_report";

    async validate(ctx: CommandContext): Promise<ValidationResult> {
        const { entities } = ctx.parsedCommand;

        if (!entities.report_id && !entities.engagement_id) {
            return {
                valid: false,
                missingEntities: ["report_id"],
                clarificationPrompt: "Which report should be published? "
                    + "Provide a report ID or engagement ID.",
            };
        }
        return { valid: true };
    }

    async execute(ctx: CommandContext): Promise<CommandResult> {
        const { entities } = ctx.parsedCommand;
        const reportId = entities.report_id as string;

        // Always require confirmation for publish — this sends to the customer
        return {
            card: {
                type: "AdaptiveCard",
                version: "1.5",
                body: [
                    {
                        type: "TextBlock",
                        text: "⚠️ Confirm Report Publication",
                        weight: "Bolder",
                        size: "Large",
                        color: "Warning",
                    },
                    {
                        type: "TextBlock",
                        text: "Publishing this report will make it visible to the customer "
                            + "on their portal. This action requires lead analyst approval.",
                        wrap: true,
                    },
                    {
                        type: "FactSet",
                        facts: [
                            { title: "Report ID", value: reportId },
                        ],
                    },
                    {
                        type: "TextBlock",
                        text: "Are you sure you want to proceed?",
                        weight: "Bolder",
                    },
                ],
                actions: [
                    {
                        type: "Action.Submit",
                        title: "✅ Publish to Customer",
                        style: "positive",
                        data: {
                            action: "confirm_publish",
                            report_id: reportId,
                        },
                    },
                    {
                        type: "Action.Submit",
                        title: "👀 Preview First",
                        data: {
                            action: "preview_report",
                            report_id: reportId,
                        },
                    },
                    {
                        type: "Action.Submit",
                        title: "❌ Cancel",
                        style: "destructive",
                        data: { action: "cancel" },
                    },
                ],
            },
        };
    }

    protected getSuggestions(): string[] {
        return ["Publish report <REPORT_ID>"];
    }
}

// Confirmation handler (invoked when user clicks "Confirm & Publish")
class ConfirmPublishHandler {
    async handle(ctx: CommandContext, reportId: string): Promise<CommandResult> {
        const result = await ctx.mcpClient.callTool<PublishResult>("publish_report", {
            report_id: reportId,
            published_by: ctx.user.id,
            notify_customer: true,
            delivery_channels: ["portal", "email"],
        });

        return {
            card: {
                type: "AdaptiveCard",
                version: "1.5",
                body: [
                    {
                        type: "TextBlock",
                        text: "✅ Report Published",
                        weight: "Bolder",
                        size: "Large",
                        color: "Good",
                    },
                    {
                        type: "FactSet",
                        facts: [
                            { title: "Report ID",   value: result.report_id },
                            { title: "Published At", value: result.published_at },
                            { title: "Portal URL",   value: result.portal_url },
                            { title: "Notified",     value: result.notifications_sent.join(", ") },
                        ],
                    },
                ],
            },
        };
    }
}
```

### 5.11 Findings Summary Handler

```typescript
// src/handlers/findings-summary-handler.ts

class FindingsSummaryHandler extends BaseCommandHandler {
    intent = "findings_summary";

    async validate(ctx: CommandContext): Promise<ValidationResult> {
        if (!ctx.parsedCommand.entities.engagement_id) {
            return {
                valid: false,
                missingEntities: ["engagement_id"],
                clarificationPrompt: "Which engagement's findings summary would you like?",
            };
        }
        return { valid: true };
    }

    async execute(ctx: CommandContext): Promise<CommandResult> {
        const engagementId = ctx.parsedCommand.entities.engagement_id as number;
        const severity = ctx.parsedCommand.entities.severity as string | undefined;

        const summary = await ctx.mcpClient.readResource<FindingsSummary>(
            `vapt://engagements/${engagementId}/findings/summary`
        );

        // If severity filter, also fetch detailed findings
        if (severity) {
            const findings = await ctx.mcpClient.readResource<FindingsList>(
                `vapt://engagements/${engagementId}/findings?severity=${severity}&limit=10`
            );
            return { card: this.buildFilteredFindingsCard(engagementId, severity, findings) };
        }

        // Use the same summary card from FetchResultsHandler
        return { card: new FetchResultsHandler().buildFindingsSummaryCard(engagementId, summary) };
    }

    private buildFilteredFindingsCard(
        engagementId: number,
        severity: string,
        findings: FindingsList,
    ): AdaptiveCard {
        const severityColors: Record<string, string> = {
            critical: "Attention", high: "Warning", medium: "Default", low: "Accent",
        };

        return {
            type: "AdaptiveCard",
            version: "1.5",
            body: [
                {
                    type: "TextBlock",
                    text: `🔍 ${severity.toUpperCase()} Findings — Engagement #${engagementId}`,
                    weight: "Bolder",
                    size: "Large",
                    color: severityColors[severity] || "Default",
                },
                {
                    type: "TextBlock",
                    text: `Showing ${findings.items.length} of ${findings.total} findings`,
                    isSubtle: true,
                },
                ...findings.items.map((f, i) => ({
                    type: "Container",
                    separator: i > 0,
                    items: [
                        {
                            type: "ColumnSet",
                            columns: [
                                {
                                    type: "Column",
                                    width: "stretch",
                                    items: [
                                        { type: "TextBlock", text: f.title, weight: "Bolder", size: "Small", wrap: true },
                                        { type: "TextBlock", text: `${f.scanner_type} | ${f.location || "N/A"}`, isSubtle: true, size: "Small" },
                                    ],
                                },
                                {
                                    type: "Column",
                                    width: "auto",
                                    verticalContentAlignment: "Center",
                                    items: [
                                        { type: "TextBlock", text: `CVSS ${f.cvss_score?.toFixed(1) || "—"}`, weight: "Bolder", size: "Small" },
                                        { type: "TextBlock", text: f.validation_status, isSubtle: true, size: "Small" },
                                    ],
                                },
                            ],
                        },
                    ],
                })),
            ],
            actions: [
                {
                    type: "Action.Submit",
                    title: "📄 Export Findings",
                    data: { action: "export_findings", engagement_id: engagementId, severity },
                },
                findings.total > findings.items.length
                    ? {
                        type: "Action.Submit",
                        title: "➡️ Next Page",
                        data: { action: "findings_page", engagement_id: engagementId, severity, offset: findings.items.length },
                    }
                    : null,
            ].filter(Boolean),
        };
    }

    protected getSuggestions(): string[] {
        return [
            "Show findings for engagement <ID>",
            "Show critical findings for engagement <ID>",
        ];
    }
}
```

### 5.12 Command Handler Registry

```typescript
// src/handlers/handler-registry.ts

class CommandHandlerRegistry {
    private handlers: Map<string, CommandHandler> = new Map();

    constructor() {
        // Register all command handlers
        this.register(new StartScanHandler());
        this.register(new ShowTargetsHandler());
        this.register(new FetchResultsHandler());
        this.register(new ScanStatusHandler());
        this.register(new AssignAnalystHandler());
        this.register(new GenerateReportHandler());
        this.register(new PublishReportHandler());
        this.register(new FindingsSummaryHandler());
        this.register(new HelpHandler());
        this.register(new SubscribeHandler());
    }

    register(handler: CommandHandler): void {
        this.handlers.set(handler.intent, handler);
    }

    get(intent: string): CommandHandler | undefined {
        return this.handlers.get(intent);
    }

    async dispatch(ctx: CommandContext): Promise<CommandResult> {
        const handler = this.handlers.get(ctx.parsedCommand.intent);

        if (!handler) {
            return {
                text: `Unknown command: "${ctx.parsedCommand.rawInput}". Type **help** for available commands.`,
                suggestions: ["help"],
            };
        }

        // RBAC check
        const permission = COMMAND_PERMISSIONS[ctx.parsedCommand.intent];
        if (permission && !permission.allowedRoles.includes(ctx.user.role)) {
            return {
                text: `⛔ You don't have permission to use this command. Required role: ${permission.allowedRoles.join(" or ")}.`,
            };
        }

        // Channel restriction check
        if (permission?.channelRestriction === "private" && !isPrivateChannel(ctx.turnContext)) {
            return {
                text: "🔒 This command can only be used in private chats or private channels for security reasons.",
            };
        }

        // Audit log
        await logCommandAudit(ctx);

        return handler.handle(ctx);
    }
}
```

### 5.13 Action Submit Handler (Adaptive Card Button Clicks)

```typescript
// src/handlers/action-submit-handler.ts

class ActionSubmitHandler {
    private registry: CommandHandlerRegistry;
    private mcpClient: MCPClientAdapter;

    constructor(registry: CommandHandlerRegistry, mcpClient: MCPClientAdapter) {
        this.registry = registry;
        this.mcpClient = mcpClient;
    }

    async handleSubmitAction(turnContext: TurnContext, user: PlatformUser): Promise<void> {
        const data = turnContext.activity.value;

        if (!data || !data.action) {
            await turnContext.sendActivity("Invalid action. Please try again.");
            return;
        }

        switch (data.action) {
            case "confirm_scan":
                await this.handleConfirmScan(turnContext, user, data);
                break;

            case "confirm_publish":
                await this.handleConfirmPublish(turnContext, user, data);
                break;

            case "cancel":
                await turnContext.sendActivity("Operation cancelled.");
                break;

            case "retry":
                // Re-execute the last failed command from conversation state
                const lastCommand = await this.getLastCommand(turnContext);
                if (lastCommand) {
                    await this.registry.dispatch({
                        turnContext,
                        parsedCommand: lastCommand,
                        user,
                        mcpClient: this.mcpClient,
                        conversationState: await this.getConversationState(turnContext),
                        logger: this.logger,
                    });
                }
                break;

            case "check_status":
            case "scan_status":
                await this.dispatchSyntheticCommand(turnContext, user, "scan_status", {
                    engagement_id: data.engagement_id,
                    job_id: data.job_id,
                });
                break;

            case "fetch_results":
                await this.dispatchSyntheticCommand(turnContext, user, "fetch_results", {
                    job_id: data.job_id,
                    engagement_id: data.engagement_id,
                });
                break;

            case "view_findings":
                await this.dispatchSyntheticCommand(turnContext, user, "findings_summary", {
                    engagement_id: data.engagement_id,
                });
                break;

            case "assign_analyst_prompt":
                await turnContext.sendActivity(
                    "Who should be assigned? Reply with: `assign @analyst to engagement "
                    + `${data.engagement_id}\``
                );
                break;

            case "generate_report":
                await this.dispatchSyntheticCommand(turnContext, user, "generate_report", {
                    engagement_id: data.engagement_id,
                });
                break;

            case "start_scan_prompt":
                await turnContext.sendActivity(
                    `What type of scan? Reply with: \`start <web|api|infra|code|mobile|all> scan for engagement ${data.engagement_id}\``
                );
                break;

            default:
                await turnContext.sendActivity(`Unknown action: ${data.action}`);
        }
    }

    private async dispatchSyntheticCommand(
        turnContext: TurnContext,
        user: PlatformUser,
        intent: string,
        entities: Record<string, unknown>,
    ): Promise<void> {
        const syntheticCommand: ParsedCommand = {
            intent,
            confidence: 1.0,
            source: "action_submit",
            entities,
            rawInput: `[Button: ${intent}]`,
            requiresConfirmation: false,
        };

        const result = await this.registry.dispatch({
            turnContext,
            parsedCommand: syntheticCommand,
            user,
            mcpClient: this.mcpClient,
            conversationState: await this.getConversationState(turnContext),
            logger: this.logger,
        });

        if (result.card) {
            await turnContext.sendActivity({
                attachments: [CardFactory.adaptiveCard(result.card)],
            });
        } else if (result.text) {
            await turnContext.sendActivity(result.text);
        }
    }

    private async handleConfirmScan(
        turnContext: TurnContext,
        user: PlatformUser,
        data: any,
    ): Promise<void> {
        const results: ScanInitResult[] = [];
        for (const tool of data.tools) {
            const result = await this.mcpClient.callTool<ScanInitResult>(tool.name, {
                engagement_id: data.engagement_id,
                target_ids: tool.targetIds,
                priority: "medium",
                notify_on_complete: true,
                requested_by: user.id,
            });
            results.push(result);
        }

        const card = new StartScanHandler().buildScanStartedCard(data.engagement_id, results);
        await turnContext.sendActivity({
            attachments: [CardFactory.adaptiveCard(card)],
        });
    }

    private async handleConfirmPublish(
        turnContext: TurnContext,
        user: PlatformUser,
        data: any,
    ): Promise<void> {
        const handler = new ConfirmPublishHandler();
        const result = await handler.handle(
            {
                turnContext,
                parsedCommand: { intent: "publish_report", confidence: 1.0, source: "action_submit", entities: { report_id: data.report_id }, rawInput: "", requiresConfirmation: false },
                user,
                mcpClient: this.mcpClient,
                conversationState: await this.getConversationState(turnContext),
                logger: this.logger,
            },
            data.report_id,
        );

        if (result.card) {
            await turnContext.sendActivity({
                attachments: [CardFactory.adaptiveCard(result.card)],
            });
        }
    }
}
```

---

## 6. Adaptive Card Templates

### 6.1 Card Template Engine

```typescript
// src/cards/card-template-engine.ts

interface CardTemplateContext {
    data: Record<string, unknown>;
    user: PlatformUser;
    theme?: "light" | "dark";
}

class CardTemplateEngine {
    private templates: Map<string, (ctx: CardTemplateContext) => AdaptiveCard> = new Map();

    constructor() {
        this.registerBuiltinTemplates();
    }

    render(templateName: string, ctx: CardTemplateContext): AdaptiveCard {
        const template = this.templates.get(templateName);
        if (!template) {
            throw new Error(`Unknown card template: ${templateName}`);
        }
        return template(ctx);
    }

    private registerBuiltinTemplates(): void {
        this.templates.set("scan_progress",       this.scanProgressCard);
        this.templates.set("scan_complete",        this.scanCompleteCard);
        this.templates.set("finding_alert",        this.findingAlertCard);
        this.templates.set("report_ready",         this.reportReadyCard);
        this.templates.set("assignment_notify",    this.assignmentNotifyCard);
        this.templates.set("error",                this.errorCard);
        this.templates.set("engagement_overview",  this.engagementOverviewCard);
        this.templates.set("help",                 this.helpCard);
    }
}
```

### 6.2 Scan Progress Notification Card

```json
{
    "type": "AdaptiveCard",
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "version": "1.5",
    "body": [
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [
                        {
                            "type": "Image",
                            "url": "${scanner_icon_url}",
                            "size": "Small",
                            "style": "Person"
                        }
                    ]
                },
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "▶️ Scan In Progress",
                            "weight": "Bolder",
                            "size": "Medium"
                        },
                        {
                            "type": "TextBlock",
                            "text": "${scanner_type} — Job ${job_id}",
                            "isSubtle": true,
                            "spacing": "None"
                        }
                    ]
                }
            ]
        },
        {
            "type": "TextBlock",
            "text": "Engagement #${engagement_id} — ${engagement_name}",
            "spacing": "Small"
        },
        {
            "type": "ColumnSet",
            "spacing": "Medium",
            "columns": [
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "${progress_bar}",
                            "fontType": "Monospace",
                            "size": "Small"
                        }
                    ]
                },
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "${progress_pct}%",
                            "weight": "Bolder"
                        }
                    ]
                }
            ]
        },
        {
            "type": "FactSet",
            "facts": [
                { "title": "Phase",      "value": "${current_phase}" },
                { "title": "Elapsed",    "value": "${elapsed_time}" },
                { "title": "Targets",    "value": "${targets_completed}/${targets_total}" },
                { "title": "Findings",   "value": "${findings_so_far} so far" }
            ]
        }
    ],
    "actions": [
        {
            "type": "Action.Submit",
            "title": "⏸️ Pause Scan",
            "data": { "action": "pause_scan", "job_id": "${job_id}" }
        },
        {
            "type": "Action.Submit",
            "title": "🔄 Refresh",
            "data": { "action": "scan_status", "job_id": "${job_id}" }
        }
    ]
}
```

### 6.3 Scan Complete Notification Card

```json
{
    "type": "AdaptiveCard",
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "version": "1.5",
    "body": [
        {
            "type": "TextBlock",
            "text": "✅ Scan Complete",
            "weight": "Bolder",
            "size": "Large",
            "color": "Good"
        },
        {
            "type": "FactSet",
            "facts": [
                { "title": "Scanner",      "value": "${scanner_type}" },
                { "title": "Job ID",       "value": "${job_id}" },
                { "title": "Engagement",   "value": "#${engagement_id} — ${engagement_name}" },
                { "title": "Duration",     "value": "${duration}" },
                { "title": "Targets",      "value": "${targets_scanned} scanned" }
            ]
        },
        {
            "type": "TextBlock",
            "text": "Findings Summary",
            "weight": "Bolder",
            "spacing": "Medium"
        },
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "1",
                    "items": [
                        { "type": "TextBlock", "text": "🔴", "horizontalAlignment": "Center" },
                        { "type": "TextBlock", "text": "${critical_count}", "weight": "Bolder", "horizontalAlignment": "Center", "color": "Attention" },
                        { "type": "TextBlock", "text": "Critical", "size": "Small", "isSubtle": true, "horizontalAlignment": "Center" }
                    ]
                },
                {
                    "type": "Column",
                    "width": "1",
                    "items": [
                        { "type": "TextBlock", "text": "🟠", "horizontalAlignment": "Center" },
                        { "type": "TextBlock", "text": "${high_count}", "weight": "Bolder", "horizontalAlignment": "Center", "color": "Warning" },
                        { "type": "TextBlock", "text": "High", "size": "Small", "isSubtle": true, "horizontalAlignment": "Center" }
                    ]
                },
                {
                    "type": "Column",
                    "width": "1",
                    "items": [
                        { "type": "TextBlock", "text": "🟡", "horizontalAlignment": "Center" },
                        { "type": "TextBlock", "text": "${medium_count}", "weight": "Bolder", "horizontalAlignment": "Center" },
                        { "type": "TextBlock", "text": "Medium", "size": "Small", "isSubtle": true, "horizontalAlignment": "Center" }
                    ]
                },
                {
                    "type": "Column",
                    "width": "1",
                    "items": [
                        { "type": "TextBlock", "text": "🔵", "horizontalAlignment": "Center" },
                        { "type": "TextBlock", "text": "${low_count}", "weight": "Bolder", "horizontalAlignment": "Center", "color": "Accent" },
                        { "type": "TextBlock", "text": "Low", "size": "Small", "isSubtle": true, "horizontalAlignment": "Center" }
                    ]
                }
            ]
        },
        {
            "type": "TextBlock",
            "text": "⚠️ ${critical_count} critical and ${high_count} high-severity findings require immediate attention.",
            "color": "Attention",
            "wrap": true,
            "spacing": "Medium",
            "$when": "${critical_count > 0 || high_count > 0}"
        }
    ],
    "actions": [
        {
            "type": "Action.Submit",
            "title": "📊 View Results",
            "style": "positive",
            "data": { "action": "fetch_results", "job_id": "${job_id}" }
        },
        {
            "type": "Action.Submit",
            "title": "👤 Assign Analyst",
            "data": { "action": "assign_analyst_prompt", "engagement_id": "${engagement_id}" }
        },
        {
            "type": "Action.Submit",
            "title": "📝 Generate Report",
            "data": { "action": "generate_report", "engagement_id": "${engagement_id}" }
        }
    ]
}
```

### 6.4 Critical Finding Alert Card

```json
{
    "type": "AdaptiveCard",
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "version": "1.5",
    "body": [
        {
            "type": "Container",
            "style": "attention",
            "bleed": true,
            "items": [
                {
                    "type": "TextBlock",
                    "text": "🚨 CRITICAL FINDING DETECTED",
                    "weight": "Bolder",
                    "size": "Large",
                    "color": "Attention"
                }
            ]
        },
        {
            "type": "FactSet",
            "facts": [
                { "title": "Title",        "value": "${finding_title}" },
                { "title": "Severity",     "value": "CRITICAL — CVSS ${cvss_score}" },
                { "title": "Scanner",      "value": "${scanner_type}" },
                { "title": "Engagement",   "value": "#${engagement_id} — ${engagement_name}" },
                { "title": "Customer",     "value": "${customer_name}" },
                { "title": "Location",     "value": "${finding_location}" }
            ]
        },
        {
            "type": "TextBlock",
            "text": "Description",
            "weight": "Bolder",
            "spacing": "Medium"
        },
        {
            "type": "TextBlock",
            "text": "${finding_description}",
            "wrap": true,
            "maxLines": 5
        },
        {
            "type": "TextBlock",
            "text": "AI Assessment",
            "weight": "Bolder",
            "spacing": "Medium"
        },
        {
            "type": "FactSet",
            "facts": [
                { "title": "Exploitability",   "value": "${ai_exploitability}" },
                { "title": "Business Impact",  "value": "${ai_business_impact}" },
                { "title": "False Positive",    "value": "${ai_fp_probability}% probability" },
                { "title": "Remediation",       "value": "${ai_remediation_summary}" }
            ]
        }
    ],
    "actions": [
        {
            "type": "Action.Submit",
            "title": "✅ Confirm Finding",
            "style": "positive",
            "data": {
                "action": "validate_finding",
                "finding_id": "${finding_id}",
                "validation": "confirmed"
            }
        },
        {
            "type": "Action.Submit",
            "title": "❌ False Positive",
            "style": "destructive",
            "data": {
                "action": "validate_finding",
                "finding_id": "${finding_id}",
                "validation": "false_positive"
            }
        },
        {
            "type": "Action.Submit",
            "title": "🔍 View Details",
            "data": {
                "action": "view_finding_detail",
                "finding_id": "${finding_id}"
            }
        },
        {
            "type": "Action.OpenUrl",
            "title": "🌐 Open in Portal",
            "url": "${portal_url}/findings/${finding_id}"
        }
    ]
}
```

### 6.5 Report Ready Card

```json
{
    "type": "AdaptiveCard",
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "version": "1.5",
    "body": [
        {
            "type": "TextBlock",
            "text": "📄 Report Ready for Review",
            "weight": "Bolder",
            "size": "Large"
        },
        {
            "type": "FactSet",
            "facts": [
                { "title": "Report ID",    "value": "${report_id}" },
                { "title": "Engagement",   "value": "#${engagement_id} — ${engagement_name}" },
                { "title": "Customer",     "value": "${customer_name}" },
                { "title": "Type",         "value": "${report_type}" },
                { "title": "Format",       "value": "${report_format}" },
                { "title": "Generated",    "value": "${generated_at}" },
                { "title": "Pages",        "value": "${page_count}" }
            ]
        },
        {
            "type": "TextBlock",
            "text": "Report Contents",
            "weight": "Bolder",
            "spacing": "Medium"
        },
        {
            "type": "TextBlock",
            "text": "• Executive Summary\n• Methodology\n• ${total_findings} Detailed Findings (${critical_count} Critical, ${high_count} High)\n• Remediation Roadmap\n• Appendices",
            "wrap": true
        }
    ],
    "actions": [
        {
            "type": "Action.OpenUrl",
            "title": "📥 Download Draft",
            "url": "${download_url}"
        },
        {
            "type": "Action.Submit",
            "title": "✅ Approve & Publish",
            "style": "positive",
            "data": {
                "action": "confirm_publish",
                "report_id": "${report_id}"
            }
        },
        {
            "type": "Action.Submit",
            "title": "✏️ Request Changes",
            "data": {
                "action": "request_report_changes",
                "report_id": "${report_id}"
            }
        }
    ]
}
```

### 6.6 Help Card

```json
{
    "type": "AdaptiveCard",
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "version": "1.5",
    "body": [
        {
            "type": "TextBlock",
            "text": "🛡️ VAPT Bot — Command Reference",
            "weight": "Bolder",
            "size": "Large"
        },
        {
            "type": "TextBlock",
            "text": "Scan Operations",
            "weight": "Bolder",
            "spacing": "Medium",
            "color": "Accent"
        },
        {
            "type": "FactSet",
            "facts": [
                { "title": "start scan",    "value": "Start <web|api|infra|code|mobile|all> scan for engagement <ID>" },
                { "title": "scan status",   "value": "Check status for engagement <ID>" },
                { "title": "pause/resume",  "value": "Pause/resume scan job <JOB_ID>" }
            ]
        },
        {
            "type": "TextBlock",
            "text": "Targets & Scope",
            "weight": "Bolder",
            "spacing": "Medium",
            "color": "Accent"
        },
        {
            "type": "FactSet",
            "facts": [
                { "title": "show targets",  "value": "Show targets for engagement <ID>" },
                { "title": "show scope",    "value": "Show scope for engagement <ID>" }
            ]
        },
        {
            "type": "TextBlock",
            "text": "Results & Findings",
            "weight": "Bolder",
            "spacing": "Medium",
            "color": "Accent"
        },
        {
            "type": "FactSet",
            "facts": [
                { "title": "fetch results",    "value": "Fetch <burp|tenable|fortify|mobsf> results for engagement <ID>" },
                { "title": "show findings",     "value": "Show <critical|high|medium|low> findings for engagement <ID>" },
                { "title": "findings summary",  "value": "Findings summary for engagement <ID>" }
            ]
        },
        {
            "type": "TextBlock",
            "text": "Analyst Assignment",
            "weight": "Bolder",
            "spacing": "Medium",
            "color": "Accent"
        },
        {
            "type": "FactSet",
            "facts": [
                { "title": "assign",  "value": "Assign @analyst to engagement <ID>" },
                { "title": "assign validation",  "value": "Assign manual validation for engagement <ID> to @analyst" }
            ]
        },
        {
            "type": "TextBlock",
            "text": "Reports",
            "weight": "Bolder",
            "spacing": "Medium",
            "color": "Accent"
        },
        {
            "type": "FactSet",
            "facts": [
                { "title": "generate",  "value": "Generate <pdf|docx> report for engagement <ID>" },
                { "title": "publish",   "value": "Publish report <REPORT_ID>" }
            ]
        },
        {
            "type": "TextBlock",
            "text": "Notifications",
            "weight": "Bolder",
            "spacing": "Medium",
            "color": "Accent"
        },
        {
            "type": "FactSet",
            "facts": [
                { "title": "subscribe",    "value": "Subscribe to engagement <ID> updates" },
                { "title": "unsubscribe",  "value": "Unsubscribe from engagement <ID>" }
            ]
        }
    ]
}
```

---

## 7. Proactive Notification Engine

### 7.1 Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                     Proactive Notification Engine                      │
│                                                                        │
│  ┌──────────────┐    ┌─────────────────┐    ┌────────────────────┐    │
│  │ Kafka        │    │ Notification    │    │ Teams Delivery     │    │
│  │ Consumer     │───▶│ Router          │───▶│ Service            │    │
│  │              │    │                 │    │                    │    │
│  │ Topics:      │    │ - Filter by    │    │ - ConversationRef  │    │
│  │ scan.status  │    │   subscription │    │   lookup           │    │
│  │ scan.complete│    │ - Severity     │    │ - Card rendering   │    │
│  │ finding.new  │    │   threshold    │    │ - Batch / debounce │    │
│  │ report.ready │    │ - Dedup        │    │ - Rate limiting    │    │
│  │ assignment   │    │ - Throttle     │    │ - Retry with       │    │
│  └──────────────┘    └─────────────────┘    │   backoff          │    │
│                                              └────────────────────┘    │
│                                                        │               │
│                           ┌────────────────────────────┘               │
│                           ▼                                            │
│              ┌─────────────────────────┐                               │
│              │ Subscription Store      │                               │
│              │ (Redis)                 │                               │
│              │                         │                               │
│              │ Key: sub:{user}:{topic} │                               │
│              │ Val: ConversationRef +  │                               │
│              │      preferences        │                               │
│              └─────────────────────────┘                               │
└────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Kafka Consumer Implementation

```typescript
// src/notifications/kafka-notification-consumer.ts

import { Kafka, Consumer, EachMessagePayload } from "kafkajs";

interface NotificationEvent {
    event_type: string;
    engagement_id: number;
    customer_id: number;
    payload: Record<string, unknown>;
    timestamp: string;
    correlation_id: string;
}

interface Subscription {
    userId: string;
    platformUserId: string;
    conversationRef: Partial<ConversationReference>;
    topic: string;
    engagementId?: number;
    preferences: {
        severityThreshold: "critical" | "high" | "medium" | "low" | "all";
        quietHoursStart?: string;  // "22:00" UTC
        quietHoursEnd?: string;    // "08:00" UTC
        batchIntervalMinutes?: number;
    };
    createdAt: string;
}

class KafkaNotificationConsumer {
    private kafka: Kafka;
    private consumer: Consumer;
    private subscriptionStore: SubscriptionStore;
    private teamsDelivery: TeamsDeliveryService;
    private cardEngine: CardTemplateEngine;
    private logger: Logger;

    private readonly TOPICS = [
        "vapt.scan.status-changed",
        "vapt.scan.completed",
        "vapt.finding.created",
        "vapt.finding.critical-alert",
        "vapt.report.generated",
        "vapt.report.published",
        "vapt.assignment.created",
        "vapt.assignment.updated",
    ];

    constructor(
        config: KafkaConfig,
        subscriptionStore: SubscriptionStore,
        teamsDelivery: TeamsDeliveryService,
        cardEngine: CardTemplateEngine,
        logger: Logger,
    ) {
        this.kafka = new Kafka({
            clientId: "vapt-teams-bot",
            brokers: config.brokers,
            ssl: config.ssl,
            sasl: config.sasl,
        });
        this.consumer = this.kafka.consumer({
            groupId: "vapt-teams-notifications",
            sessionTimeout: 30000,
            heartbeatInterval: 10000,
        });
        this.subscriptionStore = subscriptionStore;
        this.teamsDelivery = teamsDelivery;
        this.cardEngine = cardEngine;
        this.logger = logger;
    }

    async start(): Promise<void> {
        await this.consumer.connect();
        await this.consumer.subscribe({
            topics: this.TOPICS,
            fromBeginning: false,
        });

        await this.consumer.run({
            eachMessage: async (payload: EachMessagePayload) => {
                try {
                    await this.handleMessage(payload);
                } catch (error) {
                    this.logger.error("Notification processing error", {
                        topic: payload.topic,
                        error,
                    });
                }
            },
        });

        this.logger.info("Kafka notification consumer started", { topics: this.TOPICS });
    }

    private async handleMessage(payload: EachMessagePayload): Promise<void> {
        const event: NotificationEvent = JSON.parse(payload.message.value!.toString());

        // Route to appropriate handler based on topic
        const handler = this.getHandler(payload.topic);
        if (!handler) return;

        // Find all subscribers for this event
        const subscribers = await this.subscriptionStore.findSubscribers(
            payload.topic,
            event.engagement_id,
            event.customer_id,
        );

        if (subscribers.length === 0) return;

        // Build the notification card
        const card = handler(event);

        // Deliver to each subscriber (with filtering)
        for (const sub of subscribers) {
            if (!this.shouldDeliver(sub, event)) continue;

            await this.teamsDelivery.sendProactiveMessage(
                sub.conversationRef,
                card,
                event.correlation_id,
            );
        }
    }

    private getHandler(topic: string): ((event: NotificationEvent) => AdaptiveCard) | null {
        const handlers: Record<string, (event: NotificationEvent) => AdaptiveCard> = {
            "vapt.scan.status-changed": (e) => this.cardEngine.render("scan_progress", {
                data: e.payload,
                user: {} as PlatformUser,
            }),
            "vapt.scan.completed": (e) => this.cardEngine.render("scan_complete", {
                data: e.payload,
                user: {} as PlatformUser,
            }),
            "vapt.finding.critical-alert": (e) => this.cardEngine.render("finding_alert", {
                data: e.payload,
                user: {} as PlatformUser,
            }),
            "vapt.report.generated": (e) => this.cardEngine.render("report_ready", {
                data: e.payload,
                user: {} as PlatformUser,
            }),
            "vapt.assignment.created": (e) => this.cardEngine.render("assignment_notify", {
                data: e.payload,
                user: {} as PlatformUser,
            }),
        };

        return handlers[topic] || null;
    }

    private shouldDeliver(sub: Subscription, event: NotificationEvent): boolean {
        // Severity threshold check
        const severityOrder = ["critical", "high", "medium", "low", "informational"];
        if (event.payload.severity) {
            const eventIdx = severityOrder.indexOf(event.payload.severity as string);
            const thresholdIdx = severityOrder.indexOf(sub.preferences.severityThreshold);
            if (eventIdx > thresholdIdx) return false;
        }

        // Quiet hours check
        if (sub.preferences.quietHoursStart && sub.preferences.quietHoursEnd) {
            const now = new Date();
            const hour = now.getUTCHours();
            const minute = now.getUTCMinutes();
            const currentTime = `${hour.toString().padStart(2, "0")}:${minute.toString().padStart(2, "0")}`;

            const start = sub.preferences.quietHoursStart;
            const end = sub.preferences.quietHoursEnd;

            // Handle overnight quiet hours (e.g., 22:00 to 08:00)
            if (start > end) {
                if (currentTime >= start || currentTime < end) {
                    // Queue for delivery after quiet hours
                    this.queueForLater(sub, event);
                    return false;
                }
            } else {
                if (currentTime >= start && currentTime < end) {
                    this.queueForLater(sub, event);
                    return false;
                }
            }
        }

        return true;
    }

    private queueForLater(sub: Subscription, event: NotificationEvent): void {
        // Store in Redis sorted set keyed by delivery time
        this.subscriptionStore.queueDeferredNotification(sub, event);
    }

    async stop(): Promise<void> {
        await this.consumer.disconnect();
    }
}
```

### 7.3 Teams Proactive Messaging Service

```typescript
// src/notifications/teams-delivery-service.ts

import {
    BotFrameworkAdapter,
    ConversationReference,
    CardFactory,
    TurnContext,
} from "botbuilder";

class TeamsDeliveryService {
    private adapter: BotFrameworkAdapter;
    private logger: Logger;
    private rateLimiter: RateLimiter;

    // Microsoft Teams rate limits:
    // - 1:1 chats: 1 message per second per conversation
    // - Channels: 2 messages per second per channel
    // - Global: 50 messages per second per bot
    private readonly RATE_LIMITS = {
        perConversation: { tokens: 1, intervalMs: 1000 },
        global: { tokens: 50, intervalMs: 1000 },
    };

    constructor(adapter: BotFrameworkAdapter, logger: Logger) {
        this.adapter = adapter;
        this.logger = logger;
        this.rateLimiter = new TokenBucketRateLimiter(this.RATE_LIMITS);
    }

    async sendProactiveMessage(
        conversationRef: Partial<ConversationReference>,
        card: AdaptiveCard,
        correlationId: string,
    ): Promise<void> {
        // Acquire rate limit token
        await this.rateLimiter.acquire(conversationRef.conversation?.id || "global");

        try {
            await this.adapter.continueConversation(
                conversationRef as ConversationReference,
                async (turnContext: TurnContext) => {
                    await turnContext.sendActivity({
                        attachments: [CardFactory.adaptiveCard(card)],
                    });
                },
            );

            this.logger.info("Proactive message sent", {
                conversationId: conversationRef.conversation?.id,
                correlationId,
            });
        } catch (error: any) {
            if (error.statusCode === 403) {
                // Bot was removed from conversation — clean up subscription
                this.logger.warn("Bot removed from conversation, cleaning up", {
                    conversationId: conversationRef.conversation?.id,
                });
                await this.cleanupSubscription(conversationRef);
            } else if (error.statusCode === 429) {
                // Rate limited by Teams — retry with backoff
                const retryAfter = parseInt(error.headers?.["retry-after"] || "5", 10);
                this.logger.warn("Teams rate limited, retrying", { retryAfter });
                await this.sleep(retryAfter * 1000);
                await this.sendProactiveMessage(conversationRef, card, correlationId);
            } else {
                this.logger.error("Proactive message failed", { error, correlationId });
                throw error;
            }
        }
    }

    async sendBatchNotifications(
        notifications: { ref: Partial<ConversationReference>; card: AdaptiveCard }[],
    ): Promise<void> {
        // Group by conversation to respect per-conversation rate limits
        const byConversation = new Map<string, typeof notifications>();
        for (const n of notifications) {
            const key = n.ref.conversation?.id || "unknown";
            const group = byConversation.get(key) || [];
            group.push(n);
            byConversation.set(key, group);
        }

        // Send in parallel across conversations, sequential within
        const promises = Array.from(byConversation.entries()).map(async ([, group]) => {
            for (const notification of group) {
                await this.sendProactiveMessage(
                    notification.ref,
                    notification.card,
                    `batch-${Date.now()}`,
                );
            }
        });

        await Promise.allSettled(promises);
    }

    private async cleanupSubscription(ref: Partial<ConversationReference>): Promise<void> {
        // Remove all subscriptions for this conversation
        // Implementation delegates to SubscriptionStore
    }

    private sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
```

### 7.4 Subscription Store

```typescript
// src/notifications/subscription-store.ts

import Redis from "ioredis";

class SubscriptionStore {
    private redis: Redis;

    constructor(redis: Redis) {
        this.redis = redis;
    }

    async subscribe(sub: Subscription): Promise<void> {
        const key = `sub:${sub.userId}:${sub.topic}:${sub.engagementId || "all"}`;
        await this.redis.set(key, JSON.stringify(sub), "EX", 86400 * 30); // 30-day TTL

        // Add to topic index for fast lookup
        await this.redis.sadd(`topic:${sub.topic}:${sub.engagementId || "all"}`, key);

        // Add to user index
        await this.redis.sadd(`user_subs:${sub.userId}`, key);
    }

    async unsubscribe(userId: string, topic: string, engagementId?: number): Promise<void> {
        const key = `sub:${userId}:${topic}:${engagementId || "all"}`;
        const data = await this.redis.get(key);
        if (data) {
            await this.redis.del(key);
            await this.redis.srem(`topic:${topic}:${engagementId || "all"}`, key);
            await this.redis.srem(`user_subs:${userId}`, key);
        }
    }

    async findSubscribers(
        topic: string,
        engagementId: number,
        customerId: number,
    ): Promise<Subscription[]> {
        // Look up both engagement-specific and "all" subscriptions
        const specificKeys = await this.redis.smembers(`topic:${topic}:${engagementId}`);
        const globalKeys = await this.redis.smembers(`topic:${topic}:all`);
        const allKeys = [...new Set([...specificKeys, ...globalKeys])];

        if (allKeys.length === 0) return [];

        const values = await this.redis.mget(...allKeys);
        return values
            .filter(Boolean)
            .map(v => JSON.parse(v!) as Subscription);
    }

    async getUserSubscriptions(userId: string): Promise<Subscription[]> {
        const keys = await this.redis.smembers(`user_subs:${userId}`);
        if (keys.length === 0) return [];

        const values = await this.redis.mget(...keys);
        return values
            .filter(Boolean)
            .map(v => JSON.parse(v!) as Subscription);
    }

    async queueDeferredNotification(sub: Subscription, event: NotificationEvent): Promise<void> {
        // Calculate delivery time (end of quiet hours)
        const deliverAt = this.calculateDeliveryTime(sub.preferences.quietHoursEnd!);
        await this.redis.zadd(
            "deferred_notifications",
            deliverAt.getTime(),
            JSON.stringify({ subscription: sub, event }),
        );
    }

    private calculateDeliveryTime(quietHoursEnd: string): Date {
        const [hours, minutes] = quietHoursEnd.split(":").map(Number);
        const now = new Date();
        const delivery = new Date(now);
        delivery.setUTCHours(hours, minutes, 0, 0);
        if (delivery <= now) {
            delivery.setDate(delivery.getDate() + 1);
        }
        return delivery;
    }
}
```

---

## 8. Conversation State Management

### 8.1 State Architecture

```typescript
// src/state/conversation-state.ts

import { ConversationState as BotConversationState, UserState, MemoryStorage, TurnContext } from "botbuilder";
import Redis from "ioredis";

// Redis-backed storage for production
class RedisStorage {
    private redis: Redis;
    private ttlSeconds: number;

    constructor(redis: Redis, ttlSeconds: number = 86400) {
        this.redis = redis;
        this.ttlSeconds = ttlSeconds;
    }

    async read(keys: string[]): Promise<Record<string, any>> {
        if (keys.length === 0) return {};
        const values = await this.redis.mget(...keys);
        const result: Record<string, any> = {};
        keys.forEach((key, i) => {
            if (values[i]) {
                result[key] = JSON.parse(values[i]!);
            }
        });
        return result;
    }

    async write(changes: Record<string, any>): Promise<void> {
        const pipeline = this.redis.pipeline();
        for (const [key, value] of Object.entries(changes)) {
            pipeline.setex(key, this.ttlSeconds, JSON.stringify(value));
        }
        await pipeline.exec();
    }

    async delete(keys: string[]): Promise<void> {
        if (keys.length > 0) {
            await this.redis.del(...keys);
        }
    }
}

// State properties tracked per conversation
interface VAPTConversationData {
    lastCommand?: ParsedCommand;
    activeEngagementId?: number;
    pendingConfirmation?: {
        action: string;
        data: Record<string, unknown>;
        expiresAt: string;
    };
    commandHistory: {
        intent: string;
        timestamp: string;
        success: boolean;
    }[];
    notificationSubscriptions: string[];
}

// State properties tracked per user
interface VAPTUserData {
    platformUserId?: string;
    linkedAt?: string;
    role?: string;
    preferences: {
        defaultEngagementId?: number;
        notificationSeverity: string;
        quietHoursEnabled: boolean;
        timezone?: string;
    };
    recentEngagements: number[];
}

class StateManager {
    private conversationState: BotConversationState;
    private userState: UserState;
    private conversationDataAccessor: StatePropertyAccessor<VAPTConversationData>;
    private userDataAccessor: StatePropertyAccessor<VAPTUserData>;

    constructor(storage: RedisStorage) {
        this.conversationState = new BotConversationState(storage);
        this.userState = new UserState(storage);

        this.conversationDataAccessor = this.conversationState.createProperty<VAPTConversationData>("vaptConversation");
        this.userDataAccessor = this.userState.createProperty<VAPTUserData>("vaptUser");
    }

    async getConversationData(turnContext: TurnContext): Promise<VAPTConversationData> {
        return await this.conversationDataAccessor.get(turnContext, {
            commandHistory: [],
            notificationSubscriptions: [],
        });
    }

    async getUserData(turnContext: TurnContext): Promise<VAPTUserData> {
        return await this.userDataAccessor.get(turnContext, {
            preferences: {
                notificationSeverity: "high",
                quietHoursEnabled: false,
            },
            recentEngagements: [],
        });
    }

    async saveAll(turnContext: TurnContext): Promise<void> {
        await Promise.all([
            this.conversationState.saveChanges(turnContext),
            this.userState.saveChanges(turnContext),
        ]);
    }

    // Track engagement context for follow-up commands
    async updateActiveEngagement(turnContext: TurnContext, engagementId: number): Promise<void> {
        const convData = await this.getConversationData(turnContext);
        convData.activeEngagementId = engagementId;

        const userData = await this.getUserData(turnContext);
        // Update recent engagements (keep last 10)
        userData.recentEngagements = [
            engagementId,
            ...userData.recentEngagements.filter(id => id !== engagementId),
        ].slice(0, 10);
    }

    async recordCommand(turnContext: TurnContext, intent: string, success: boolean): Promise<void> {
        const convData = await this.getConversationData(turnContext);
        convData.commandHistory.push({
            intent,
            timestamp: new Date().toISOString(),
            success,
        });
        // Keep last 50 commands per conversation
        if (convData.commandHistory.length > 50) {
            convData.commandHistory = convData.commandHistory.slice(-50);
        }
    }
}
```

### 8.2 Context-Aware Entity Resolution

```typescript
// src/state/context-resolver.ts

// Resolves implicit entity references using conversation state
class ContextResolver {
    private stateManager: StateManager;

    constructor(stateManager: StateManager) {
        this.stateManager = stateManager;
    }

    async resolveEntities(
        turnContext: TurnContext,
        parsed: ParsedCommand,
    ): Promise<ParsedCommand> {
        const convData = await this.stateManager.getConversationData(turnContext);
        const userData = await this.stateManager.getUserData(turnContext);

        // If engagement_id is missing, try to resolve from context
        if (!parsed.entities.engagement_id) {
            // Check conversation context first
            if (convData.activeEngagementId) {
                parsed.entities.engagement_id = convData.activeEngagementId;
                parsed.entities._resolved_from = "conversation_context";
            }
            // Then check user's default
            else if (userData.preferences.defaultEngagementId) {
                parsed.entities.engagement_id = userData.preferences.defaultEngagementId;
                parsed.entities._resolved_from = "user_default";
            }
        }

        // Resolve "it" / "that" / "the scan" references
        if (parsed.entities._reference === "last") {
            const lastCommand = convData.lastCommand;
            if (lastCommand) {
                // Carry forward entities from last command
                for (const [key, value] of Object.entries(lastCommand.entities)) {
                    if (!parsed.entities[key] && key !== "_reference") {
                        parsed.entities[key] = value;
                    }
                }
            }
        }

        return parsed;
    }
}
```

---

## 9. Main Bot Application

### 9.1 Bot Entry Point

```typescript
// src/bot/vapt-bot.ts

import {
    ActivityHandler,
    TurnContext,
    TeamsActivityHandler,
    CardFactory,
    MessageFactory,
} from "botbuilder";

class VAPTTeamsBot extends TeamsActivityHandler {
    private commandParser: CommandParsingPipeline;
    private handlerRegistry: CommandHandlerRegistry;
    private actionHandler: ActionSubmitHandler;
    private mcpClient: MCPClientAdapter;
    private stateManager: StateManager;
    private contextResolver: ContextResolver;
    private identityResolver: IdentityResolver;
    private logger: Logger;

    constructor(
        mcpClient: MCPClientAdapter,
        stateManager: StateManager,
        logger: Logger,
    ) {
        super();
        this.mcpClient = mcpClient;
        this.stateManager = stateManager;
        this.contextResolver = new ContextResolver(stateManager);
        this.identityResolver = new IdentityResolver();
        this.commandParser = new CommandParsingPipeline();
        this.handlerRegistry = new CommandHandlerRegistry();
        this.actionHandler = new ActionSubmitHandler(this.handlerRegistry, mcpClient);
        this.logger = logger;
    }

    // ── Message Handler ───────────────────────────────────────────

    async onMessage(turnContext: TurnContext): Promise<void> {
        const text = turnContext.activity.text?.trim();
        if (!text) return;

        // Remove bot @mention from text
        const cleanText = TurnContext.removeRecipientMention(turnContext.activity);

        try {
            // Step 1: Resolve platform identity
            const user = await this.identityResolver.resolve(turnContext);
            if (!user) {
                await this.sendLinkAccountCard(turnContext);
                return;
            }

            // Step 2: Parse command
            let parsed = await this.commandParser.parse(cleanText || text);

            // Step 3: Resolve entities from context
            parsed = await this.contextResolver.resolveEntities(turnContext, parsed);

            // Step 4: Handle clarification needed
            if (parsed.intent === "clarification_needed") {
                await turnContext.sendActivity(parsed.clarificationQuestion!);
                return;
            }

            // Step 5: Update state context
            if (parsed.entities.engagement_id) {
                await this.stateManager.updateActiveEngagement(
                    turnContext,
                    parsed.entities.engagement_id as number,
                );
            }

            // Step 6: Dispatch to handler
            const result = await this.handlerRegistry.dispatch({
                turnContext,
                parsedCommand: parsed,
                user,
                mcpClient: this.mcpClient,
                conversationState: await this.stateManager.getConversationData(turnContext),
                logger: this.logger,
            });

            // Step 7: Send response
            if (result.card) {
                await turnContext.sendActivity({
                    attachments: [CardFactory.adaptiveCard(result.card)],
                });
            } else if (result.text) {
                await turnContext.sendActivity(MessageFactory.text(result.text));
            }

            // Step 8: Handle update subscriptions
            if (result.subscribeToUpdates) {
                // Auto-subscribe for status updates
                const subStore = new SubscriptionStore(this.redis);
                await subStore.subscribe({
                    userId: user.id,
                    platformUserId: user.id,
                    conversationRef: result.subscribeToUpdates.conversationRef,
                    topic: result.subscribeToUpdates.topic,
                    engagementId: parsed.entities.engagement_id as number,
                    preferences: {
                        severityThreshold: "all",
                    },
                    createdAt: new Date().toISOString(),
                });
            }

            // Step 9: Record command and save state
            await this.stateManager.recordCommand(turnContext, parsed.intent, true);
            await this.stateManager.saveAll(turnContext);

        } catch (error) {
            this.logger.error("Message handling error", { error, text });
            await this.stateManager.recordCommand(turnContext, "error", false);
            await this.stateManager.saveAll(turnContext);

            await turnContext.sendActivity(
                "An unexpected error occurred. Our team has been notified. Please try again.",
            );
        }
    }

    // ── Adaptive Card Submit Handler ──────────────────────────────

    async onAdaptiveCardInvoke(turnContext: TurnContext): Promise<any> {
        const user = await this.identityResolver.resolve(turnContext);
        if (!user) {
            return { statusCode: 401, type: "application/vnd.microsoft.error" };
        }

        await this.actionHandler.handleSubmitAction(turnContext, user);
        return { statusCode: 200, type: "application/vnd.microsoft.activity.message" };
    }

    // ── Member Events ─────────────────────────────────────────────

    async onMembersAdded(turnContext: TurnContext): Promise<void> {
        for (const member of turnContext.activity.membersAdded || []) {
            if (member.id !== turnContext.activity.recipient.id) {
                await turnContext.sendActivity(
                    "👋 Welcome to the **VAPT Security Bot**! I help manage vulnerability assessments.\n\n"
                    + "Type **help** to see available commands, or start with:\n"
                    + "• `show targets for engagement <ID>`\n"
                    + "• `start scan for engagement <ID>`\n"
                    + "• `check status for engagement <ID>`",
                );
            }
        }
    }

    // ── Account Linking ───────────────────────────────────────────

    private async sendLinkAccountCard(turnContext: TurnContext): Promise<void> {
        const card: AdaptiveCard = {
            type: "AdaptiveCard",
            version: "1.5",
            body: [
                {
                    type: "TextBlock",
                    text: "🔐 Account Not Linked",
                    weight: "Bolder",
                    size: "Large",
                },
                {
                    type: "TextBlock",
                    text: "Your Teams account is not linked to the VAPT platform. "
                        + "Please click below to authenticate and link your account.",
                    wrap: true,
                },
            ],
            actions: [
                {
                    type: "Action.OpenUrl",
                    title: "🔗 Link Account",
                    url: `${process.env.AUTH_URL}/link?provider=teams&redirect=${encodeURIComponent(process.env.BOT_REDIRECT_URL!)}`,
                },
            ],
        };

        await turnContext.sendActivity({
            attachments: [CardFactory.adaptiveCard(card)],
        });
    }
}
```

---

## 10. Deployment Configuration

### 10.1 Kubernetes Deployment

```yaml
# k8s/teams-bot/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vapt-teams-bot
  namespace: vapt-platform
  labels:
    app: vapt-teams-bot
    component: teams-bot
    part-of: vapt-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vapt-teams-bot
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: vapt-teams-bot
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: vapt-teams-bot
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: teams-bot
          image: registry.vapt-platform.internal/vapt-teams-bot:1.0.0
          ports:
            - name: http
              containerPort: 3978
              protocol: TCP
            - name: metrics
              containerPort: 9090
              protocol: TCP
          env:
            - name: NODE_ENV
              value: "production"
            - name: PORT
              value: "3978"
            - name: MCP_SERVER_URL
              value: "http://vapt-mcp-server.vapt-platform.svc.cluster.local:8080"
            - name: MCP_SSE_ENDPOINT
              value: "/sse"
            - name: MCP_MESSAGES_ENDPOINT
              value: "/messages"
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: vapt-teams-bot-secrets
                  key: redis-url
            - name: KAFKA_BROKERS
              value: "kafka-0.kafka.vapt-platform.svc.cluster.local:9092,kafka-1.kafka.vapt-platform.svc.cluster.local:9092,kafka-2.kafka.vapt-platform.svc.cluster.local:9092"
            - name: MICROSOFT_APP_ID
              valueFrom:
                secretKeyRef:
                  name: vapt-teams-bot-secrets
                  key: microsoft-app-id
            - name: MICROSOFT_APP_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: vapt-teams-bot-secrets
                  key: microsoft-app-password
            - name: KEYCLOAK_URL
              value: "http://keycloak.vapt-platform.svc.cluster.local:8080"
            - name: KEYCLOAK_REALM
              value: "vapt"
            - name: CLAUDE_API_KEY
              valueFrom:
                secretKeyRef:
                  name: vapt-teams-bot-secrets
                  key: claude-api-key
            - name: PORTAL_URL
              value: "https://portal.vapt-platform.com"
            - name: AUTH_URL
              value: "https://auth.vapt-platform.com"
            - name: LOG_LEVEL
              value: "info"
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
              port: http
            initialDelaySeconds: 10
            periodSeconds: 30
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health/ready
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
          startupProbe:
            httpGet:
              path: /health/startup
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 12
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir: {}
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: vapt-teams-bot
---
# k8s/teams-bot/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: vapt-teams-bot
  namespace: vapt-platform
spec:
  selector:
    app: vapt-teams-bot
  ports:
    - name: http
      port: 3978
      targetPort: http
      protocol: TCP
    - name: metrics
      port: 9090
      targetPort: metrics
      protocol: TCP
  type: ClusterIP
---
# k8s/teams-bot/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: vapt-teams-bot
  namespace: vapt-platform
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - teams-bot.vapt-platform.com
      secretName: vapt-teams-bot-tls
  rules:
    - host: teams-bot.vapt-platform.com
      http:
        paths:
          - path: /api/messages
            pathType: Prefix
            backend:
              service:
                name: vapt-teams-bot
                port:
                  number: 3978
---
# k8s/teams-bot/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vapt-teams-bot
  namespace: vapt-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vapt-teams-bot
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "100"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
```

### 10.2 Health Check Endpoints

```typescript
// src/health/health-controller.ts

import express from "express";

class HealthController {
    private mcpClient: MCPClientAdapter;
    private redis: Redis;
    private kafkaConsumer: KafkaNotificationConsumer;

    constructor(
        mcpClient: MCPClientAdapter,
        redis: Redis,
        kafkaConsumer: KafkaNotificationConsumer,
    ) {
        this.mcpClient = mcpClient;
        this.redis = redis;
        this.kafkaConsumer = kafkaConsumer;
    }

    register(app: express.Application): void {
        // Startup probe — true once bot is initialised
        app.get("/health/startup", (req, res) => {
            if (this.mcpClient.isConnected()) {
                res.status(200).json({ status: "started" });
            } else {
                res.status(503).json({ status: "starting" });
            }
        });

        // Liveness probe — true if process is healthy
        app.get("/health/live", (req, res) => {
            res.status(200).json({
                status: "alive",
                uptime: process.uptime(),
                memoryUsage: process.memoryUsage().rss,
            });
        });

        // Readiness probe — true if all dependencies are available
        app.get("/health/ready", async (req, res) => {
            const checks = await Promise.allSettled([
                this.checkMCP(),
                this.checkRedis(),
                this.checkKafka(),
            ]);

            const results = {
                mcp:   checks[0].status === "fulfilled" ? "ok" : "down",
                redis: checks[1].status === "fulfilled" ? "ok" : "down",
                kafka: checks[2].status === "fulfilled" ? "ok" : "down",
            };

            const allHealthy = Object.values(results).every(v => v === "ok");

            res.status(allHealthy ? 200 : 503).json({
                status: allHealthy ? "ready" : "degraded",
                checks: results,
            });
        });
    }

    private async checkMCP(): Promise<void> {
        if (!this.mcpClient.isConnected()) {
            throw new Error("MCP not connected");
        }
    }

    private async checkRedis(): Promise<void> {
        await this.redis.ping();
    }

    private async checkKafka(): Promise<void> {
        // Verify consumer is connected and consuming
        if (!this.kafkaConsumer.isRunning()) {
            throw new Error("Kafka consumer not running");
        }
    }
}
```

### 10.3 Observability

```typescript
// src/observability/metrics.ts

import { Registry, Counter, Histogram, Gauge } from "prom-client";

const register = new Registry();

// Command metrics
const commandsTotal = new Counter({
    name: "vapt_bot_commands_total",
    help: "Total commands processed",
    labelNames: ["intent", "source", "status"],
    registers: [register],
});

const commandDuration = new Histogram({
    name: "vapt_bot_command_duration_seconds",
    help: "Command processing duration",
    labelNames: ["intent"],
    buckets: [0.1, 0.25, 0.5, 1, 2.5, 5, 10],
    registers: [register],
});

// MCP metrics
const mcpCallsTotal = new Counter({
    name: "vapt_bot_mcp_calls_total",
    help: "Total MCP tool/resource calls",
    labelNames: ["method", "tool_or_resource", "status"],
    registers: [register],
});

const mcpCallDuration = new Histogram({
    name: "vapt_bot_mcp_call_duration_seconds",
    help: "MCP call duration",
    labelNames: ["method", "tool_or_resource"],
    buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30],
    registers: [register],
});

// Notification metrics
const notificationsSent = new Counter({
    name: "vapt_bot_notifications_sent_total",
    help: "Total proactive notifications sent",
    labelNames: ["topic", "status"],
    registers: [register],
});

// Connection metrics
const activeConnections = new Gauge({
    name: "vapt_bot_active_connections",
    help: "Active SSE connections to MCP server",
    registers: [register],
});

const activeSubscriptions = new Gauge({
    name: "vapt_bot_active_subscriptions",
    help: "Active notification subscriptions",
    labelNames: ["topic"],
    registers: [register],
});

// Identity resolution metrics
const identityResolutions = new Counter({
    name: "vapt_bot_identity_resolutions_total",
    help: "Identity resolution attempts",
    labelNames: ["status"],  // success, not_linked, error
    registers: [register],
});

// LLM fallback metrics
const llmFallbacks = new Counter({
    name: "vapt_bot_llm_fallbacks_total",
    help: "Commands that required LLM classification",
    labelNames: ["result"],  // parsed, clarification, error
    registers: [register],
});

export {
    register,
    commandsTotal,
    commandDuration,
    mcpCallsTotal,
    mcpCallDuration,
    notificationsSent,
    activeConnections,
    activeSubscriptions,
    identityResolutions,
    llmFallbacks,
};
```

### 10.4 Prometheus Alerting Rules

```yaml
# monitoring/teams-bot-alerts.yaml
groups:
  - name: vapt-teams-bot
    rules:
      - alert: TeamsBotHighErrorRate
        expr: |
          rate(vapt_bot_commands_total{status="error"}[5m])
          / rate(vapt_bot_commands_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Teams bot error rate above 5%"

      - alert: TeamsBotMCPDisconnected
        expr: vapt_bot_active_connections == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Teams bot lost MCP server connection"

      - alert: TeamsBotHighLatency
        expr: |
          histogram_quantile(0.95, rate(vapt_bot_command_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Teams bot p95 command latency above 5 seconds"

      - alert: TeamsBotNotificationBacklog
        expr: |
          rate(vapt_bot_notifications_sent_total{status="error"}[5m]) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Teams bot notification delivery failures"

      - alert: TeamsBotHighLLMFallbackRate
        expr: |
          rate(vapt_bot_llm_fallbacks_total[5m])
          / rate(vapt_bot_commands_total[5m]) > 0.3
        for: 15m
        labels:
          severity: info
        annotations:
          summary: "Over 30% of commands require LLM fallback — consider adding regex patterns"
```

---

## 11. End-to-End Command Flow Summary

```
User types: "Start web scan for engagement 102"
│
├─1─▶ Teams Client → Azure Bot Service → POST /api/messages
│
├─2─▶ VAPTTeamsBot.onMessage()
│     ├── IdentityResolver: aadObjectId → teams_user_mappings → platform user
│     ├── RBAC check: user.role ∈ {platform_admin, lead_analyst, analyst, scanner_operator}
│     │
│     ├── CommandParsingPipeline.parse("Start web scan for engagement 102")
│     │   ├── Preprocessor: normalise → "start web scan for engagement 102"
│     │   ├── RegexMatcher: MATCH /^start\s+(web|api|infra|code|mobile|all)\s+scan/i
│     │   │   └── intent: "start_scan", entities: { scan_type: "web", engagement_id: 102 }
│     │   └── confidence: 0.95, source: "regex"
│     │
│     ├── ContextResolver: engagement_id=102 present, no resolution needed
│     │
│     └── HandlerRegistry.dispatch() → StartScanHandler
│
├─3─▶ StartScanHandler.execute()
│     ├── MCP Resource Read:  vapt://engagements/102/scope     → EngagementScope
│     ├── MCP Resource Read:  vapt://engagements/102/targets   → TargetList
│     ├── resolveScanTools("web", targets) → [{ name: "start_burp_scan", targetIds: [5,6] }]
│     │
│     ├── Confirmation required → buildConfirmationCard()
│     └── ← AdaptiveCard: "Confirm Scan Initiation" with ✅/❌ buttons
│
├─4─▶ User clicks "✅ Confirm & Start"
│     ├── ActionSubmitHandler.handleConfirmScan()
│     │   └── MCP Tool Call: start_burp_scan({ engagement_id: 102, target_ids: [5,6] })
│     │       └── JSON-RPC 2.0 → MCP Server → Scan Orchestration → Temporal Workflow
│     │
│     └── ← AdaptiveCard: "✅ Scans Initiated" (Job ID, status=queued)
│         + Auto-subscribe to scan.status updates for engagement:102
│
├─5─▶ [Async] Kafka: vapt.scan.status-changed { job_id, progress: 45% }
│     ├── KafkaNotificationConsumer receives event
│     ├── SubscriptionStore.findSubscribers("vapt.scan.status-changed", 102)
│     ├── CardTemplateEngine.render("scan_progress", { progress: 45% })
│     └── TeamsDeliveryService.sendProactiveMessage() → Scan Progress Card
│
├─6─▶ [Async] Kafka: vapt.scan.completed { job_id, findings: [...] }
│     ├── KafkaNotificationConsumer receives event
│     ├── CardTemplateEngine.render("scan_complete", { critical: 2, high: 5 })
│     └── TeamsDeliveryService.sendProactiveMessage() → Scan Complete Card
│         with action buttons: View Results | Assign Analyst | Generate Report
│
└─7─▶ [Async] Kafka: vapt.finding.critical-alert { finding_id, cvss: 9.8 }
      ├── Severity check: "critical" ≥ subscriber threshold "all" → DELIVER
      ├── CardTemplateEngine.render("finding_alert", { ... })
      └── TeamsDeliveryService.sendProactiveMessage() → Critical Finding Alert Card
          with action buttons: Confirm | False Positive | View Details | Open Portal
```

---

*This document is part of the VAPT Orchestration Platform architecture. See also: [ARCHITECTURE.md](./ARCHITECTURE.md), [MICROSERVICES.md](./MICROSERVICES.md), [DATABASE_SCHEMA.sql](./DATABASE_SCHEMA.sql), [MCP_SERVER.md](./MCP_SERVER.md), [SCAN_ORCHESTRATION_WORKFLOWS.md](./SCAN_ORCHESTRATION_WORKFLOWS.md).*
