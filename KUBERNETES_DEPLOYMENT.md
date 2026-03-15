# Kubernetes Deployment Architecture — AI-Driven VAPT Orchestration Platform

## Production-Grade Infrastructure for MSSP Operations at Scale (500+ Customers)

---

## 1. Infrastructure Diagram

```
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                    CLOUD PROVIDER (AWS / Azure / GCP)                                  ║
║                                                                                                        ║
║  ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐    ║
║  │                         EXTERNAL EDGE (CDN + WAF + DDoS Protection)                             │    ║
║  │                         Cloudflare / AWS CloudFront + Shield + WAF                              │    ║
║  └──────────────────────────────────────────┬──────────────────────────────────────────────────────┘    ║
║                                              │                                                          ║
║                                              ▼                                                          ║
║  ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐    ║
║  │                              KUBERNETES CLUSTER (EKS / AKS / GKE)                               │    ║
║  │                           Multi-AZ │ Private Subnets │ Node Auto-scaling                        │    ║
║  │                                                                                                  │    ║
║  │  ┌─── ingress-system ──────────────────────────────────────────────────────────────────────┐     │    ║
║  │  │                                                                                         │     │    ║
║  │  │   ┌──────────────────────────┐    ┌────────────────────────────────────────────────┐    │     │    ║
║  │  │   │   KONG INGRESS GATEWAY   │    │         CERT-MANAGER (Let's Encrypt)           │    │     │    ║
║  │  │   │   ────────────────────   │    │   Auto-provision TLS certificates              │    │     │    ║
║  │  │   │   • Rate limiting        │    └────────────────────────────────────────────────┘    │     │    ║
║  │  │   │   • JWT validation       │                                                          │     │    ║
║  │  │   │   • mTLS termination     │    ┌────────────────────────────────────────────────┐    │     │    ║
║  │  │   │   • Tenant routing       │    │         EXTERNAL-DNS                           │    │     │    ║
║  │  │   │   • Request transform    │    │   Auto-manage DNS records                      │    │     │    ║
║  │  │   │   • OAuth2 plugin        │    └────────────────────────────────────────────────┘    │     │    ║
║  │  │   │   • IP allowlisting      │                                                          │     │    ║
║  │  │   │   • L7 load balancing    │                                                          │     │    ║
║  │  │   └──────────┬───────────────┘                                                          │     │    ║
║  │  └──────────────┼──────────────────────────────────────────────────────────────────────────┘     │    ║
║  │                 │                                                                                │    ║
║  │  ┌──────────────┼── istio-system ──────────────────────────────────────────────────────────┐     │    ║
║  │  │              │                                                                          │     │    ║
║  │  │   ┌──────────▼───────────────┐    ┌────────────────────────────────────────────────┐    │     │    ║
║  │  │   │   ISTIO SERVICE MESH     │    │         ISTIO CONTROL PLANE                    │    │     │    ║
║  │  │   │   ────────────────────   │    │   • istiod (Pilot + Citadel + Galley)          │    │     │    ║
║  │  │   │   • Envoy sidecar proxy  │    │   • mTLS certificate rotation                  │    │     │    ║
║  │  │   │   • Circuit breaker      │    │   • Traffic policy enforcement                 │    │     │    ║
║  │  │   │   • Retry policies       │    │   • Service discovery                          │    │     │    ║
║  │  │   │   • mTLS pod-to-pod      │    └────────────────────────────────────────────────┘    │     │    ║
║  │  │   │   • Distributed tracing  │                                                          │     │    ║
║  │  │   │   • Traffic shifting     │                                                          │     │    ║
║  │  │   └──────────────────────────┘                                                          │     │    ║
║  │  └─────────────────────────────────────────────────────────────────────────────────────────┘     │    ║
║  │                                                                                                  │    ║
║  │  ╔═══════════════════════════════════════════════════════════════════════════════════════════╗    │    ║
║  │  ║              NAMESPACE: vapt-platform  (Application Workloads)                           ║    │    ║
║  │  ║                                                                                          ║    │    ║
║  │  ║  ┌─────── TIER 1: CORE API SERVICES (Deployment) ─────────────────────────────────┐     ║    │    ║
║  │  ║  │                                                                                  │     ║    │    ║
║  │  ║  │  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────────────────┐    │     ║    │    ║
║  │  ║  │  │ engagement-svc  │  │ asset-discovery   │  │ analyst-workflow-svc         │    │     ║    │    ║
║  │  ║  │  │ ─────────────── │  │ ──────────────── │  │ ────────────────────────     │    │     ║    │    ║
║  │  ║  │  │ Replicas: 3     │  │ Replicas: 2      │  │ Replicas: 3                  │    │     ║    │    ║
║  │  ║  │  │ CPU: 500m-1000m │  │ CPU: 250m-500m   │  │ CPU: 500m-1000m              │    │     ║    │    ║
║  │  ║  │  │ Mem: 512Mi-1Gi  │  │ Mem: 256Mi-512Mi │  │ Mem: 512Mi-1Gi               │    │     ║    │    ║
║  │  ║  │  │ HPA: 3→10       │  │ HPA: 2→6         │  │ HPA: 3→12                    │    │     ║    │    ║
║  │  ║  │  └─────────────────┘  └──────────────────┘  └──────────────────────────────┘    │     ║    │    ║
║  │  ║  │                                                                                  │     ║    │    ║
║  │  ║  │  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────────────────┐    │     ║    │    ║
║  │  ║  │  │ compliance-     │  │ teams-bot-svc    │  │ findings-normalization-svc   │    │     ║    │    ║
║  │  ║  │  │  engine-svc     │  │ ──────────────── │  │ ────────────────────────     │    │     ║    │    ║
║  │  ║  │  │ ─────────────── │  │ Replicas: 2      │  │ Replicas: 3                  │    │     ║    │    ║
║  │  ║  │  │ Replicas: 2     │  │ CPU: 250m-500m   │  │ CPU: 500m-2000m              │    │     ║    │    ║
║  │  ║  │  │ CPU: 250m-500m  │  │ Mem: 256Mi-512Mi │  │ Mem: 1Gi-4Gi                 │    │     ║    │    ║
║  │  ║  │  │ Mem: 256Mi-512Mi│  │ HPA: 2→4         │  │ HPA: 3→15                    │    │     ║    │    ║
║  │  ║  │  │ HPA: 2→6        │  └──────────────────┘  └──────────────────────────────┘    │     ║    │    ║
║  │  ║  │  └─────────────────┘                                                             │     ║    │    ║
║  │  ║  └──────────────────────────────────────────────────────────────────────────────────┘     ║    │    ║
║  │  ║                                                                                          ║    │    ║
║  │  ║  ┌─────── TIER 2: AI & REPORT SERVICES (Deployment) ──────────────────────────────┐     ║    │    ║
║  │  ║  │                                                                                  │     ║    │    ║
║  │  ║  │  ┌─────────────────────────┐  ┌──────────────────────────────────────────┐      │     ║    │    ║
║  │  ║  │  │ ai-analyst-assistant    │  │ reporting-service                        │      │     ║    │    ║
║  │  ║  │  │ ─────────────────────── │  │ ──────────────────────────────           │      │     ║    │    ║
║  │  ║  │  │ Replicas: 3             │  │ Replicas: 2                              │      │     ║    │    ║
║  │  ║  │  │ CPU: 1000m-2000m        │  │ CPU: 1000m-2000m                         │      │     ║    │    ║
║  │  ║  │  │ Mem: 2Gi-4Gi            │  │ Mem: 2Gi-4Gi                             │      │     ║    │    ║
║  │  ║  │  │ HPA: 3→10               │  │ HPA: 2→8                                │      │     ║    │    ║
║  │  ║  │  │ GPU: optional            │  │ WeasyPrint rendering needs higher mem   │      │     ║    │    ║
║  │  ║  │  └─────────────────────────┘  └──────────────────────────────────────────┘      │     ║    │    ║
║  │  ║  └──────────────────────────────────────────────────────────────────────────────────┘     ║    │    ║
║  │  ║                                                                                          ║    │    ║
║  │  ║  ┌─────── TIER 3: SCAN EXECUTION LAYER (Deployment + Jobs) ───────────────────────┐     ║    │    ║
║  │  ║  │                                                                                  │     ║    │    ║
║  │  ║  │  ┌───────────────────┐  ┌───────────────────────────────────────────────────┐    │     ║    │    ║
║  │  ║  │  │ scan-orchestrator │  │         SCANNER CONNECTOR POOL                    │    │     ║    │    ║
║  │  ║  │  │ (Temporal Worker) │  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │    │     ║    │    ║
║  │  ║  │  │ ───────────────── │  │  │ burp-    │ │ tenable- │ │ fortify-         │   │    │     ║    │    ║
║  │  ║  │  │ Replicas: 3       │  │  │ connector│ │ connector│ │ connector        │   │    │     ║    │    ║
║  │  ║  │  │ CPU: 500m-1000m   │  │  │ R: 2-8   │ │ R: 2-6   │ │ R: 2-8           │   │    │     ║    │    ║
║  │  ║  │  │ Mem: 512Mi-1Gi    │  │  └──────────┘ └──────────┘ └──────────────────┘   │    │     ║    │    ║
║  │  ║  │  │ HPA: 3→15         │  │  ┌──────────┐                                     │    │     ║    │    ║
║  │  ║  │  └───────────────────┘  │  │ mobile-  │  Scan workers launch as K8s Jobs    │    │     ║    │    ║
║  │  ║  │                          │  │ connector│  with gVisor/Kata runtime class     │    │     ║    │    ║
║  │  ║  │                          │  │ R: 1-4   │  for sandboxed execution             │    │     ║    │    ║
║  │  ║  │                          │  └──────────┘                                     │    │     ║    │    ║
║  │  ║  │                          └───────────────────────────────────────────────────┘    │     ║    │    ║
║  │  ║  └──────────────────────────────────────────────────────────────────────────────────┘     ║    │    ║
║  │  ║                                                                                          ║    │    ║
║  │  ║  ┌─────── TIER 4: FRONTEND (Deployment) ──────────────────────────────────────────┐     ║    │    ║
║  │  ║  │  ┌─────────────────────────┐  ┌──────────────────────────────────────────┐      │     ║    │    ║
║  │  ║  │  │ analyst-portal          │  │ customer-portal                          │      │     ║    │    ║
║  │  ║  │  │ (Next.js SSR)           │  │ (Next.js SSR)                            │      │     ║    │    ║
║  │  ║  │  │ Replicas: 3, HPA: 3→8  │  │ Replicas: 3, HPA: 3→10                  │      │     ║    │    ║
║  │  ║  │  │ CPU: 250m-500m          │  │ CPU: 250m-500m                           │      │     ║    │    ║
║  │  ║  │  │ Mem: 256Mi-512Mi        │  │ Mem: 256Mi-512Mi                         │      │     ║    │    ║
║  │  ║  │  └─────────────────────────┘  └──────────────────────────────────────────┘      │     ║    │    ║
║  │  ║  └──────────────────────────────────────────────────────────────────────────────────┘     ║    │    ║
║  │  ╚═══════════════════════════════════════════════════════════════════════════════════════════╝    │    ║
║  │                                                                                                  │    ║
║  │  ╔═══════════════════════════════════════════════════════════════════════════════════════════╗    │    ║
║  │  ║              NAMESPACE: vapt-data  (Stateful Infrastructure)                             ║    │    ║
║  │  ║                                                                                          ║    │    ║
║  │  ║  ┌─────── DATABASE CLUSTER ────────────────────────────────────────────────────────┐     ║    │    ║
║  │  ║  │                                                                                  │     ║    │    ║
║  │  ║  │  ┌───────────────────────────────────────────────────────────────────────────┐    │     ║    │    ║
║  │  ║  │  │ POSTGRESQL 16 CLUSTER (CloudNativePG Operator)                            │    │     ║    │    ║
║  │  ║  │  │ ──────────────────────────────────────────                                │    │     ║    │    ║
║  │  ║  │  │ Primary (1) ──► Replica (2) │ Sync replication │ Auto-failover            │    │     ║    │    ║
║  │  ║  │  │ Storage: gp3-encrypted 500Gi │ PITR with WAL-G to S3                     │    │     ║    │    ║
║  │  ║  │  │ Extensions: pgvector, pg_cron, pg_stat_statements                         │    │     ║    │    ║
║  │  ║  │  │ Row-Level Security for tenant isolation                                    │    │     ║    │    ║
║  │  ║  │  │ Connection pooling: PgBouncer sidecar (max 200 connections)               │    │     ║    │    ║
║  │  ║  │  └───────────────────────────────────────────────────────────────────────────┘    │     ║    │    ║
║  │  ║  │                                                                                  │     ║    │    ║
║  │  ║  │  ┌───────────────────────────────────────────────────────────────────────────┐    │     ║    │    ║
║  │  ║  │  │ ELASTICSEARCH 8 CLUSTER (ECK Operator)                                    │    │     ║    │    ║
║  │  ║  │  │ ──────────────────────────────────────                                    │    │     ║    │    ║
║  │  ║  │  │ Master (3) │ Data (3) │ Coordinating (2)                                  │    │     ║    │    ║
║  │  ║  │  │ Data storage: gp3-encrypted 1Ti per data node                              │    │     ║    │    ║
║  │  ║  │  │ ILM policies: hot → warm → cold → delete                                  │    │     ║    │    ║
║  │  ║  │  └───────────────────────────────────────────────────────────────────────────┘    │     ║    │    ║
║  │  ║  └──────────────────────────────────────────────────────────────────────────────────┘     ║    │    ║
║  │  ║                                                                                          ║    │    ║
║  │  ║  ┌─────── QUEUE SYSTEM ────────────────────────────────────────────────────────────┐     ║    │    ║
║  │  ║  │                                                                                  │     ║    │    ║
║  │  ║  │  ┌───────────────────────────────────────────────────────────────────────────┐    │     ║    │    ║
║  │  ║  │  │ APACHE KAFKA CLUSTER (Strimzi Operator)                                   │    │     ║    │    ║
║  │  ║  │  │ ──────────────────────────────────────                                    │    │     ║    │    ║
║  │  ║  │  │ Brokers: 3 (multi-AZ) │ Replication factor: 3 │ min.insync.replicas: 2   │    │     ║    │    ║
║  │  ║  │  │ Storage: gp3-encrypted 500Gi per broker                                   │    │     ║    │    ║
║  │  ║  │  │ Topics: engagement.created, scan.requested, scan.completed,                │    │     ║    │    ║
║  │  ║  │  │         finding.normalized, finding.ai_enriched, finding.validated,         │    │     ║    │    ║
║  │  ║  │  │         report.generated, notification.dispatch                             │    │     ║    │    ║
║  │  ║  │  │ Schema Registry: Confluent Schema Registry (Avro)                          │    │     ║    │    ║
║  │  ║  │  │ Kafka Connect: S3 Sink, Elasticsearch Sink                                 │    │     ║    │    ║
║  │  ║  │  └───────────────────────────────────────────────────────────────────────────┘    │     ║    │    ║
║  │  ║  └──────────────────────────────────────────────────────────────────────────────────┘     ║    │    ║
║  │  ║                                                                                          ║    │    ║
║  │  ║  ┌─────── CACHE & ORCHESTRATION ───────────────────────────────────────────────────┐     ║    │    ║
║  │  ║  │                                                                                  │     ║    │    ║
║  │  ║  │  ┌──────────────────────────────┐  ┌────────────────────────────────────────┐    │     ║    │    ║
║  │  ║  │  │ REDIS 7 CLUSTER (Sentinel)   │  │ TEMPORAL SERVER                        │    │     ║    │    ║
║  │  ║  │  │ ──────────────────────────── │  │ ──────────────────────────────         │    │     ║    │    ║
║  │  ║  │  │ Master (1) + Replica (2)     │  │ Frontend (2) │ History (3)             │    │     ║    │    ║
║  │  ║  │  │ + Sentinel (3)               │  │ Matching (3) │ Worker (3)              │    │     ║    │    ║
║  │  ║  │  │ Memory: 16Gi per node        │  │ Visibility store: Elasticsearch        │    │     ║    │    ║
║  │  ║  │  │ Maxmemory policy: allkeys-lru│  │ Persistence: PostgreSQL                │    │     ║    │    ║
║  │  ║  │  └──────────────────────────────┘  └────────────────────────────────────────┘    │     ║    │    ║
║  │  ║  └──────────────────────────────────────────────────────────────────────────────────┘     ║    │    ║
║  │  ║                                                                                          ║    │    ║
║  │  ║  ┌─────── VAULT & OBJECT STORAGE ──────────────────────────────────────────────────┐     ║    │    ║
║  │  ║  │                                                                                  │     ║    │    ║
║  │  ║  │  ┌──────────────────────────────┐  ┌────────────────────────────────────────┐    │     ║    │    ║
║  │  ║  │  │ HASHICORP VAULT (HA Mode)    │  │ MINIO (Distributed Mode)               │    │     ║    │    ║
║  │  ║  │  │ ──────────────────────────── │  │ ──────────────────────────────         │    │     ║    │    ║
║  │  ║  │  │ Nodes: 3 (Raft storage)     │  │ Nodes: 4 (erasure coding)              │    │     ║    │    ║
║  │  ║  │  │ Auto-unseal: AWS KMS /       │  │ Storage: gp3-encrypted 1Ti per node    │    │     ║    │    ║
║  │  ║  │  │   Azure Key Vault            │  │ Bucket isolation per tenant            │    │     ║    │    ║
║  │  ║  │  │ Secret engines: KV v2,       │  │ Lifecycle policies: 90-day retention   │    │     ║    │    ║
║  │  ║  │  │   Transit, Database          │  │ Server-side encryption (SSE-S3)        │    │     ║    │    ║
║  │  ║  │  │ Audit backend: file + syslog │  │ Pre-signed URLs for portal downloads   │    │     ║    │    ║
║  │  ║  │  └──────────────────────────────┘  └────────────────────────────────────────┘    │     ║    │    ║
║  │  ║  └──────────────────────────────────────────────────────────────────────────────────┘     ║    │    ║
║  │  ╚═══════════════════════════════════════════════════════════════════════════════════════════╝    │    ║
║  │                                                                                                  │    ║
║  │  ╔═══════════════════════════════════════════════════════════════════════════════════════════╗    │    ║
║  │  ║              NAMESPACE: vapt-monitoring  (Observability Stack)                            ║    │    ║
║  │  ║                                                                                          ║    │    ║
║  │  ║  ┌──────────────────┐ ┌──────────────┐ ┌───────────┐ ┌──────────────┐ ┌──────────────┐  ║    │    ║
║  │  ║  │ Prometheus       │ │ Grafana      │ │ Loki      │ │ Tempo        │ │ Alertmanager │  ║    │    ║
║  │  ║  │ (metrics)        │ │ (dashboards) │ │ (logs)    │ │ (traces)     │ │ (alerts)     │  ║    │    ║
║  │  ║  │ Retain: 30d      │ │ 40+ panels   │ │ Retain:   │ │ Retain: 7d   │ │ PagerDuty,   │  ║    │    ║
║  │  ║  │ Thanos sidecar   │ │              │ │ 30d       │ │ S3 backend   │ │ Slack, OpsGe │  ║    │    ║
║  │  ║  └──────────────────┘ └──────────────┘ └───────────┘ └──────────────┘ └──────────────┘  ║    │    ║
║  │  ╚═══════════════════════════════════════════════════════════════════════════════════════════╝    │    ║
║  │                                                                                                  │    ║
║  │  ╔═══════════════════════════════════════════════════════════════════════════════════════════╗    │    ║
║  │  ║              NAMESPACE: vapt-security  (Security Infrastructure)                         ║    │    ║
║  │  ║                                                                                          ║    │    ║
║  │  ║  ┌──────────────────┐ ┌──────────────┐ ┌───────────────────┐ ┌───────────────────────┐  ║    │    ║
║  │  ║  │ Keycloak (IAM)   │ │ Falco        │ │ Kyverno           │ │ Sealed Secrets        │  ║    │    ║
║  │  ║  │ Replicas: 2      │ │ (runtime     │ │ (policy engine)   │ │ (encrypted secrets    │  ║    │    ║
║  │  ║  │ OIDC/SAML        │ │  security)   │ │ • Image allowlist │ │  in Git)              │  ║    │    ║
║  │  ║  │ MFA enforcement  │ │ • Syscall    │ │ • No privileged   │ └───────────────────────┘  ║    │    ║
║  │  ║  │ RBAC + ABAC      │ │   monitoring │ │ • Resource quotas │                             ║    │    ║
║  │  ║  └──────────────────┘ └──────────────┘ └───────────────────┘                             ║    │    ║
║  │  ╚═══════════════════════════════════════════════════════════════════════════════════════════╝    │    ║
║  │                                                                                                  │    ║
║  │  ┌── NODE POOLS ─────────────────────────────────────────────────────────────────────────────┐   │    ║
║  │  │                                                                                            │   │    ║
║  │  │  ┌────────────────────┐  ┌──────────────────┐  ┌────────────────┐  ┌───────────────────┐  │   │    ║
║  │  │  │ system-pool        │  │ app-pool          │  │ scan-pool      │  │ data-pool         │  │   │    ║
║  │  │  │ ────────────────── │  │ ──────────────── │  │ ────────────── │  │ ───────────────── │  │   │    ║
║  │  │  │ t3.large (2/8Gi)  │  │ m6i.xlarge       │  │ c6i.2xlarge    │  │ r6i.2xlarge       │  │   │    ║
║  │  │  │ Nodes: 3 (fixed)  │  │ (4/16Gi)         │  │ (8/16Gi)       │  │ (8/64Gi)          │  │   │    ║
║  │  │  │ System components  │  │ Nodes: 3-20      │  │ Nodes: 2-30    │  │ Nodes: 3-6        │  │   │    ║
║  │  │  │ + monitoring       │  │ API services     │  │ Scanner workers│  │ DB + ES + Kafka   │  │   │    ║
║  │  │  │                    │  │ + frontends       │  │ gVisor runtime │  │ + Redis + Vault   │  │   │    ║
║  │  │  │ Taint: system-only │  │ No taint          │  │ Taint: scan    │  │ Taint: data-only  │  │   │    ║
║  │  │  └────────────────────┘  └──────────────────┘  └────────────────┘  └───────────────────┘  │   │    ║
║  │  └────────────────────────────────────────────────────────────────────────────────────────────┘   │    ║
║  └──────────────────────────────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                                          ║
║  ┌── EXTERNAL MANAGED SERVICES (Optional cloud-native alternatives) ────────────────────────────────┐   ║
║  │  • AWS RDS Aurora PostgreSQL / Azure Database for PostgreSQL (instead of in-cluster PG)           │   ║
║  │  • Amazon MSK / Azure Event Hubs (instead of in-cluster Kafka)                                    │   ║
║  │  • Amazon ElastiCache / Azure Cache for Redis (instead of in-cluster Redis)                       │   ║
║  │  • AWS S3 / Azure Blob Storage (instead of MinIO)                                                 │   ║
║  │  • Amazon OpenSearch / Elastic Cloud (instead of in-cluster ES)                                   │   ║
║  └───────────────────────────────────────────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

### Network Topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    VPC / VNET (10.0.0.0/16)                             │
│                                                                         │
│  ┌─── Public Subnets (10.0.0.0/20) ──────────────────────────────┐     │
│  │  • NLB / ALB (Kong ingress)                                    │     │
│  │  • NAT Gateway                                                 │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                         │
│  ┌─── Private Subnets (10.0.16.0/20) ─ AZ-a ──┐                       │
│  │  K8s worker nodes (app-pool, scan-pool)      │                       │
│  │  Pod CIDR: 10.0.32.0/19                      │                       │
│  └──────────────────────────────────────────────┘                       │
│  ┌─── Private Subnets (10.0.48.0/20) ─ AZ-b ──┐                       │
│  │  K8s worker nodes (app-pool, scan-pool)      │                       │
│  └──────────────────────────────────────────────┘                       │
│  ┌─── Private Subnets (10.0.64.0/20) ─ AZ-c ──┐                       │
│  │  K8s worker nodes (app-pool, scan-pool)      │                       │
│  └──────────────────────────────────────────────┘                       │
│                                                                         │
│  ┌─── Data Subnets (10.0.128.0/20) ─────────────────────────────┐     │
│  │  PostgreSQL, Elasticsearch, Kafka, Redis, Vault, MinIO        │     │
│  │  No internet access — only private link / service endpoints   │     │
│  └────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Scaling Strategy

### 2.1 Node Pool Auto-Scaling

| Node Pool | Instance Type | Min | Max | Scale Trigger | Taint |
|-----------|--------------|-----|-----|---------------|-------|
| system-pool | t3.large (2 vCPU, 8 GiB) | 3 | 3 | Fixed | `node-role=system:NoSchedule` |
| app-pool | m6i.xlarge (4 vCPU, 16 GiB) | 3 | 20 | CPU > 70% for 3m | None |
| scan-pool | c6i.2xlarge (8 vCPU, 16 GiB) | 2 | 30 | Pending pods | `workload=scan:NoSchedule` |
| data-pool | r6i.2xlarge (8 vCPU, 64 GiB) | 3 | 6 | Manual | `workload=data:NoSchedule` |

### 2.2 Horizontal Pod Autoscaler (HPA) Policies

| Service | Min | Max | Target CPU | Target Memory | Custom Metric |
|---------|-----|-----|------------|---------------|---------------|
| engagement-svc | 3 | 10 | 70% | — | — |
| asset-discovery-svc | 2 | 6 | 70% | — | — |
| analyst-workflow-svc | 3 | 12 | 65% | — | `queue_depth > 50` |
| findings-normalization-svc | 3 | 15 | 60% | 75% | `kafka_lag > 1000` |
| ai-analyst-assistant | 3 | 10 | 50% | — | `pending_analyses > 20` |
| reporting-service | 2 | 8 | 60% | 70% | `queue_depth > 10` |
| scan-orchestrator | 3 | 15 | 60% | — | `pending_scans > 5` |
| burp-connector | 2 | 8 | 70% | — | `active_scans > 3` |
| tenable-connector | 2 | 6 | 70% | — | `active_scans > 3` |
| fortify-connector | 2 | 8 | 60% | — | `active_scans > 3` |
| mobile-connector | 1 | 4 | 70% | — | — |
| compliance-engine | 2 | 6 | 70% | — | — |
| teams-bot-svc | 2 | 4 | 60% | — | — |
| analyst-portal | 3 | 8 | 70% | — | — |
| customer-portal | 3 | 10 | 70% | — | `active_sessions > 500` |

### 2.3 Vertical Pod Autoscaler (VPA) Recommendations

VPA runs in **recommendation mode** for all services. Resource requests are periodically reviewed and adjusted during maintenance windows. VPA is NOT in auto mode to prevent disruptive restarts.

### 2.4 Scan Worker Scaling Strategy

```
                    SCAN WORKER SCALING FLOW
                    ═══════════════════════

  ┌──────────────────┐
  │ scan.requested   │  Kafka event
  │ event arrives    │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐       ┌──────────────────────────┐
  │ Scan Orchestrator│──────►│ Check resource quotas     │
  │ (Temporal)       │       │ per tenant (max 5 scans)  │
  └────────┬─────────┘       └──────────────────────────┘
           │
           ▼
  ┌──────────────────┐
  │ Create K8s Job   │  Runtime: gVisor (runsc)
  │ for scanner type │  Resource limits enforced
  └────────┬─────────┘  TTL: 4h max
           │
           ▼
  ┌──────────────────┐
  │ Karpenter /      │  Scale node pool if no
  │ Cluster          │  schedulable capacity
  │ Autoscaler       │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ Scan executes    │  Results → Object Storage
  │ in sandbox       │  Events → Kafka
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ Job TTL cleanup  │  Node scale-down after
  │ Node cooldown    │  10m idle (Karpenter)
  └──────────────────┘
