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
