# Analyst Workbench UI Design

## Overview

The Analyst Workbench is the primary interface where VAPT analysts perform manual validation of automated scan findings. It provides a unified workspace for triaging findings, recording proof-of-concept exploits, updating risk severity, and authoring remediation guidance.

---

## 1. UI Wireframes

### 1.1 Main Workbench Layout (Split-Panel)

```
+------------------------------------------------------------------+
| [Logo] Analyst Workbench    [Engagement: ACME-2026-Q1]  [A] [?]  |
+----------+-------------------------------------------------------+
|          |  Scan Results Dashboard                                |
| SIDEBAR  |  +----------+ +----------+ +----------+ +----------+  |
|          |  | Critical | | High     | | Medium   | | Low      |  |
| Engage-  |  |    12    | |    47    | |   128    | |    89    |  |
| ments    |  +----------+ +----------+ +----------+ +----------+  |
|          |                                                        |
| Recent   |  Scan Coverage        Findings by Scanner              |
| --------+|  +--------------+    +------------------------+       |
| ACME Q1  |  | ████████ 92% |    | Burp Suite    ▓▓▓  45 |       |
| Beta Inc |  | Web App      |    | Nuclei        ▓▓   38 |       |
| Corp X   |  | ████░░░░ 47% |    | Fortify       ▓▓   31 |       |
|          |  | API          |    | Tenable       ▓    22 |       |
| Filters  |  +--------------+    +------------------------+       |
| --------+|                                                        |
| Status   |  Recent Activity                                       |
| Scanner  |  +--------------------------------------------------+ |
| Severity |  | 10:32 Finding #247 validated as True Positive     | |
| Assignee |  | 10:28 PoC recorded for SQL Injection #189         | |
|          |  | 10:15 Severity upgraded: #312 Medium → High       | |
|          |  +--------------------------------------------------+ |
+----------+-------------------------------------------------------+
```

### 1.2 Finding Triage Queue

```
+------------------------------------------------------------------+
| Finding Triage                    [Bulk Actions ▼] [AI Assist ▼]  |
+------------------------------------------------------------------+
| [x] Select All  | Sort: AI Priority ▼ | Group: Category ▼        |
+------------------------------------------------------------------+
| □ CRIT #247  SQL Injection - Login Endpoint                       |
|   Burp Suite | ACME Corp | Web App | CVSS 9.8 | AI: 97% TP      |
|   ┌─ Suggested: True Positive (AI Confidence: High)              |
|   └─ Similar to: #189, #203 (cluster)                            |
+------------------------------------------------------------------+
| ■ HIGH #312  XSS Reflected - Search Parameter                    |
|   Nuclei | ACME Corp | Web App | CVSS 7.4 | AI: 89% TP          |
|   ┌─ Status: In Review (analyst: jsmith)                         |
|   └─ Notes: 2 | PoC: 1                                          |
+------------------------------------------------------------------+
| □ HIGH #318  Insecure Direct Object Reference                    |
|   Burp Suite | ACME Corp | API | CVSS 7.5 | AI: 82% TP          |
|   ┌─ Suggested: True Positive                                    |
|   └─ Attack chain: #318 → #247 (escalation path)                |
+------------------------------------------------------------------+
| □ MED  #401  Missing Security Headers                            |
|   Nuclei | ACME Corp | Web App | CVSS 5.3 | AI: 95% TP          |
|   ┌─ Suggested: True Positive                                    |
|   └─ Remediation template available                              |
+------------------------------------------------------------------+
| □ LOW  #455  Information Disclosure - Server Version              |
|   Nmap | ACME Corp | Infra | CVSS 3.1 | AI: 72% FP              |
|   ┌─ Suggested: False Positive (version mismatch)                |
|   └─ AI Reason: Banner spoofing detected                        |
+------------------------------------------------------------------+
| Showing 1-20 of 276  [< Prev] [1] [2] [3] ... [14] [Next >]     |
+------------------------------------------------------------------+
```

### 1.3 Finding Detail Panel (Right Drawer / Full Page)