```

### 2.5 Database Scaling Strategy

| Component | Read Scaling | Write Scaling | Sharding |
|-----------|-------------|---------------|----------|
| PostgreSQL | Read replicas (2→4) | Vertical scaling | Citus extension at >1000 tenants |
| Elasticsearch | Data nodes (3→6) | Index-per-month | ILM hot/warm/cold |
| Redis | Replica reads | Redis Cluster mode at >32Gi | Keyspace partitioning by tenant |
| Kafka | Partition count per topic | Broker count (3→5) | Topic partitioning by tenant_id |

### 2.6 Multi-Region Strategy (Future)

```
  Region A (Primary)                Region B (DR / Active-Active)
  ─────────────────                 ────────────────────────────
  Full K8s cluster                  Full K8s cluster
  PostgreSQL primary                PostgreSQL standby (async)
  Kafka MirrorMaker 2       ◄────► Kafka MirrorMaker 2
  MinIO replication          ◄────► MinIO replication
  DNS failover via Route53 / Traffic Manager
  RPO: < 5 minutes │ RTO: < 15 minutes
```

---

## 3. Monitoring Stack

### 3.1 Architecture

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    OBSERVABILITY STACK (vapt-monitoring namespace)           ║
║                                                                             ║
║  ┌────────────────────────────────────────────────────────────────────────┐  ║
║  │                          GRAFANA (Unified UI)                          │  ║
║  │  ┌────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────────┐  │  ║
║  │  │ Metrics    │ │ Logs        │ │ Traces      │ │ Alerts           │  │  ║
║  │  │ Dashboards │ │ Explorer    │ │ Explorer    │ │ Dashboard        │  │  ║
║  │  └──────┬─────┘ └──────┬──────┘ └──────┬──────┘ └──────────────────┘  │  ║
║  │         │              │               │                               │  ║
║  └─────────┼──────────────┼───────────────┼───────────────────────────────┘  ║
║            │              │               │                                  ║
║    ┌───────▼───────┐ ┌────▼──────┐ ┌──────▼──────┐  ┌──────────────────┐    ║
║    │  PROMETHEUS   │ │   LOKI    │ │   TEMPO     │  │  ALERTMANAGER    │    ║
║    │  ───────────  │ │  ──────── │ │  ────────── │  │  ──────────────  │    ║
║    │  • Service    │ │  • Log    │ │  • Distrib. │  │  • Routing       │    ║
║    │    discovery  │ │    aggr.  │ │    tracing   │  │  • Dedup         │    ║
║    │  • PromQL     │ │  • LogQL  │ │  • TraceQL  │  │  • Silencing     │    ║
║    │  • 30d local  │ │  • S3     │ │  • S3       │  │  • Escalation    │    ║
║    │  • Thanos     │ │    backend│ │    backend   │  │                  │    ║
║    │    sidecar    │ └───────────┘ └─────────────┘  └──────────────────┘    ║
║    └───────────────┘                                                         ║
║                                                                             ║
║    ┌── DATA COLLECTION AGENTS ─────────────────────────────────────────┐    ║
║    │                                                                    │    ║
║    │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │    ║
║    │  │ Prometheus   │  │ Promtail     │  │ OpenTelemetry Collector │  │    ║
║    │  │ ServiceMonitor│ │ (DaemonSet)  │  │ (DaemonSet)             │  │    ║
║    │  │ PodMonitor   │  │ → Loki       │  │ → Tempo                 │  │    ║
║    │  └──────────────┘  └──────────────┘  └─────────────────────────┘  │    ║
║    └────────────────────────────────────────────────────────────────────┘    ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### 3.2 Grafana Dashboard Inventory

| Dashboard | Key Panels | Data Source |
|-----------|-----------|-------------|
| **Platform Overview** | Total engagements, active scans, findings pipeline throughput, error rate | Prometheus |
| **Service Health** | Per-service: request rate, latency (p50/p95/p99), error rate, saturation | Prometheus |
| **Kafka Pipeline** | Consumer lag per group, message throughput, partition distribution | Prometheus (JMX) |
| **Scan Execution** | Active scans, queue depth, scan duration, failure rate by scanner type | Prometheus + Loki |
| **AI Analyst** | LLM call latency, token usage, cache hit rate, analysis throughput | Prometheus |
| **Report Generation** | Generation queue, render duration, PDF/DOCX sizes, failure rate | Prometheus |
| **PostgreSQL** | Connections, query latency, replication lag, table bloat, cache hit ratio | Prometheus (pg_exporter) |
| **Elasticsearch** | Cluster health, indexing rate, search latency, shard allocation | Prometheus (ES exporter) |
| **Kafka Cluster** | Broker health, under-replicated partitions, ISR shrinks, disk usage | Prometheus (JMX) |
| **Redis** | Memory usage, hit rate, connected clients, evictions, replication lag | Prometheus (redis_exporter) |
| **Vault** | Seal status, token creation rate, secret access audit, lease count | Prometheus (vault metrics) |
| **MinIO** | Bucket sizes, request rate, error rate, disk usage | Prometheus (MinIO metrics) |
| **Node Resources** | CPU/memory/disk/network per node pool, pod density, OOM events | Prometheus (node_exporter) |
| **Tenant Activity** | Per-tenant: active engagements, scan volume, finding count, report gen | Prometheus (custom) |
| **Security Events** | Falco alerts, failed auth, API abuse, privilege escalation attempts | Loki + Prometheus |
| **SLA Compliance** | Engagement SLA adherence, scan turnaround, report delivery time | Prometheus |

### 3.3 Alert Rules

```yaml
# ── Critical (PagerDuty — immediate page) ──
- PostgreSQL primary down or replication lag > 30s
- Kafka broker offline or under-replicated partitions > 0 for 5m
- Vault sealed
- Certificate expiry < 7 days
- API error rate > 5% for 5m
- Scan worker OOM kills > 3 in 10m
- Node pool capacity < 20% remaining
- Data pool disk usage > 85%

