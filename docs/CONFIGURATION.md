# Configuration Guide

All backend services use Pydantic Settings with environment variable injection. Each service uses a unique prefix to avoid collisions.

## Table of Contents

1. [AI Analyst Assistant](#ai-analyst-assistant)
2. [Security Services](#security-services)
3. [Reporting Service](#reporting-service)
4. [Frontend Configuration](#frontend-configuration)
5. [Infrastructure Configuration](#infrastructure-configuration)
6. [Secrets Management](#secrets-management)

---

## AI Analyst Assistant

**Env prefix:** `AI_ASSISTANT_`
**Port:** 8090
**Config file:** `backend/services/ai-analyst-assistant/src/config/settings.py`

### Service

| Variable | Default | Description |
|---|---|---|
| `AI_ASSISTANT_SERVICE_NAME` | `ai-analyst-assistant` | Service identifier |
| `AI_ASSISTANT_ENVIRONMENT` | `development` | Environment (`development`, `staging`, `production`) |
| `AI_ASSISTANT_LOG_LEVEL` | `INFO` | Logging level |
| `AI_ASSISTANT_API_PORT` | `8090` | HTTP listen port |

### Claude API

| Variable | Default | Required | Description |
|---|---|---|---|
| `AI_ASSISTANT_ANTHROPIC_API_KEY` | _(empty)_ | **Yes** (non-dev) | Anthropic API key |
| `AI_ASSISTANT_CLAUDE_MODEL` | `claude-opus-4-6` | No | Claude model ID |
| `AI_ASSISTANT_CLAUDE_MAX_TOKENS_SUMMARY` | `2048` | No | Max tokens for summarization |
| `AI_ASSISTANT_CLAUDE_MAX_TOKENS_FP` | `2048` | No | Max tokens for FP detection |
| `AI_ASSISTANT_CLAUDE_MAX_TOKENS_PRIORITY` | `4096` | No | Max tokens for risk prioritization |
| `AI_ASSISTANT_CLAUDE_MAX_TOKENS_REMEDIATION` | `4096` | No | Max tokens for remediation |
| `AI_ASSISTANT_CLAUDE_MAX_TOKENS_REPORT` | `16384` | No | Max tokens for report drafting |
| `AI_ASSISTANT_CLAUDE_TEMPERATURE` | `0.1` | No | Model temperature (lower = more deterministic) |
| `AI_ASSISTANT_CLAUDE_TIMEOUT_SECONDS` | `120` | No | API call timeout |
| `AI_ASSISTANT_CLAUDE_MAX_RETRIES` | `3` | No | API retry count |

### Database

| Variable | Default | Description |
|---|---|---|
| `AI_ASSISTANT_DATABASE_URL` | `postgresql+asyncpg://vapt@localhost:5432/vapt_platform` | Async PostgreSQL connection string |

### Redis (Cache)

| Variable | Default | Description |
|---|---|---|
| `AI_ASSISTANT_REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `AI_ASSISTANT_CACHE_TTL_SUMMARY` | `14400` (4h) | Summary cache TTL in seconds |
| `AI_ASSISTANT_CACHE_TTL_FP_DETECTION` | `86400` (24h) | FP detection cache TTL |
| `AI_ASSISTANT_CACHE_TTL_REMEDIATION` | `43200` (12h) | Remediation cache TTL |
| `AI_ASSISTANT_CACHE_TTL_REPORT` | `3600` (1h) | Report draft cache TTL |
| `AI_ASSISTANT_CACHE_TTL_PRIORITY` | `7200` (2h) | Priority analysis cache TTL |

### Kafka

| Variable | Default | Description |
|---|---|---|
| `AI_ASSISTANT_KAFKA_BOOTSTRAP_SERVERS` | `vapt-kafka-kafka-bootstrap.vapt-data.svc.cluster.local:9093` | Kafka broker addresses |
| `AI_ASSISTANT_KAFKA_CONSUMER_GROUP` | `ai-analyst-assistant` | Consumer group ID |
| `AI_ASSISTANT_KAFKA_TOPIC_FINDINGS_NORMALIZED` | `finding.normalized` | Input topic |
| `AI_ASSISTANT_KAFKA_TOPIC_FINDINGS_ENRICHED` | `finding.ai_enriched` | Output topic |

### RAG / Embeddings

| Variable | Default | Description |
|---|---|---|
| `AI_ASSISTANT_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model for vector search |
| `AI_ASSISTANT_RAG_SIMILARITY_TOP_K` | `10` | Number of similar findings to retrieve |
| `AI_ASSISTANT_RAG_SIMILARITY_THRESHOLD` | `0.75` | Minimum similarity score |

### Keycloak OIDC

| Variable | Default | Description |
|---|---|---|
| `AI_ASSISTANT_KEYCLOAK_URL` | `https://keycloak.vapt-security.svc.cluster.local:8443` | Keycloak base URL |
| `AI_ASSISTANT_KEYCLOAK_REALM` | `vapt` | OIDC realm |
| `AI_ASSISTANT_JWT_ALGORITHM` | `RS256` | JWT signing algorithm |
| `AI_ASSISTANT_JWT_AUDIENCE` | `vapt-platform` | Expected JWT audience |
| `AI_ASSISTANT_KEYCLOAK_TLS_CA_PATH` | _(empty)_ | Path to CA cert for Keycloak TLS |

### Rate Limiting & Token Budget

| Variable | Default | Description |
|---|---|---|
| `AI_ASSISTANT_RATE_LIMIT_PER_TENANT_PER_MINUTE` | `60` | API rate limit per tenant |
| `AI_ASSISTANT_RATE_LIMIT_PER_ANALYST_PER_MINUTE` | `30` | API rate limit per analyst |
| `AI_ASSISTANT_MAX_INPUT_TOKENS` | `100000` | Max input tokens per request |
| `AI_ASSISTANT_MAX_EVIDENCE_CHARS` | `4000` | Max evidence characters per finding |
| `AI_ASSISTANT_MAX_TOKENS_PER_TENANT_PER_DAY` | `5000000` | Daily token budget per tenant |

---

## Security Services

**Env prefix:** `SECURITY_`
**Port:** 8092
**Config file:** `backend/services/security-services/src/config/settings.py`

### Service

| Variable | Default | Description |
|---|---|---|
| `SECURITY_SERVICE_NAME` | `security-services` | Service identifier |
| `SECURITY_ENVIRONMENT` | `development` | Environment |
| `SECURITY_API_PORT` | `8092` | HTTP listen port |

### Keycloak OIDC

| Variable | Default | Description |
|---|---|---|
| `SECURITY_KEYCLOAK_URL` | `https://keycloak.vapt-security.svc.cluster.local:8443` | Keycloak base URL |
| `SECURITY_KEYCLOAK_REALM` | `vapt` | OIDC realm |
| `SECURITY_KEYCLOAK_JWKS_URL` | _(auto-derived)_ | Override JWKS endpoint URL |
| `SECURITY_KEYCLOAK_CLIENT_ID` | `vapt-platform` | OIDC client ID |
| `SECURITY_KEYCLOAK_ADMIN_CLIENT_ID` | `admin-cli` | Admin client ID |
| `SECURITY_JWT_ALGORITHM` | `RS256` | JWT signing algorithm |
| `SECURITY_JWT_AUDIENCE` | `vapt-platform` | Expected JWT audience |
| `SECURITY_KEYCLOAK_TLS_CA_PATH` | _(empty)_ | Path to CA cert for Keycloak TLS |

### PostgreSQL

| Variable | Default | Required | Description |
|---|---|---|---|
| `SECURITY_DB_HOST` | `vapt-pgbouncer-rw.vapt-data.svc.cluster.local` | Yes | Database host |
| `SECURITY_DB_PORT` | `5432` | No | Database port |
| `SECURITY_DB_NAME` | `vapt_platform` | No | Database name |
| `SECURITY_DB_USER` | `vapt_security` | No | Database user |
| `SECURITY_DB_PASSWORD` | _(empty)_ | **Yes** (non-dev) | Database password |
| `SECURITY_DB_SSL_MODE` | `require` | No | SSL mode |

### HashiCorp Vault

| Variable | Default | Description |
|---|---|---|
| `SECURITY_VAULT_ADDR` | `https://vault.vapt-data.svc.cluster.local:8200` | Vault server address |
| `SECURITY_VAULT_AUTH_METHOD` | `kubernetes` | Vault auth method |
| `SECURITY_VAULT_ROLE` | `security-services` | Vault Kubernetes auth role |
| `SECURITY_VAULT_MOUNT_TRANSIT` | `transit` | Transit engine mount path |
| `SECURITY_VAULT_MOUNT_KV` | `secret` | KV-v2 engine mount path |
| `SECURITY_VAULT_CREDENTIAL_TTL` | `900` (15 min) | Default credential lease TTL |

### Redis

| Variable | Default | Description |
|---|---|---|
| `SECURITY_REDIS_URL` | `redis://redis-master.vapt-data.svc.cluster.local:6379/3` | Redis connection URL |
| `SECURITY_RBAC_CACHE_TTL` | `300` (5 min) | RBAC context cache TTL |
| `SECURITY_IP_ALLOWLIST_CACHE_TTL` | `60` (1 min) | IP allowlist cache TTL |

### Kafka

| Variable | Default | Description |
|---|---|---|
| `SECURITY_KAFKA_BOOTSTRAP_SERVERS` | `vapt-kafka-kafka-bootstrap.vapt-data.svc.cluster.local:9093` | Kafka brokers |
| `SECURITY_KAFKA_AUDIT_TOPIC` | `audit.events` | Audit event topic |
| `SECURITY_KAFKA_CONSUMER_GROUP` | `security-services` | Consumer group ID |

### Audit

| Variable | Default | Description |
|---|---|---|
| `SECURITY_AUDIT_HASH_CHAIN_ENABLED` | `true` | Enable tamper-evident hash chains |
| `SECURITY_AUDIT_RETENTION_DAYS` | `2555` (7 years) | Audit log retention period |

### Scan Windows

| Variable | Default | Description |
|---|---|---|
| `SECURITY_SCAN_WINDOW_DEFAULT_TIMEZONE` | `UTC` | Default timezone for scan windows |
| `SECURITY_SCAN_EMERGENCY_OVERRIDE_REQUIRES_APPROVAL` | `true` | Require dual-approval for overrides |
| `SECURITY_SCAN_EMERGENCY_OVERRIDE_APPROVERS_REQUIRED` | `2` | Number of approvers required |

### IP Allowlists

| Variable | Default | Description |
|---|---|---|
| `SECURITY_IP_ALLOWLIST_MAX_ENTRIES_PER_TENANT` | `500` | Max allowlist entries per tenant |
| `SECURITY_SCANNER_EGRESS_NAT_MODE` | `shared_pool` | NAT mode (`shared_pool` or `dedicated_nat`) |

---

## Reporting Service

**Env prefix:** `REPORT_`
**Port:** 8091
**Config file:** `backend/services/reporting-service/src/config/settings.py`

### Service

| Variable | Default | Description |
|---|---|---|
| `REPORT_SERVICE_NAME` | `reporting-service` | Service identifier |
| `REPORT_ENVIRONMENT` | `development` | Environment |
| `REPORT_LOG_LEVEL` | `INFO` | Logging level |
| `REPORT_API_PORT` | `8091` | HTTP listen port |

### Database

| Variable | Default | Description |
|---|---|---|
| `REPORT_DATABASE_URL` | `postgresql+asyncpg://vapt@localhost:5432/vapt_platform` | Async PostgreSQL connection |

### MinIO / S3

| Variable | Default | Required | Description |
|---|---|---|---|
| `REPORT_MINIO_ENDPOINT` | `minio.vapt-data.svc.cluster.local:9000` | Yes | MinIO server endpoint |
| `REPORT_MINIO_ACCESS_KEY` | _(empty)_ | **Yes** (non-dev) | MinIO access key |
| `REPORT_MINIO_SECRET_KEY` | _(empty)_ | **Yes** (non-dev) | MinIO secret key |
| `REPORT_MINIO_BUCKET_PREFIX` | `vapt-reports` | No | Bucket name prefix |
| `REPORT_MINIO_USE_SSL` | `true` | No | Enable TLS for MinIO |
| `REPORT_PRESIGNED_URL_TTL_SECONDS` | `900` (15 min) | No | Pre-signed URL expiry |

### Kafka

| Variable | Default | Description |
|---|---|---|
| `REPORT_KAFKA_BOOTSTRAP_SERVERS` | `vapt-kafka-kafka-bootstrap.vapt-data.svc.cluster.local:9093` | Kafka brokers |
| `REPORT_KAFKA_CONSUMER_GROUP` | `reporting-service` | Consumer group ID |
| `REPORT_KAFKA_TOPIC_FINDING_VALIDATED` | `finding.validated` | Input topic |
| `REPORT_KAFKA_TOPIC_REPORT_GENERATED` | `report.generated` | Output topic |
| `REPORT_KAFKA_TOPIC_REPORT_APPROVED` | `report.approved` | Approval event topic |

### Internal Service URLs

| Variable | Default | Description |
|---|---|---|
| `REPORT_FINDINGS_SERVICE_URL` | `https://findings-service:8080` | Findings service address |
| `REPORT_ENGAGEMENT_SERVICE_URL` | `https://engagement-service:8080` | Engagement service address |
| `REPORT_COMPLIANCE_ENGINE_URL` | `https://compliance-engine:8080` | Compliance engine address |
| `REPORT_AI_ASSISTANT_URL` | `https://ai-analyst-assistant:8090` | AI assistant address |
| `REPORT_SERVICE_MESH_CA_PATH` | _(empty)_ | CA cert for service mesh mTLS |

### Keycloak OIDC

| Variable | Default | Description |
|---|---|---|
| `REPORT_KEYCLOAK_URL` | `https://keycloak.vapt-security.svc.cluster.local:8443` | Keycloak base URL |
| `REPORT_KEYCLOAK_REALM` | `vapt` | OIDC realm |
| `REPORT_JWT_ALGORITHM` | `RS256` | JWT signing algorithm |
| `REPORT_JWT_AUDIENCE` | `vapt-platform` | Expected JWT audience |
| `REPORT_KEYCLOAK_TLS_CA_PATH` | _(empty)_ | CA cert for Keycloak TLS |

### Report Generation

| Variable | Default | Description |
|---|---|---|
| `REPORT_TEMPLATE_DIR` | `src/templates` | Path to report templates |
| `REPORT_MAX_CONCURRENT_RENDERS` | `4` | Max parallel PDF renders |
| `REPORT_PDF_RENDER_TIMEOUT_SECONDS` | `120` | PDF generation timeout |
| `REPORT_MAX_REPORT_SIZE_MB` | `50` | Maximum report file size |
| `REPORT_REPORT_RETENTION_DAYS` | `90` | Report retention period |

---

## Frontend Configuration

### Analyst Portal

**Config file:** `frontend/analyst-portal/next.config.ts`
**Environment:** `.env.local` (development) or injected at build time

| Variable | Default | Description |
|---|---|---|
| `API_GATEWAY_URL` | `http://localhost:8080` | Backend API gateway URL |
| `NEXT_PUBLIC_WS_URL` | `ws://localhost:8081` | WebSocket server URL |
| `NEXT_PUBLIC_KEYCLOAK_URL` | — | Keycloak base URL |
| `NEXT_PUBLIC_KEYCLOAK_REALM` | `vapt` | Keycloak realm |
| `NEXT_PUBLIC_KEYCLOAK_CLIENT_ID` | — | OIDC client ID |

### Security Headers (Built-in)

The Next.js config applies these headers automatically:

| Header | Value |
|---|---|
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; ...` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), payment=()` |
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` |

---

## Infrastructure Configuration

### Kong API Gateway

Key configuration in `infrastructure/k8s/ingress/kong-gateway.yaml`:

| Setting | Value |
|---|---|
| Gateway replicas | 3 |
| Rate limit | 600 req/min per consumer |
| JWT validation | RS256, verifies `exp` |
| Max request size | 50 MB |
| CORS origins | `analyst.vapt-platform.com`, `portal.vapt-platform.com` |

### Prometheus Alerts

Configured in `infrastructure/k8s/monitoring/prometheus-stack.yaml`:

| Alert | Threshold |
|---|---|
| High auth failure rate | >50 failures / 5 min |
| Vault sealed | Vault status != unsealed |
| Credential checkout anomaly | >10 / user / hour |
| Audit hash chain broken | Any integrity failure |

---

## Secrets Management

### Kubernetes Secrets (Recommended Approach)

Use External Secrets Operator or Vault Agent Injector to inject secrets:

```yaml
# Example: Vault Agent injection annotation
spec:
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "security-services"
        vault.hashicorp.com/agent-inject-secret-db: "secret/data/vapt/db"
        vault.hashicorp.com/agent-inject-template-db: |
          {{- with secret "secret/data/vapt/db" -}}
          export SECURITY_DB_PASSWORD="{{ .Data.data.password }}"
          {{- end }}
```

### Sensitive Variables Summary

These variables **must not** be stored in plaintext configs:

| Service | Variable | Injection Method |
|---|---|---|
| AI Assistant | `AI_ASSISTANT_ANTHROPIC_API_KEY` | K8s Secret / Vault |
| Security | `SECURITY_DB_PASSWORD` | K8s Secret / Vault |
| Reporting | `REPORT_MINIO_ACCESS_KEY` | K8s Secret / Vault |
| Reporting | `REPORT_MINIO_SECRET_KEY` | K8s Secret / Vault |
| Redis | `requirepass` | K8s Secret |
| Kafka | TLS keystores | K8s Secret (Strimzi-managed) |
| Vault | KMS unseal key | K8s Secret (`secretKeyRef`) |

### Credential Validation

All services validate that required credentials are present in non-development environments. If a required credential is missing at startup, the service will **fail fast** with a clear error message rather than running in a degraded state.