```
+------------------------------------------------------------------+
| ← Back to Triage    Finding #247: SQL Injection - Login Endpoint  |
+------------------------------------------------------------------+
| TABS: [Details] [Validation] [PoC] [Remediation] [History]       |
+------------------------------------------------------------------+
|                                                                    |
|  ┌─ DETAILS TAB ─────────────────────────────────────────────┐   |
|  │                                                            │   |
|  │  Status: ● Under Review          Assignee: jsmith         │   |
|  │  Severity: [CRITICAL ▼]          CVSS: 9.8 (AV:N/AC:L)   │   |
|  │  Category: CWE-89 SQL Injection  Scanner: Burp Suite      │   |
|  │  Asset: login.acmecorp.com        Endpoint: POST /auth    │   |
|  │                                                            │   |
|  │  Description                                               │   |
|  │  ┌──────────────────────────────────────────────────────┐ │   |
|  │  │ SQL injection vulnerability detected in the login    │ │   |
|  │  │ endpoint. The 'username' parameter is concatenated   │ │   |
|  │  │ directly into a SQL query without parameterization.  │ │   |
|  │  │ An attacker can extract the entire database.         │ │   |
|  │  └──────────────────────────────────────────────────────┘ │   |
|  │                                                            │   |
|  │  Evidence (from scanner)                                   │   |
|  │  ┌──────────────────────────────────────────────────────┐ │   |
|  │  │ Request:                                             │ │   |
|  │  │ POST /api/auth/login HTTP/1.1                        │ │   |
|  │  │ Content-Type: application/json                       │ │   |
|  │  │ {"username": "admin' OR '1'='1", "password": "x"}   │ │   |
|  │  │                                                      │ │   |
|  │  │ Response:                                            │ │   |
|  │  │ HTTP/1.1 200 OK                                     │ │   |
|  │  │ {"token": "eyJhbG...", "user": "admin"}             │ │   |
|  │  └──────────────────────────────────────────────────────┘ │   |
|  │                                                            │   |
|  │  AI Analysis                                               │   |
|  │  ┌──────────────────────────────────────────────────────┐ │   |
|  │  │ Confidence: 97% True Positive                        │ │   |
|  │  │ Exploitability: HIGH - No authentication required    │ │   |
|  │  │ Business Impact: CRITICAL - Full DB access           │ │   |
|  │  │ Attack Chains: Links to #318 (IDOR) for escalation  │ │   |
|  │  └──────────────────────────────────────────────────────┘ │   |
|  └────────────────────────────────────────────────────────────┘   |
|                                                                    |
+------------------------------------------------------------------+
```

### 1.4 Validation & Notes Tab

```
+------------------------------------------------------------------+
| VALIDATION TAB                                                     |
+------------------------------------------------------------------+
|                                                                    |
|  Validation Verdict                                                |
|  ┌──────────────────────────────────────────────────────────────┐ |
|  │  ( ) True Positive    ( ) False Positive    ( ) Duplicate   │ |
|  │  ( ) Requires Retest  ( ) Not Applicable    ( ) Informational│|
|  └──────────────────────────────────────────────────────────────┘ |
|                                                                    |
|  Validation Checklist (OWASP WSTG-INPV-05)                       |
|  ┌──────────────────────────────────────────────────────────────┐ |
|  │  [x] Identify injection points                              │ |
|  │  [x] Test with basic SQL syntax                             │ |
|  │  [x] Test with time-based blind payloads                    │ |
|  │  [ ] Test with UNION-based payloads                         │ |
|  │  [ ] Test with out-of-band (OOB) techniques                │ |
|  │  [x] Verify data extraction capability                      │ |
|  │  [ ] Test WAF/filter bypass techniques                      │ |
|  └──────────────────────────────────────────────────────────────┘ |
|                                                                    |
|  Analyst Notes                                                     |
|  ┌──────────────────────────────────────────────────────────────┐ |
|  │  + Add Note                                                  │ |
|  │                                                              │ |
|  │  ┌────────────────────────────────────────────────────────┐ │ |
|  │  │ jsmith - 2026-03-15 10:32                              │ │ |
|  │  │ Confirmed SQL injection via time-based blind.          │ │ |
|  │  │ MySQL 8.0 backend. Extracted 3 tables. Auth bypass     │ │ |
|  │  │ confirmed. WAF does not filter SLEEP() function.       │ │ |
|  │  │ [Screenshot: auth_bypass_evidence.png]                 │ │ |
|  │  └────────────────────────────────────────────────────────┘ │ |
|  │                                                              │ |
|  │  ┌────────────────────────────────────────────────────────┐ │ |
|  │  │ agarcia - 2026-03-15 09:15                             │ │ |
|  │  │ Initial triage: AI flagged as TP. Scanner evidence     │ │ |
|  │  │ looks solid. Assigning to jsmith for manual validation.│ │ |
|  │  └────────────────────────────────────────────────────────┘ │ |
|  └──────────────────────────────────────────────────────────────┘ |
|                                                                    |
+------------------------------------------------------------------+
```