# ── Warning (Slack — business hours) ──
- Service restart count > 3 in 15m
- AI analyst LLM latency p99 > 30s
- Report generation queue depth > 20
- Kafka consumer lag > 5000 messages for 10m
- Redis memory usage > 80%
- Elasticsearch cluster yellow status
- Findings normalization backlog > 10000
- Pod pending > 5m (scheduling issues)

# ── Info (Slack — low priority) ──
- New tenant onboarded
- Engagement completed
- VPA recommendation differs > 30% from current
- Certificate renewed successfully
- Database backup completed
```

### 3.4 SLO Definitions

| Service | SLI | SLO Target | Error Budget (30d) |
|---------|-----|------------|-------------------|
| API Gateway | Availability (non-5xx) | 99.9% | 43.2 minutes |
| Core API Services | Latency p99 < 500ms | 99.5% | 3.6 hours |
| Scan Pipeline | Scan completion within SLA | 99.0% | 7.2 hours |
| Report Generation | Generation success rate | 99.5% | 3.6 hours |
| AI Analyst | Analysis completion rate | 98.0% | 14.4 hours |
| Data Layer | Database availability | 99.99% | 4.3 minutes |

### 3.5 Log Aggregation Strategy

```
Application Pods                      Loki
─────────────────                     ────
stdout/stderr (JSON) ──► Promtail ──► Loki ──► S3 (long-term)
                          (DaemonSet)
