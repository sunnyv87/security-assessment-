# VAPT SaaS Platform

Enterprise multi-tenant Vulnerability Assessment and Penetration Testing platform with AI-powered analysis, automated scan orchestration, and compliance reporting.

## Architecture Overview

```
                          ┌─────────────────┐
                          │   Kong Gateway   │  JWT + Rate Limiting + CORS
                          └────────┬────────┘
                  ┌────────────────┼────────────────┐
                  │                │                 │
          ┌───────▼──────┐ ┌──────▼───────┐ ┌──────▼──────────┐
          │   Analyst     │ │   Customer   │ │  API Consumers  │
          │   Portal      │ │   Portal     │ │  (MCP / CI/CD)  │
          │  (Next.js)    │ │  (Next.js)   │ │                 │
          └───────────────┘ └──────────────┘ └─────────────────┘
                  │                │                 │
       ┌─────────┴─────────┬─────┴────────┬────────┘
       │                   │              │
┌──────▼──────┐  ┌─────────▼────┐  ┌──────▼──────────┐
│  Security   │  │  Core Svcs   │  │  AI + Reporting │
│  Services   │  │  (5 svcs)    │  │  Services       │
│  (FastAPI)  │  │  (FastAPI)   │  │  (FastAPI)      │
└──────┬──────┘  └──────┬───────┘  └──────┬──────────┘
       │                │                 │
       ├────────────────┼─────────────────┤
       │         ┌──────▼───────┐         │
       │         │    Kafka     │         │
       │         │  (Strimzi)   │         │
       │         └──────────────┘         │
       │                                  │
┌──────▼──────┐ ┌──────────┐ ┌────────────▼──┐
│ PostgreSQL  │ │  Redis   │ │ Elasticsearch │
│ (CloudNative│ │  (HA)    │ │  + MinIO      │
│  PG)        │ │          │ │               │
└─────────────┘ └──────────┘ └───────────────┘
       │
┌──────▼──────┐
│  HashiCorp  │
│  Vault      │
└─────────────┘
```

## Backend Services

| Service | Port | Description |
|---|---|---|
| **security-services** | 8092 | RBAC enforcement, audit logging, credential vault, scan windows, IP allowlists |
| **ai-analyst-assistant** | 8090 | Claude-powered finding analysis, FP detection, risk prioritization, report drafting |
| **reporting-service** | 8091 | PDF/DOCX/HTML report generation, MinIO storage, four-eyes approval workflow |
| **engagement-svc** | 8080 | Engagement lifecycle management |
| **asset-discovery-svc** | 8080 | Target asset discovery and inventory |
| **analyst-workflow-svc** | 8080 | Finding triage and validation workflows |
| **findings-normalization-svc** | 8080 | Multi-scanner finding deduplication and normalization |
| **compliance-engine-svc** | 8080 | Compliance framework mapping (PCI-DSS, OWASP, ISO 27001) |
| **teams-bot-svc** | 8080 | Microsoft Teams notification integration |
| **scan-orchestrator** | 8080 | Scanner job orchestration (Burp, Tenable, Fortify, Mobile) |

## Frontend Applications

| App | Framework | Description |
|---|---|---|
| **analyst-portal** | Next.js 14 + React 18 | Security analyst workbench — triage, validation, remediation, PoC recording |
| **customer-portal** | Next.js 14 + React 18 | Customer-facing dashboard — engagement status, findings, report downloads |

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), Pydantic v2 |
| Frontend | TypeScript 5.5, Next.js 14, React 18, TailwindCSS, Radix UI, Zustand, TanStack Query |
| AI/LLM | Anthropic Claude (Opus 4.6), pgvector for RAG embeddings |
| Database | PostgreSQL 16 (CloudNativePG), Row-Level Security |
| Cache | Redis 7 with TLS + auth |
| Message Queue | Apache Kafka (Strimzi operator), per-service ACLs |
| Search/Analytics | Elasticsearch 8 with ILM (7-year retention) |
| Object Storage | MinIO (S3-compatible), per-tenant bucket isolation |
| Secrets | HashiCorp Vault with KMS auto-unseal |
| Identity | Keycloak (OIDC/OAuth2), RS256 JWT |
| API Gateway | Kong Ingress Controller with JWT + rate limiting |
| Service Mesh | Istio (strict mTLS, AuthorizationPolicy) |
| Container Runtime | Kubernetes with gVisor (runsc), Kyverno policy engine |
| Monitoring | Prometheus + Grafana + Alertmanager, Loki, Tempo |
| CI/CD | Container images pinned to semver tags |

## RBAC Roles