### 1.5 Proof-of-Concept (PoC) Recorder

```
+------------------------------------------------------------------+
| PROOF OF CONCEPT TAB                                               |
+------------------------------------------------------------------+
|                                                                    |
|  PoC Steps                               [+ Add Step] [Record ●] |
|  ┌──────────────────────────────────────────────────────────────┐ |
|  │  Step 1: Authentication Bypass                               │ |
|  │  ┌────────────────────────────────────────────────────────┐ │ |
|  │  │ Request                          │ Response             │ │ |
|  │  │ POST /api/auth/login HTTP/1.1    │ HTTP/1.1 200 OK     │ │ |
|  │  │ Host: login.acmecorp.com         │ Content-Type: json  │ │ |
|  │  │ Content-Type: application/json   │                     │ │ |
|  │  │                                  │ {"token":"eyJ..."}  │ │ |
|  │  │ {"username":"admin' OR 1=1--",   │                     │ │ |
|  │  │  "password":"anything"}          │                     │ │ |
|  │  └────────────────────────────────────────────────────────┘ │ |
|  │  Annotations: Auth bypassed using classic OR payload        │ |
|  │  [Screenshot ▼] [Edit] [Delete]                             │ |
|  │                                                              │ |
|  │  Step 2: Data Extraction                                    │ |
|  │  ┌────────────────────────────────────────────────────────┐ │ |
|  │  │ Request                          │ Response             │ │ |
|  │  │ POST /api/auth/login HTTP/1.1    │ HTTP/1.1 200 OK     │ │ |
|  │  │                                  │                     │ │ |
|  │  │ {"username":"' UNION SELECT      │ {"users": [         │ │ |
|  │  │   table_name FROM               │   "users",          │ │ |
|  │  │   information_schema.tables--", │   "orders",         │ │ |
|  │  │  "password":"x"}                │   "payments"]}      │ │ |
|  │  └────────────────────────────────────────────────────────┘ │ |
|  │  Annotations: Extracted table names via UNION injection     │ |
|  │  [Screenshot ▼] [Edit] [Delete]                             │ |
|  └──────────────────────────────────────────────────────────────┘ |
|                                                                    |
|  PoC Environment                                                   |
|  ┌──────────────────────────────────────────────────────────────┐ |
|  │ Target: login.acmecorp.com:443    Tool: Burp Suite Pro      │ |
|  │ Date: 2026-03-15                  Analyst: jsmith            │ |
|  │ Network: VPN (ACME-PENTEST)       Scope: Authorized         │ |
|  └──────────────────────────────────────────────────────────────┘ |
|                                                                    |
|  [Export PoC as PDF] [Attach to Report] [Share with Team]         |
+------------------------------------------------------------------+
```

### 1.6 Remediation Guidance Panel