Structured log format:
{
  "timestamp": "2026-03-15T10:30:00Z",
  "level": "info",
  "service": "reporting-service",
  "tenant_id": "t-abc123",           ← Tenant context for filtering
  "engagement_id": "e-def456",
  "trace_id": "abc123def456",        ← Correlate with Tempo
  "message": "report_generated",
  "duration_ms": 4520,
  "report_type": "full_technical"
}

Retention policy:
  - Hot (SSD):   7 days  — full query
  - Warm (S3):   30 days — indexed labels only
  - Cold (S3 IA): 365 days — compliance archive
```

### 3.6 Distributed Tracing

```
   Client Request
        │
        ▼
   Kong Gateway ──────────── span: gateway.request
        │
        ▼
   Istio Envoy ──────────── span: mesh.inbound
        │
        ▼
   Engagement Service ────── span: engagement.create
        │    │
        │    └──► Asset Service ──── span: asset.register
        │
        ▼
   Kafka Producer ─────────── span: kafka.produce(scan.requested)
        │
        ▼
   Scan Orchestrator ──────── span: scan.orchestrate
        │
        ├──► Burp Connector ─── span: burp.scan (long-running)
        └──► Tenable Connector── span: tenable.scan
              │
              ▼
         Kafka Producer ────── span: kafka.produce(scan.completed)
              │
              ▼
         Findings Service ──── span: finding.normalize
              │
              ▼
         AI Analyst ─────────── span: ai.analyze
              │
              ▼
         Reporting Service ──── span: report.generate

   Trace propagation: W3C TraceContext headers via Istio + OTel SDK
   Sampling: 10% of requests, 100% of errors, 100% of slow requests (>5s)