| Role | Scope |
|---|---|
| `platform_admin` | Full platform access across all tenants |
| `tenant_admin` | Full access within own tenant |
| `engagement_manager` | Manage engagements, scans, reports |
| `lead_analyst` | Validate findings, approve reports |
| `analyst` | Triage findings, run AI analysis, draft reports |
| `scanner_operator` | Launch/cancel scans, checkout credentials |
| `customer_admin` | Manage own engagement credentials, view findings/reports |
| `customer_viewer` | Read-only access to engagements, findings, reports |

## Security Posture

- **Production Readiness Score:** 97/100
- **Security Readiness Score:** 96/100
- **Red-Team Findings:** 42/42 remediated and verified

See `SECURITY_RETEST_REPORT.md` for full details.

## Quick Start

```bash
# Prerequisites: Python 3.12+, Node.js 20+, Docker, kubectl, Helm

# Backend (any service)
cd backend/services/ai-analyst-assistant
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8090

# Frontend
cd frontend/analyst-portal
npm install
npm run dev
```

See `docs/INSTALLATION.md` for full setup, `docs/DEPLOYMENT.md` for production Kubernetes deployment, and `docs/CONFIGURATION.md` for environment variable reference.

## Documentation

| Document | Description |
|---|---|
| [Installation Guide](docs/INSTALLATION.md) | Prerequisites, local development setup, dependency installation |
| [Deployment Guide](docs/DEPLOYMENT.md) | Kubernetes cluster setup, Helm charts, production deployment |
| [Configuration Guide](docs/CONFIGURATION.md) | Environment variables, secrets, per-service configuration |
| [User Guide](docs/USER_GUIDE.md) | Analyst workflows, AI features, report generation |
| [Security Re-Test Report](SECURITY_RETEST_REPORT.md) | Full 42-finding re-test with evidence |

## Project Structure

```
├── backend/
│   └── services/
│       ├── ai-analyst-assistant/     # AI-powered analysis (Claude)
│       │   ├── src/
│       │   │   ├── api/              # FastAPI routes
│       │   │   ├── config/           # Pydantic settings
│       │   │   ├── middleware/       # CSRF, rate limiting
│       │   │   ├── models/           # Domain models
│       │   │   ├── pipelines/        # AI pipelines (summarization, FP, risk, remediation, report)
│       │   │   ├── prompts/          # Prompt templates with injection defenses
│       │   │   └── services/         # LLM gateway, context builder, cache, Kafka
│       │   ├── tests/
│       │   ├── Dockerfile
│       │   └── pyproject.toml
│       ├── reporting-service/        # Report generation (PDF/DOCX/HTML)
│       │   ├── src/
│       │   │   ├── api/
│       │   │   ├── config/
│       │   │   ├── models/
│       │   │   ├── pipeline/         # Report generation pipeline
│       │   │   ├── renderers/        # PDF, HTML, DOCX renderers
│       │   │   └── services/         # MinIO storage, data collector, Kafka
│       │   └── Dockerfile
│       └── security-services/        # Security enforcement
│           ├── src/
│           │   ├── api/
│           │   ├── config/
│           │   ├── middleware/       # Tenant isolation, CSRF
│           │   ├── models/           # RBAC, audit, credential, scan window models
│           │   └── services/         # RBAC enforcer, audit logger, credential vault,
│           │                         # scan windows, IP allowlists
│           └── tests/
├── frontend/
│   └── analyst-portal/               # Analyst workbench (Next.js)
│       ├── src/
│       │   ├── app/                  # Next.js App Router pages
│       │   ├── components/           # React components (triage, findings, PoC, dashboard)
│       │   ├── hooks/                # React hooks (useFindings, useTriage, useValidation)
│       │   ├── lib/                  # API client, auth, WebSocket
│       │   ├── stores/               # Zustand stores
│       │   └── types/                # TypeScript type definitions
│       ├── next.config.ts
│       ├── tailwind.config.ts
│       └── package.json
├── infrastructure/
│   └── k8s/
│       ├── data/                     # PostgreSQL, Redis, Kafka, Elasticsearch, Vault, MinIO
│       ├── ingress/                  # Kong gateway, ingress routes
│       ├── monitoring/               # Prometheus stack, Loki, Tempo
│       ├── namespaces/               # Namespace definitions, network policies, quotas
│       ├── networking/               # Istio mTLS + AuthorizationPolicy
│       ├── platform/                 # Service deployments (core, scan, AI, frontends)
│       ├── scaling/                  # HPA, PodDisruptionBudgets
│       └── security/                 # Audit policy, Kyverno policies
└── SECURITY_RETEST_REPORT.md
```

## License

Proprietary. All rights reserved.