```
+------------------------------------------------------------------+
| REMEDIATION TAB                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  AI-Generated Remediation          [Regenerate] [Edit] [Approve] |
|  ┌──────────────────────────────────────────────────────────────┐ |
|  │  Summary                                                     │ |
|  │  Replace string concatenation in SQL queries with            │ |
|  │  parameterized queries (prepared statements). Implement      │ |
|  │  input validation as defense-in-depth.                       │ |
|  │                                                              │ |
|  │  Detailed Steps                                              │ |
|  │  1. Replace raw SQL in /src/auth/loginHandler.java:42       │ |
|  │     with PreparedStatement                                   │ |
|  │  2. Add input validation for username (alphanumeric only)   │ |
|  │  3. Implement WAF rule for SQL injection patterns            │ |
|  │  4. Enable parameterized query audit logging                 │ |
|  │                                                              │ |
|  │  Code Example                                                │ |
|  │  ┌──────────────────────────────────────────────────────┐   │ |
|  │  │ // BEFORE (vulnerable)                               │   │ |
|  │  │ String q = "SELECT * FROM users WHERE                │   │ |
|  │  │   username='" + input + "'";                         │   │ |
|  │  │                                                      │   │ |
|  │  │ // AFTER (secure)                                    │   │ |
|  │  │ PreparedStatement ps = conn.prepareStatement(        │   │ |
|  │  │   "SELECT * FROM users WHERE username = ?");         │   │ |
|  │  │ ps.setString(1, input);                              │   │ |
|  │  └──────────────────────────────────────────────────────┘   │ |
|  │                                                              │ |
|  │  References                                                  │ |
|  │  • OWASP SQL Injection Prevention Cheat Sheet              │ |
|  │  • CWE-89: SQL Injection                                   │ |
|  │  • ASVS V5.3: Output Encoding & Injection Prevention       │ |
|  └──────────────────────────────────────────────────────────────┘ |
|                                                                    |
|  Severity Override                                                 |
|  ┌──────────────────────────────────────────────────────────────┐ |
|  │  Scanner Severity: Critical (CVSS 9.8)                      │ |
|  │  AI Adjusted:      Critical (CVSS 9.8) - No change          │ |
|  │  Analyst Override:  [Critical ▼]  CVSS: [9.8]               │ |
|  │  Justification:    [                                    ]   │ |
|  │                                                              │ |
|  │  Context Factors                                             │ |
|  │  [x] Internet-facing     [ ] Compensating controls          │ |
|  │  [x] Auth not required   [ ] Limited data exposure          │ |
|  │  [x] PII/sensitive data  [ ] Rate limiting in place         │ |
|  └──────────────────────────────────────────────────────────────┘ |
|                                                                    |
+------------------------------------------------------------------+
```

---

## 2. Frontend Architecture

### 2.1 Technology Stack

| Layer              | Technology                | Purpose                          |
|--------------------|---------------------------|----------------------------------|
| Framework          | Next.js 14 (App Router)   | SSR, routing, API routes         |
| Language           | TypeScript 5.5+           | Type safety                      |
| State Management   | Zustand                   | Lightweight global state         |
| Server State       | TanStack Query v5         | API cache, mutations, pagination |
| Real-time          | WebSocket + Yjs           | Live updates, CRDT collaboration |
| UI Components      | Radix UI + Tailwind CSS   | Accessible primitives + utility  |
| Charts             | Recharts                  | Dashboard visualizations         |
| Tables             | TanStack Table v8         | Sortable, filterable data grids  |
| Forms              | React Hook Form + Zod     | Form state + schema validation   |
| HTTP Client        | ky                        | Fetch-based API client           |
| Code Highlighting  | Shiki                     | HTTP request/response rendering  |
| Rich Text          | TipTap                    | Analyst notes editor             |
| Drag & Drop        | dnd-kit                   | PoC step reordering              |
| Testing            | Vitest + Testing Library  | Unit/integration tests           |
| E2E Testing        | Playwright                | End-to-end testing               |

### 2.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js App Router                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    Layouts                             │  │
│  │  RootLayout → AuthLayout → WorkbenchLayout            │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    Pages                               │  │
│  │  /workbench           → Dashboard (scan results)      │  │
│  │  /workbench/triage    → Finding triage queue          │  │
│  │  /workbench/[id]      → Finding detail view           │  │
│  │  /workbench/[id]/poc  → PoC recorder                  │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │               State Management                         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │  │
│  │  │ Zustand   │  │ TanStack │  │ WebSocket/Yjs    │    │  │
│  │  │ UI State  │  │ Query    │  │ Real-time State  │    │  │
│  │  │ Filters   │  │ Server   │  │ Collaboration    │    │  │
│  │  │ Selection │  │ Cache    │  │ Notifications    │    │  │
│  │  └──────────┘  └──────────┘  └──────────────────┘    │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │               Service Layer                            │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │  │
│  │  │ API      │  │ WS       │  │ Auth             │    │  │
│  │  │ Client   │  │ Manager  │  │ Service          │    │  │
│  │  │ (ky)     │  │          │  │ (OIDC/Keycloak)  │    │  │
│  │  └──────────┘  └──────────┘  └──────────────────┘    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                    API Gateway
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
  Findings Service  Analyst Workbench  AI Analysis
    (Python)         Service (Go)     Engine (Python)