```

---

## 4. Namespace Organization

| Namespace | Purpose | Resource Quota |
|-----------|---------|---------------|
| `vapt-platform` | Application workloads (13 services + 2 frontends) | CPU: 60 cores, Mem: 120Gi |
| `vapt-data` | Stateful infrastructure (PG, ES, Kafka, Redis, Vault, MinIO, Temporal) | CPU: 40 cores, Mem: 256Gi |
| `vapt-monitoring` | Observability stack (Prometheus, Grafana, Loki, Tempo, Alertmanager) | CPU: 8 cores, Mem: 32Gi |
| `vapt-security` | Security infrastructure (Keycloak, Falco, Kyverno, Sealed Secrets) | CPU: 4 cores, Mem: 16Gi |
| `ingress-system` | Kong, cert-manager, external-dns | CPU: 4 cores, Mem: 8Gi |
| `istio-system` | Istio control plane | CPU: 4 cores, Mem: 8Gi |

---

## 5. Security Hardening

### 5.1 Pod Security Standards

- All namespaces enforce `restricted` Pod Security Standard
- Exception: `scan-pool` nodes allow `baseline` for gVisor runtime scanner containers
- No privileged containers, no host network, no host PID
- Read-only root filesystem for all application pods
- Non-root user (UID 1000) for all containers
- `seccomp` profile: RuntimeDefault

### 5.2 Network Policies

```
Default: deny-all ingress + egress in vapt-platform namespace

