# Deployment Guide

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Kubernetes Cluster Setup](#kubernetes-cluster-setup)
3. [Namespace and Network Policy Setup](#namespace-and-network-policy-setup)
4. [Data Layer Deployment](#data-layer-deployment)
5. [Security Infrastructure](#security-infrastructure)
6. [Platform Services Deployment](#platform-services-deployment)
7. [Ingress and API Gateway](#ingress-and-api-gateway)
8. [Monitoring Stack](#monitoring-stack)
9. [Scaling and High Availability](#scaling-and-high-availability)
10. [Post-Deployment Verification](#post-deployment-verification)

---

## Architecture Overview

### Deployment Order

Deploy in this order to satisfy dependencies:

```
1. Namespaces + Network Policies
2. Istio Service Mesh
3. Data Layer (PostgreSQL → Redis → Kafka → Elasticsearch → MinIO → Vault)
4. Security Policies (Kyverno, Audit Policy)
5. Core Platform Services
6. Scan Execution Services
7. AI + Reporting Services
8. Frontend Applications
9. Ingress / API Gateway
10. Monitoring Stack
11. HPA + PDB (Scaling)
```

### Namespaces

| Namespace | Purpose |
|---|---|
| `vapt-platform` | Core services, scan execution, AI, reporting |
| `vapt-data` | PostgreSQL, Redis, Kafka, Elasticsearch, MinIO, Vault |
| `vapt-security` | Keycloak, security services |
| `vapt-monitoring` | Prometheus, Grafana, Loki, Tempo |
| `ingress-system` | Kong Ingress Controller |
| `istio-system` | Istio control plane |
| `kyverno` | Kyverno policy engine |

---

## Kubernetes Cluster Setup

### Minimum Cluster Requirements

| Resource | Minimum | Recommended |
|---|---|---|
| Nodes | 3 (HA) | 6+ (multi-AZ) |
| CPU per node | 8 cores | 16 cores |
| Memory per node | 32 GB | 64 GB |
| Storage class | SSD-backed | gp3 / io2 (AWS) |
| Kubernetes version | 1.28+ | 1.30+ |

### Node Pools (Recommended)

```
system-pool:     3 nodes (8 CPU, 32 GB) — data layer, monitoring
platform-pool:   3 nodes (8 CPU, 32 GB) — platform services
scan-pool:       2-6 nodes (4 CPU, 16 GB) — scan jobs (auto-scaling)
```

### Container Runtime

The platform uses **gVisor (runsc)** for scan execution pods. Install gVisor RuntimeClass:

```bash
kubectl apply -f - <<EOF
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
EOF
```

---

## Namespace and Network Policy Setup

```bash
# Create all namespaces
kubectl apply -f infrastructure/k8s/namespaces/namespaces.yaml

# Apply network policies (restrict cross-namespace traffic)
kubectl apply -f infrastructure/k8s/namespaces/network-policies.yaml

# Apply namespace-level resource quotas
kubectl apply -f infrastructure/k8s/namespaces/resource-quotas.yaml
```

---

## Data Layer Deployment

### 1. PostgreSQL (CloudNativePG)

```bash
# Prerequisites: CloudNativePG operator installed
kubectl apply -f infrastructure/k8s/data/postgresql.yaml
```

Key configuration:
- 3-node HA cluster with streaming replication
- `hostssl` with `scram-sha-256` and `clientcert=verify-ca`
- PgBouncer connection pooling
- `shared_preload_libraries: 'vector'` for RAG embeddings
- PVC: 100Gi per instance (SSD storage class)

Verify:
```bash
kubectl get cluster -n vapt-data
kubectl exec -it vapt-pg-1 -n vapt-data -- psql -c "SELECT pg_is_in_recovery();"
```

### 2. Redis

```bash
kubectl apply -f infrastructure/k8s/data/redis.yaml
```

Key configuration:
- HA with Sentinel (3 replicas)
- TLS on port 6380 with client certificate authentication
- `requirepass` enabled
- `maxmemory-policy: allkeys-lru`
- PVC: 10Gi per instance

### 3. Kafka (Strimzi)

```bash
# Prerequisites: Strimzi operator installed
kubectl apply -f infrastructure/k8s/data/kafka.yaml
```

Key configuration:
- 3-broker cluster with TLS (AES-256-GCM + ChaCha20 cipher suites)
- Per-service KafkaUser resources with topic-level ACLs:
  - `scan-orchestrator` — Write `scan.requested`, Read/Write `scan.completed`
  - `findings-service` — Write `finding.normalized`
  - `ai-analyst-assistant` — Read `finding.normalized`, Write `finding.ai_enriched`
  - `reporting-service` — Read `finding.validated`, Write `report.generated`
  - `audit-logger` — Write `audit.events`
- 7-day retention, replication factor 3

### 4. Elasticsearch

```bash
kubectl apply -f infrastructure/k8s/data/elasticsearch.yaml
```

Key configuration:
- 3-node cluster (master + data roles)
- ILM policy: hot → warm (90d) → cold (365d) → delete (2555d / 7 years)
- Security audit index template
- PVC: 500Gi per node

### 5. MinIO

```bash
kubectl apply -f infrastructure/k8s/data/minio.yaml
```

Key configuration:
- 4-node distributed mode
- Per-tenant bucket isolation (`vapt-reports-{tenant_id}`)
- TLS enabled
- PVC: 200Gi per node

### 6. HashiCorp Vault

```bash
kubectl apply -f infrastructure/k8s/data/vault.yaml
```

Key configuration:
- 3-node HA with Raft storage
- KMS auto-unseal (AWS KMS key reference via K8s Secret)
- Kubernetes auth method for service authentication
- Transit secrets engine for encryption
- KV-v2 for credential storage
- 15-minute default credential lease TTL

Post-deployment initialization:
```bash
# Initialize Vault (only on first deploy)
kubectl exec -it vault-0 -n vapt-data -- vault operator init \
  -key-shares=5 -key-threshold=3

# Enable Kubernetes auth
kubectl exec -it vault-0 -n vapt-data -- vault auth enable kubernetes

# Configure policies per service role
kubectl exec -it vault-0 -n vapt-data -- vault policy write security-services - <<EOF
path "secret/data/tenants/+/credentials/*" {
  capabilities = ["create", "read", "update", "delete"]
}
path "transit/encrypt/*" {
  capabilities = ["update"]
}
path "transit/decrypt/*" {
  capabilities = ["update"]
}
EOF
```

---

## Security Infrastructure

### Istio Service Mesh

```bash
# Install Istio (if not already installed)
istioctl install --set profile=default -y

# Enable sidecar injection
kubectl label namespace vapt-platform istio-injection=enabled
kubectl label namespace vapt-data istio-injection=enabled
kubectl label namespace vapt-security istio-injection=enabled

# Apply mTLS + AuthorizationPolicy
kubectl apply -f infrastructure/k8s/networking/istio-auth-policies.yaml
```

Policies applied:
- **PeerAuthentication**: STRICT mTLS (no plaintext allowed)
- **AuthorizationPolicy** per service: explicit principal allowlists
- **deny-all-default**: Denies traffic not matching any allow rule

### Kyverno Policies

```bash
kubectl apply -f infrastructure/k8s/security/kyverno-policies.yaml
```

Enforced policies:
- `restrict-image-registries` — Only `vapt-registry/` images allowed (enforce mode)
- `require-pod-security-standards` — Restricted PSS baseline
- `disallow-latest-tag` — Blocks `:latest` image tags
- `require-resource-limits` — All pods must declare CPU/memory limits

### Kubernetes Audit Policy

```bash
# Apply to API server (managed cluster: use cloud provider's audit config)
kubectl apply -f infrastructure/k8s/security/audit-policy.yaml
```

Audit rules:
- Secrets access: `Metadata` level
- RBAC changes: `RequestResponse` level
- Job create/delete: `RequestResponse` level
- Pod exec/attach: `RequestResponse` level
- Default: `Metadata` level

---

## Platform Services Deployment

### Core Services

```bash
kubectl apply -f infrastructure/k8s/platform/core-services.yaml
```

Deploys:
- `engagement-svc` (2 replicas)
- `asset-discovery-svc` (2 replicas)
- `analyst-workflow-svc` (2 replicas)
- `findings-normalization-svc` (2 replicas)
- `compliance-engine-svc` (2 replicas)
- `teams-bot-svc` (1 replica)

All services run as:
- Non-root user (UID 10001)
- Read-only root filesystem
- `allowPrivilegeEscalation: false`
- `runAsNonRoot: true`
- Pinned to `:1.0.0` image tags

### Scan Execution Services

```bash
kubectl apply -f infrastructure/k8s/platform/scan-execution.yaml
kubectl apply -f infrastructure/k8s/platform/resource-quotas.yaml
```

Deploys:
- `scan-orchestrator` (2 replicas) — Manages scan Jobs
- Scanner connectors as Job templates:
  - `burp-connector` (4 CPU, 8Gi memory limit per job)
  - `tenable-connector`
  - `fortify-connector`
  - `mobile-connector`

Resource quotas for scan namespace:
- Max 32 CPU requests, 64Gi memory requests
- Max 20 concurrent pods

### AI + Reporting Services

```bash
kubectl apply -f infrastructure/k8s/platform/ai-reporting-services.yaml
```

Deploys:
- `ai-analyst-assistant` (2 replicas, port 8090)
- `reporting-service` (2 replicas, port 8091)

### Frontend Applications

```bash
kubectl apply -f infrastructure/k8s/platform/frontends.yaml
```

Deploys:
- `analyst-portal` (3 replicas) — CSP, HSTS, X-Frame-Options headers
- `customer-portal` (3 replicas)

---

## Ingress and API Gateway

```bash
# Kong Ingress Controller (via Helm)
helm install kong kong/ingress -n ingress-system \
  -f infrastructure/k8s/ingress/kong-gateway.yaml

# Ingress routes
kubectl apply -f infrastructure/k8s/ingress/ingress-routes.yaml
```

Kong plugins configured:
- **Rate limiting**: 600 req/min per consumer (Redis-backed)
- **JWT validation**: RS256, validates `exp` claim
- **IP restriction**: Admin endpoints restricted to `10.0.0.0/8`
- **Request size limit**: 50 MB maximum payload
- **CORS**: Allowed origins for analyst and customer portals

---

## Monitoring Stack

```bash
kubectl apply -f infrastructure/k8s/monitoring/prometheus-stack.yaml
kubectl apply -f infrastructure/k8s/monitoring/loki-tempo.yaml
```

Components:
- **Prometheus** — Metrics collection with 8 security alert rules
- **Grafana** — Dashboards for platform, scan, and security metrics
- **Alertmanager** — Alert routing to PagerDuty/Slack/email
- **Loki** — Log aggregation
- **Tempo** — Distributed tracing

### Security Alert Rules

| Alert | Severity | Trigger |
|---|---|---|
| `HighAuthFailureRate` | critical | >50 auth failures in 5 minutes |
| `CredentialCheckoutAnomaly` | warning | >10 checkouts per user in 1 hour |
| `ScanOutsideWindow` | warning | Scan attempt outside approved window |
| `AuditHashChainBroken` | critical | Audit log integrity failure |
| `VaultSealedAlert` | critical | Vault in sealed state |
| `TenantIsolationBypass` | critical | Cross-tenant access attempt detected |
| `AITokenBudgetExceeded` | warning | Tenant approaching daily AI token limit |
| `SuspiciousIPAccess` | warning | Access from non-allowlisted IP |

---

## Scaling and High Availability

```bash
kubectl apply -f infrastructure/k8s/scaling/hpa.yaml
kubectl apply -f infrastructure/k8s/scaling/pod-disruption-budgets.yaml
```

### Horizontal Pod Autoscalers

| Service | Min | Max | Target CPU |
|---|---|---|---|
| Core services | 2 | 8 | 70% |
| AI assistant | 2 | 6 | 60% |
| Reporting | 2 | 4 | 70% |
| Frontends | 3 | 10 | 60% |
| Scan orchestrator | 2 | 4 | 70% |

### Pod Disruption Budgets

All critical services maintain `minAvailable: 1` or `maxUnavailable: 1` to ensure zero-downtime rolling updates.

---

## Post-Deployment Verification

### Health Checks

```bash
# All services expose /health endpoints
for svc in engagement-svc asset-discovery-svc analyst-workflow-svc \
           findings-normalization-svc compliance-engine-svc scan-orchestrator \
           ai-analyst-assistant reporting-service; do
  echo "Checking $svc..."
  kubectl exec -it deploy/$svc -n vapt-platform -- \
    curl -s http://localhost:8080/health || echo "FAILED"
done
```

### Verify mTLS

```bash
# Check Istio mTLS status
istioctl x check-inject -n vapt-platform
istioctl proxy-status -n vapt-platform
```

### Verify Kyverno Policies

```bash
# Try to deploy a :latest image (should be blocked)
kubectl run test --image=nginx:latest -n vapt-platform --dry-run=server
# Expected: admission webhook denied

# Check policy reports
kubectl get policyreport -n vapt-platform
```

### Verify Vault

```bash
kubectl exec -it vault-0 -n vapt-data -- vault status
kubectl exec -it vault-0 -n vapt-data -- vault auth list
```

### Verify Kafka ACLs

```bash
kubectl exec -it vapt-kafka-kafka-0 -n vapt-data -- \
  bin/kafka-acls.sh --bootstrap-server localhost:9093 \
  --command-config /tmp/admin.properties --list
```

### Smoke Test

```bash
# Get a JWT from Keycloak
TOKEN=$(curl -s -X POST \
  "https://keycloak.vapt-security.svc.cluster.local:8443/realms/vapt/protocol/openid-connect/token" \
  -d "grant_type=client_credentials&client_id=vapt-platform&client_secret=<secret>" \
  | jq -r '.access_token')

# Validate token via security-services
curl -H "Authorization: Bearer $TOKEN" \
  https://api.vapt-platform.com/api/v1/security/auth/validate

# Check AI service health
curl -H "Authorization: Bearer $TOKEN" \
  https://api.vapt-platform.com/v1/health
```

---

## Rollback Procedure

### Service Rollback

```bash
# Roll back a deployment to previous revision
kubectl rollout undo deployment/<service-name> -n vapt-platform

# Check rollout status
kubectl rollout status deployment/<service-name> -n vapt-platform
```

### Database Rollback

PostgreSQL uses CloudNativePG with point-in-time recovery:

```bash
# List available backups
kubectl get backups -n vapt-data

# Restore to a specific point in time
kubectl apply -f - <<EOF
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: vapt-pg-restored
  namespace: vapt-data
spec:
  bootstrap:
    recovery:
      source: vapt-pg
      recoveryTarget:
        targetTime: "2026-03-15T10:00:00Z"
EOF
```

---

## TLS Certificate Requirements

| Component | Certificate | Issuer |
|---|---|---|
| Kong Ingress | Wildcard `*.vapt-platform.com` | Public CA (Let's Encrypt / DigiCert) |
| Inter-service mTLS | Auto-generated | Istio Citadel |
| PostgreSQL client certs | Per-service certs | Internal CA |
| Kafka TLS | Broker + client certs | Strimzi CA |
| Redis TLS | Server + client certs | Internal CA |
| Vault TLS | Server cert | Internal CA |
| Keycloak TLS | Server cert | Internal CA |