```

### 2.3 Directory Structure

```
frontend/analyst-portal/
├── package.json
├── tsconfig.json
├── next.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── .env.example
├── public/
│   └── icons/
├── src/
│   ├── app/
│   │   ├── layout.tsx                    # Root layout (providers)
│   │   ├── page.tsx                      # Redirect to /workbench
│   │   ├── globals.css                   # Tailwind base styles
│   │   └── workbench/
│   │       ├── layout.tsx                # Workbench shell (sidebar)
│   │       ├── page.tsx                  # Dashboard / scan results
│   │       ├── triage/
│   │       │   └── page.tsx              # Finding triage queue
│   │       └── findings/
│   │           └── [findingId]/
│   │               ├── page.tsx          # Finding detail
│   │               └── poc/
│   │                   └── page.tsx      # PoC recorder page
│   ├── components/
│   │   ├── common/
│   │   │   ├── Badge.tsx                 # Severity/status badges
│   │   │   ├── Card.tsx                  # Content card wrapper
│   │   │   ├── DataTable.tsx             # Sortable data table
│   │   │   ├── EmptyState.tsx            # Empty state placeholder
│   │   │   ├── PageHeader.tsx            # Page title + actions
│   │   │   └── Sidebar.tsx               # Navigation sidebar
│   │   ├── dashboard/
│   │   │   ├── ScanResultsDashboard.tsx  # Main dashboard view
│   │   │   ├── SeverityBreakdown.tsx     # Severity stat cards
│   │   │   ├── ScanCoverageChart.tsx     # Coverage progress bars
│   │   │   ├── FindingsByScanner.tsx     # Scanner distribution
│   │   │   └── ActivityFeed.tsx          # Recent activity feed
│   │   ├── triage/
│   │   │   ├── FindingTriage.tsx         # Triage queue container
│   │   │   ├── FindingCard.tsx           # Individual finding row
│   │   │   ├── BulkActions.tsx           # Bulk triage controls
│   │   │   ├── TriageFilters.tsx         # Filter sidebar
│   │   │   └── AiSuggestionBadge.tsx     # AI confidence display
│   │   ├── findings/
│   │   │   ├── FindingDetailPanel.tsx    # Full finding detail
│   │   │   ├── FindingTabs.tsx           # Tab navigation
│   │   │   ├── DetailsTab.tsx            # Finding metadata
│   │   │   ├── EvidenceViewer.tsx        # Request/response viewer
│   │   │   └── AiAnalysisCard.tsx        # AI analysis display
│   │   ├── validation/
│   │   │   ├── ValidationPanel.tsx       # Validation container
│   │   │   ├── VerdictSelector.tsx       # TP/FP/Dup selection
│   │   │   ├── ValidationChecklist.tsx   # OWASP checklist
│   │   │   └── ValidationNotes.tsx       # Analyst notes editor
│   │   ├── poc/
│   │   │   ├── PocRecorder.tsx           # PoC container
│   │   │   ├── PocStep.tsx              # Single PoC step
│   │   │   ├── RequestResponseViewer.tsx # HTTP req/res display
│   │   │   ├── PocEnvironment.tsx        # Environment metadata
│   │   │   └── PocExport.tsx             # Export controls
│   │   ├── remediation/
│   │   │   ├── RemediationGuidance.tsx   # Remediation container
│   │   │   ├── RemediationEditor.tsx     # Editable guidance
│   │   │   ├── CodeExample.tsx           # Before/after code
│   │   │   ├── ReferenceLinks.tsx        # OWASP/CWE refs
│   │   │   └── SeverityUpdater.tsx       # Severity override
│   │   └── workbench/
│   │       └── WorkbenchLayout.tsx       # Overall layout shell
│   ├── hooks/
│   │   ├── useFindings.ts                # Finding CRUD queries
│   │   ├── useTriage.ts                  # Triage mutations
│   │   ├── useValidation.ts              # Validation mutations
│   │   ├── usePoc.ts                     # PoC CRUD operations
│   │   ├── useRemediation.ts             # Remediation queries
│   │   ├── useWebSocket.ts               # WebSocket connection
│   │   └── useEngagement.ts              # Engagement context
│   ├── stores/
│   │   ├── workbenchStore.ts             # UI state (filters, selection)
│   │   └── notificationStore.ts          # Real-time notifications
│   ├── types/
│   │   ├── finding.ts                    # Finding domain types
│   │   ├── engagement.ts                 # Engagement types
│   │   ├── validation.ts                 # Validation types
│   │   ├── poc.ts                        # PoC types
│   │   └── api.ts                        # API response types
│   └── lib/
│       ├── api-client.ts                 # HTTP client (ky)
│       ├── ws-client.ts                  # WebSocket manager
│       ├── auth.ts                       # OIDC auth helpers
│       └── utils.ts                      # Shared utilities
└── tests/
    ├── components/
    └── hooks/