Allow rules:
  Kong → all services in vapt-platform (port 8080-8091)
  vapt-platform → vapt-data (database ports only)
  vapt-platform → vapt-platform (service-to-service via Istio mTLS)
  vapt-platform → external (scanner APIs — specific CIDRs only)
  vapt-monitoring → all namespaces (metrics scrape ports)
  vapt-data → vapt-data (cluster communication)
  Deny: vapt-data → internet (no egress)
```

### 5.3 Secret Management

```
Application secrets flow:
  1. Developer encrypts secret → SealedSecret CR → Git
  2. Sealed Secrets controller decrypts → K8s Secret
  3. Application reads K8s Secret (mounted as volume, never env var)

Scanner credentials flow:
  1. Customer submits credentials → API → Vault
  2. Scan worker → Vault (short-lived lease, 1h TTL)
  3. Vault audit log records every access
  4. Credential auto-rotated on schedule
```

---

## 6. Deployment Strategy

### 6.1 GitOps with ArgoCD

```
Git Repository (source of truth)
        │
        ▼
  ArgoCD Application Controller
        │
        ├──► vapt-platform (auto-sync, self-heal)
        ├──► vapt-data (manual sync — stateful changes need approval)
        ├──► vapt-monitoring (auto-sync)
        └──► vapt-security (manual sync)

Deployment strategy per service:
  - API services: Rolling update (maxSurge: 1, maxUnavailable: 0)
  - Frontends: Blue-green via Istio traffic shifting
  - Stateful: Manual rolling (database, Kafka — one node at a time)
  - Scanner connectors: Rolling update
```

### 6.2 CI/CD Pipeline

```
  Code Push → GitHub Actions
        │
        ├── Lint + Unit Tests
        ├── SAST (Semgrep) + SCA (Trivy)
        ├── Container build (Kaniko)
        ├── Image scan (Trivy)
        ├── Push to ECR/ACR/GAR
        ├── Update Kustomize overlay (image tag)
        └── ArgoCD detects change → deploy to staging → promote to prod
```

---

## 7. Disaster Recovery

| Component | Backup Method | Frequency | Retention | RTO | RPO |
|-----------|-------------|-----------|-----------|-----|-----|
| PostgreSQL | WAL-G continuous archiving to S3 | Continuous + daily full | 30 days | 15 min | 5 min |
| Elasticsearch | Snapshot to S3 | Every 6 hours | 14 days | 30 min | 6 hours |
| Kafka | MirrorMaker 2 to DR cluster | Continuous | 7 days | 10 min | 1 min |
| Redis | RDB snapshots to S3 | Every 1 hour | 7 days | 5 min | 1 hour |
| Vault | Raft snapshots to S3 | Every 1 hour | 90 days | 10 min | 1 hour |
| MinIO | Bucket replication to DR | Continuous | Same as source | 15 min | 5 min |
| etcd | Velero backup | Every 6 hours | 14 days | 30 min | 6 hours |

---

## 8. Cost Estimation (AWS, us-east-1)

| Component | Instance / SKU | Count | Monthly Cost |
|-----------|---------------|-------|-------------|
| EKS Control Plane | — | 1 | $73 |
| system-pool | t3.large | 3 | $180 |
| app-pool | m6i.xlarge | 3-20 | $432-$2,880 |
| scan-pool | c6i.2xlarge | 2-30 | $490-$7,344 |
| data-pool | r6i.2xlarge | 3-6 | $1,134-$2,268 |
| EBS (gp3) | 500Gi × PG + 1Ti × ES + 500Gi × Kafka | — | ~$1,200 |
| S3 (backups + reports) | — | ~5 TB | ~$115 |
| NAT Gateway | — | 3 (multi-AZ) | $100 |
| NLB | — | 1 | $22 + data |
| **Baseline estimate** | | | **~$4,000-$14,000/mo** |

*Scan-pool cost varies dramatically with scan volume. Use Spot instances for scan-pool to reduce by ~60%.*