```

### 2.4 Data Flow

```
User Action (click "Validate as TP")
    │
    ▼
React Component (VerdictSelector)
    │
    ├──▶ useTriage() hook → TanStack Mutation
    │       │
    │       ▼
    │     API Client (ky) → PUT /api/v1/findings/{id}/verdict
    │       │
    │       ▼
    │     API Gateway → Analyst Workbench Service (Go)
    │       │
    │       ▼
    │     PostgreSQL (update finding status)
    │       │
    │       ▼
    │     Kafka Event → finding.validated
    │
    ├──▶ Zustand Store (optimistic update)
    │
    └──▶ WebSocket ←── Redis Pub/Sub ←── Kafka Consumer
            │
            ▼
        Other analysts see real-time update
```

---

## 3. React Component Structure

### 3.1 Component Hierarchy

```
<RootLayout>                              # Providers, auth, theme
  <AuthGuard>                             # OIDC authentication
    <QueryClientProvider>                 # TanStack Query
      <WebSocketProvider>                 # Real-time connection
        <WorkbenchLayout>                 # Sidebar + main area
          │
          ├── <Sidebar>                   # Navigation + filters
          │   ├── <EngagementSelector>
          │   ├── <NavigationMenu>
          │   └── <FilterPanel>
          │
          └── <MainContent>               # Route-based content
              │
              ├── Route: /workbench
              │   └── <ScanResultsDashboard>
              │       ├── <SeverityBreakdown>
              │       │   └── <StatCard> x4 (Crit/High/Med/Low)
              │       ├── <ScanCoverageChart>
              │       ├── <FindingsByScanner>
              │       └── <ActivityFeed>
              │           └── <ActivityItem> x N
              │
              ├── Route: /workbench/triage
              │   └── <FindingTriage>
              │       ├── <BulkActions>
              │       ├── <TriageFilters>
              │       └── <DataTable>
              │           └── <FindingCard> x N
              │               ├── <SeverityBadge>
              │               ├── <AiSuggestionBadge>
              │               └── <FindingMeta>
              │
              └── Route: /workbench/findings/[id]
                  └── <FindingDetailPanel>
                      └── <FindingTabs>
                          ├── Tab: Details
                          │   └── <DetailsTab>
                          │       ├── <FindingMetadata>
                          │       ├── <EvidenceViewer>
                          │       └── <AiAnalysisCard>
                          │
                          ├── Tab: Validation
                          │   └── <ValidationPanel>
                          │       ├── <VerdictSelector>
                          │       ├── <ValidationChecklist>
                          │       └── <ValidationNotes>
                          │           └── <NoteEditor> (TipTap)
                          │
                          ├── Tab: PoC
                          │   └── <PocRecorder>
                          │       ├── <PocStep> x N
                          │       │   ├── <RequestResponseViewer>
                          │       │   └── <ScreenshotAttachment>
                          │       ├── <PocEnvironment>
                          │       └── <PocExport>
                          │
                          ├── Tab: Remediation
                          │   └── <RemediationGuidance>
                          │       ├── <RemediationEditor>
                          │       ├── <CodeExample>
                          │       ├── <ReferenceLinks>
                          │       └── <SeverityUpdater>
                          │           ├── <CvssCalculator>
                          │           └── <ContextFactors>
                          │
                          └── Tab: History
                              └── <AuditTimeline>
                                  └── <TimelineEntry> x N
```

### 3.2 Key Component Interfaces

See `src/types/finding.ts` and related type files for complete TypeScript
interfaces used by all components.

### 3.3 State Management Strategy

| State Type       | Tool           | Scope                              |
|------------------|----------------|-------------------------------------|
| Server data      | TanStack Query | Findings, engagements, PoCs        |
| UI state         | Zustand        | Filters, selection, panel state    |
| Form state       | React Hook Form| Validation forms, notes editor     |
| Real-time        | WebSocket/Yjs  | Live updates, collaborative edits  |
| URL state        | Next.js router | Current finding, active tab        |
| Auth state       | OIDC context   | User session, permissions          |
