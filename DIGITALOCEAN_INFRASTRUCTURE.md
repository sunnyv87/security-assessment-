# DigitalOcean Infrastructure Design — AI-Driven VAPT Orchestration Platform

## Practical Hosting Blueprint for MSSP Operations

---

## A. Recommended DigitalOcean Architecture Summary

```
╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                              DIGITALOCEAN INFRASTRUCTURE OVERVIEW                                  ║
║                                                                                                    ║
║  ┌── EXTERNAL EDGE ────────────────────────────────────────────────────────────────────────────┐   ║
║  │  Cloudflare (WAF + CDN + DDoS)  ──►  DO Load Balancer (TLS termination)                    │   ║
║  └────────────────────────────────────────────────────┬───────────────────────────────────────┘   ║
║                                                        │                                          ║
║  ┌── VPC: vapt-production (10.10.0.0/16) ─────────────┼──────────────────────────────────────┐   ║
║  │                                                     │                                      │   ║
║  │  ┌── DOKS CLUSTER: vapt-prod ──────────────────────┼─────────────────────────────────┐    │   ║
║  │  │                                                  │                                 │    │   ║
║  │  │  ┌─ Node Pool: system (General Purpose) ────────┐│                                 │    │   ║
║  │  │  │  2× gp-4vcpu-16gb  ($63/mo each)             ││                                 │    │   ║
║  │  │  │  Kong Ingress, cert-manager, monitoring       ││                                 │    │   ║
║  │  │  └───────────────────────────────────────────────┘│                                 │    │   ║
║  │  │                                                    │                                 │    │   ║
║  │  │  ┌─ Node Pool: app (General Purpose) ────────────┐│                                 │    │   ║
║  │  │  │  3-10× gp-4vcpu-16gb  ($63/mo each)          ││                                 │    │   ║
║  │  │  │  All 13 microservices + 2 frontends           ││                                 │    │   ║
║  │  │  │  HPA auto-scaling                              ││                                 │    │   ║
║  │  │  └───────────────────────────────────────────────┘│                                 │    │   ║
║  │  │                                                    │                                 │    │   ║
║  │  │  ┌─ Node Pool: scan-workers (CPU-Optimized) ────┐ │                                 │    │   ║
║  │  │  │  0-8× cpu-4vcpu-8gb  ($84/mo each)           │ │                                 │    │   ║
║  │  │  │  Burp/Tenable/Fortify/MobSF connectors       │ │                                 │    │   ║
║  │  │  │  Scale-to-zero when idle                       │ │                                 │    │   ║
║  │  │  │  Taint: workload=scan:NoSchedule              │ │                                 │    │   ║
║  │  │  └───────────────────────────────────────────────┘ │                                 │    │   ║
║  │  │                                                     │                                │    │   ║
║  │  │  ┌─ Node Pool: ai-report (General Purpose) ──────┐│                                 │    │   ║
║  │  │  │  1-4× gp-8vcpu-32gb ($126/mo each)            ││                                 │    │   ║
║  │  │  │  AI Analyst Assistant + Report Generation      ││                                 │    │   ║
║  │  │  │  Taint: workload=ai:NoSchedule                 ││                                 │    │   ║
║  │  │  └────────────────────────────────────────────────┘│                                 │    │   ║
║  │  └────────────────────────────────────────────────────┘                                 │    │   ║
║  │                                                                                         │    │   ║
║  │  ┌── MANAGED SERVICES ──────────────────────────────────────────────────────────────┐   │   ║
║  │  │                                                                                   │   │   ║
║  │  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────────┐    │   │   ║
║  │  │  │  Managed         │  │  Managed         │  │  Managed Kafka               │    │   │   ║
║  │  │  │  PostgreSQL 16   │  │  Valkey (Redis)  │  │  3-node cluster              │    │   │   ║
║  │  │  │  HA Standby      │  │  HA 2-node       │  │  Event backbone              │    │   │   ║
║  │  │  │  4 vCPU / 8 GB   │  │  2 GB            │  │                              │    │   │   ║
║  │  │  └──────────────────┘  └──────────────────┘  └──────────────────────────────┘    │   │   ║
║  │  └───────────────────────────────────────────────────────────────────────────────────┘   │   ║
║  │                                                                                         │    │   ║
║  │  ┌── STANDALONE DROPLETS ───────────────────────────────────────────────────────────┐   │   ║
║  │  │                                                                                   │   │   ║
║  │  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────────┐    │   │   ║
║  │  │  │  Temporal Server  │  │  HashiCorp Vault │  │  Elasticsearch               │    │   │   ║
║  │  │  │  gp-4vcpu-16gb   │  │  gp-2vcpu-8gb    │  │  gp-4vcpu-16gb              │    │   │   ║
║  │  │  │  + Block Storage  │  │  + Block Storage │  │  + 500GB Block Storage       │    │   │   ║
║  │  │  └──────────────────┘  └──────────────────┘  └──────────────────────────────┘    │   │   ║
║  │  └───────────────────────────────────────────────────────────────────────────────────┘   │   ║
║  │                                                                                         │    │   ║
║  │  ┌── STORAGE ───────────────────────────────────────────────────────────────────────┐   │   ║
║  │  │                                                                                   │   │   ║
║  │  │  Spaces (S3-compat): scan artifacts, reports, evidence, backups                   │   │   ║
║  │  │  Block Storage Volumes: DB data, ES indices, Vault storage, Temporal persistence  │   │   ║
║  │  └───────────────────────────────────────────────────────────────────────────────────┘   │   ║
║  └─────────────────────────────────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## B. DigitalOcean Services Required

### B.1 Compute

| Service | Purpose | Why This Service |
|---------|---------|------------------|
| **DOKS (Managed Kubernetes)** | All microservices, frontends, connectors, workers | Free control plane, HA option ($40/mo), node pool auto-scaling, scale-to-zero for scan workers. Matches existing K8s-native architecture without redesign. |
| **Droplets (General Purpose)** | Temporal server, Vault, Elasticsearch | These are stateful, long-running infrastructure services that need dedicated compute with attached block storage. Running them on K8s adds operational complexity without benefit at initial scale. |

### B.2 Data & Messaging

| Service | Purpose | Why This Service |
|---------|---------|------------------|
| **Managed PostgreSQL** | Primary OLTP database for all services (engagements, assets, findings, users, audit logs) | Automated backups, failover, maintenance. Platform uses PostgreSQL 16 with RLS for tenant isolation — fully compatible with DO Managed PG. |
| **Managed Valkey (Redis-compatible)** | Session store, rate limiting, caching, Pub/Sub for real-time features | Drop-in Redis replacement. Managed HA eliminates operational overhead for a critical caching layer. |
| **Managed Kafka** | Event bus backbone — scan.requested, finding.normalized, notification.dispatch, etc. | Platform architecture is heavily event-driven (8+ Kafka topics). DO Managed Kafka gives 3-node HA clusters with no broker management. |

### B.3 Networking

| Service | Purpose | Why This Service |
|---------|---------|------------------|
| **VPC** | Network isolation per environment | All resources (DOKS, Droplets, managed DBs) placed in a private VPC. Free on DO. |
| **Load Balancer** | Public ingress for HTTPS traffic | Routes to Kong Ingress Controller inside DOKS. TLS termination at LB or passthrough to Kong. $12/mo. |
| **Cloud Firewall** | Network-level access control | Restrict SSH, DB ports, inter-service access. Applied to Droplets and node pools. Free. |
| **Reserved IPs** | Stable egress IPs for scanner allowlisting | Customers may need to allowlist scan source IPs in their firewalls. Reserved IPs on NAT Droplets provide this. |

### B.4 Storage

| Service | Purpose | Why This Service |
|---------|---------|------------------|
| **Spaces Object Storage** | Scan results, reports (PDF/DOCX), evidence files, APK/IPA uploads, source snapshots, log archives, DB backups | S3-compatible API (platform already uses MinIO/S3). Built-in CDN. $5/mo base for 250 GB. No per-request fees. |
| **Spaces Cold Storage** | Long-term audit log retention, compliance archives (7-year retention per architecture) | $0.007/GB/mo — 10x cheaper than standard. Perfect for immutable audit trails. |
| **Block Storage Volumes** | Elasticsearch indices, Temporal persistence, Vault storage | Attached to stateful Droplets. Persistent across reboots. Snapshots available. $10/mo per 100 GB. |

### B.5 Security & Operations

| Service | Purpose | Why This Service |
|---------|---------|------------------|
| **Container Registry (DOCR)** | Private Docker image hosting for all 15+ service images | Integrated with DOKS for seamless pulls. Vulnerability scanning available. Starts at $5/mo (500 MB). |
| **DO Monitoring + Alerts** | Infrastructure-level metrics and alerting | Free built-in CPU/memory/disk/bandwidth alerts for Droplets and DOKS nodes. |
| **Uptime Checks** | Endpoint health monitoring | Free external HTTP/HTTPS checks for portal and API gateway availability. |

### B.6 External Services (Not on DO — Required)

| Service | Purpose | Why External |
|---------|---------|--------------|
| **Cloudflare** (Free/Pro) | WAF, DDoS protection, CDN for static assets | DO has no native WAF. Cloudflare Pro ($20/mo) provides OWASP ruleset, rate limiting, and global edge caching. Essential for MSSP security posture. |
| **Keycloak** (self-hosted on DOKS) | Identity provider — OIDC/SAML, RBAC+ABAC, MFA | Runs as a K8s deployment. No external service needed. |
| **HashiCorp Vault** (self-hosted on Droplet) | Credential vault — customer scan credentials, transit encryption, secret rotation | Runs on dedicated Droplet with HA Raft storage. DO has no native secrets manager equivalent. |
| **Temporal.io** (self-hosted on Droplet) | Workflow orchestration for scan pipelines | No DO equivalent. Self-hosted on Droplet with PostgreSQL backend (can share managed PG). |

---

## C. Instance Counts and Sizes — MVP / Pilot Deployment

**Assumptions:** 1-5 concurrent customer engagements, 1-3 concurrent scans, 3-5 analyst users, single-region.

### DOKS Cluster: `vapt-mvp`

| Node Pool | Node Size | Count | Auto-scale | Monthly Cost |
|-----------|-----------|-------|------------|-------------|
| **system** | General Purpose 2 vCPU / 8 GB (`gp-2vcpu-8gb`) | 2 (fixed) | No | 2 × $63 = **$126** |
| **app** | General Purpose 4 vCPU / 16 GB (`gp-4vcpu-16gb`) | 2–4 | Yes | 2-4 × $126 = **$252–$504** |
| **scan-workers** | CPU-Optimized 4 vCPU / 8 GB (`c-4vcpu-8gb`) | 0–2 | Yes (scale-to-zero) | 0-2 × $84 = **$0–$168** |

- **Control Plane HA:** No ($0) — acceptable for MVP
- **Total DOKS nodes:** 4-8

### Managed Databases

| Service | Plan | HA | Monthly Cost |
|---------|------|-----|-------------|
| **PostgreSQL 16** | 2 vCPU / 4 GB / 60 GB disk | Standby node | ~**$75** (primary + standby) |
| **Valkey (Redis)** | 1 vCPU / 2 GB | Single node | **$30** |
| **Kafka** | 3-node shared vCPU / 6 GB | Built-in (3-node) | **$147** |

### Standalone Droplets

| Service | Droplet Size | Block Storage | Monthly Cost |
|---------|-------------|---------------|-------------|
| **Temporal Server** | General Purpose 2 vCPU / 8 GB | 50 GB Volume | $63 + $5 = **$68** |
| **HashiCorp Vault** | Basic 2 vCPU / 4 GB | 20 GB Volume | $24 + $2 = **$26** |
| **Elasticsearch** | General Purpose 2 vCPU / 8 GB | 200 GB Volume | $63 + $20 = **$83** |

### Networking & Storage

| Service | Spec | Monthly Cost |
|---------|------|-------------|
| **Load Balancer** | 1× regional | **$12** |
| **Spaces (Standard)** | 250 GB included | **$5** |
| **Spaces (Cold)** | ~50 GB initial | **~$1** |
| **Container Registry** | Basic (500 MB) | **$5** |
| **Cloud Firewall** | — | **$0** |
| **VPC** | 1 (vapt-mvp) | **$0** |
| **Reserved IP** | 1 (scanner egress) | **$5** |

### External Services

| Service | Plan | Monthly Cost |
|---------|------|-------------|
| **Cloudflare** | Pro | **$20** |
| **Domain + DNS** | Cloudflare-managed | **$0** |

### MVP Total Estimate

| Category | Low (idle) | High (active scans) |
|----------|-----------|-------------------|
| DOKS nodes | $378 | $798 |
| Managed databases | $252 | $252 |
| Droplets | $177 | $177 |
| Networking + storage | $27 | $35 |
| External | $20 | $20 |
| **Total** | **~$854/mo** | **~$1,282/mo** |

---

## D. Instance Counts and Sizes — Production Initial Deployment

**Assumptions:** 10-20 concurrent engagements, 5-10 concurrent scans, 10-15 analysts, production SLAs.

### DOKS Cluster: `vapt-prod`

| Node Pool | Node Size | Count | Auto-scale | Monthly Cost |
|-----------|-----------|-------|------------|-------------|
| **system** | General Purpose 4 vCPU / 16 GB (`gp-4vcpu-16gb`) | 2 (fixed) | No | 2 × $126 = **$252** |
| **app** | General Purpose 4 vCPU / 16 GB (`gp-4vcpu-16gb`) | 4–8 | Yes | 4-8 × $126 = **$504–$1,008** |
| **scan-workers** | CPU-Optimized 8 vCPU / 16 GB (`c-8vcpu-16gb`) | 0–6 | Yes (scale-to-zero) | 0-6 × $168 = **$0–$1,008** |
| **ai-report** | General Purpose 8 vCPU / 32 GB (`gp-8vcpu-32gb`) | 1–3 | Yes | 1-3 × $252 = **$252–$756** |

- **Control Plane HA:** Yes (**$40/mo**)
- **Total DOKS nodes:** 7-19

### Managed Databases

| Service | Plan | HA | Monthly Cost |
|---------|------|-----|-------------|
| **PostgreSQL 16** | 4 vCPU / 8 GB / 100 GB disk | Standby + read replica | ~**$225** |
| **Valkey (Redis)** | 2 vCPU / 4 GB | HA (primary + standby) | ~**$120** |
| **Kafka** | 3-node dedicated 4 vCPU / 16 GB | Built-in (3-node) | ~**$597** |

### Standalone Droplets

| Service | Droplet Size | Block Storage | Count | Monthly Cost |
|---------|-------------|---------------|-------|-------------|
| **Temporal Server** | General Purpose 4 vCPU / 16 GB | 100 GB Volume | 1 | $126 + $10 = **$136** |
| **HashiCorp Vault** | General Purpose 2 vCPU / 8 GB | 50 GB Volume | 1 | $63 + $5 = **$68** |
| **Elasticsearch** | General Purpose 4 vCPU / 16 GB | 500 GB Volume | 2 (primary + replica) | 2 × ($126 + $50) = **$352** |

### Networking & Storage

| Service | Spec | Monthly Cost |
|---------|------|-------------|
| **Load Balancer** | 1× regional | **$12** |
| **Spaces (Standard)** | ~500 GB | **$10** |
| **Spaces (Cold)** | ~200 GB | **~$2** |
| **Container Registry** | Professional (5 GB) | **$12** |
| **Cloud Firewall** | Multiple rulesets | **$0** |
| **VPC** | 1 (vapt-prod) | **$0** |
| **Reserved IPs** | 2 (scanner egress + API) | **$10** |

### External Services

| Service | Plan | Monthly Cost |
|---------|------|-------------|
| **Cloudflare** | Pro | **$20** |

### Production Total Estimate

| Category | Low (typical) | High (peak scans) |
|----------|--------------|-------------------|
| DOKS nodes | $1,048 | $3,064 |
| Control plane HA | $40 | $40 |
| Managed databases | $942 | $942 |
| Droplets | $556 | $556 |
| Networking + storage | $46 | $55 |
| External | $20 | $20 |
| **Total** | **~$2,652/mo** | **~$4,677/mo** |

---

## E. Instance Counts and Sizes — HA Production Deployment

**Assumptions:** 30-50 concurrent engagements, 15-30 concurrent scans, 20-30 analysts, strict uptime SLAs, zero-downtime deploys.

### DOKS Cluster: `vapt-prod-ha`

| Node Pool | Node Size | Count | Auto-scale | Monthly Cost |
|-----------|-----------|-------|------------|-------------|
| **system** | General Purpose 4 vCPU / 16 GB | 3 (fixed) | No | 3 × $126 = **$378** |
| **app** | General Purpose 8 vCPU / 32 GB (`gp-8vcpu-32gb`) | 5–12 | Yes | 5-12 × $252 = **$1,260–$3,024** |
| **scan-workers** | CPU-Optimized 8 vCPU / 16 GB | 0–15 | Yes (scale-to-zero) | 0-15 × $168 = **$0–$2,520** |
| **ai-report** | General Purpose 8 vCPU / 32 GB | 2–5 | Yes | 2-5 × $252 = **$504–$1,260** |

- **Control Plane HA:** Yes (**$40/mo**)

### Managed Databases

| Service | Plan | HA | Monthly Cost |
|---------|------|-----|-------------|
| **PostgreSQL 16** | 8 vCPU / 16 GB / 250 GB disk | Standby + 2 read replicas | ~**$550** |
| **Valkey (Redis)** | 4 vCPU / 8 GB | HA (primary + 2 standby) | ~**$250** |
| **Kafka** | 6-node dedicated 4 vCPU / 16 GB | Built-in (6-node) | ~**$1,194** |

### Standalone Droplets (HA Pairs)

| Service | Droplet Size | Block Storage | Count | Monthly Cost |
|---------|-------------|---------------|-------|-------------|
| **Temporal Server** | General Purpose 4 vCPU / 16 GB | 200 GB Volume | 2 (HA) | 2 × $136 = **$272** |
| **HashiCorp Vault** | General Purpose 2 vCPU / 8 GB | 50 GB Volume | 3 (Raft HA) | 3 × $68 = **$204** |
| **Elasticsearch** | General Purpose 8 vCPU / 32 GB | 1 TB Volume | 3 (cluster) | 3 × ($252 + $100) = **$1,056** |

### HA Production Total Estimate

| Category | Typical | Peak |
|----------|---------|------|
| DOKS nodes | $2,142 | $7,182 |
| Control plane HA | $40 | $40 |
| Managed databases | $1,994 | $1,994 |
| Droplets | $1,532 | $1,532 |
| Networking + storage | $65 | $90 |
| External | $20 | $20 |
| **Total** | **~$5,793/mo** | **~$10,858/mo** |

---

## F. Networking and Firewall Design

### F.1 VPC Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VPC: vapt-prod  (10.10.0.0/16)                           │
│                    Region: nyc1 (or fra1 for EU compliance)                 │
│                                                                             │
│  ┌── Public-Facing (via DO Load Balancer) ─────────────────────────────┐   │
│  │                                                                      │   │
│  │  DO Load Balancer (public IP)                                        │   │
│  │    ├── HTTPS :443 → Kong Ingress (DOKS NodePort 30443)             │   │
│  │    └── Health check: /healthz on Kong                               │   │
│  │                                                                      │   │
│  │  Reserved IP: 1.2.3.4 (for scanner egress NAT)                     │   │
│  │    └── NAT Droplet (basic-1vcpu-1gb, iptables MASQUERADE)          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌── Private Segment (VPC-only, no public IPs) ───────────────────────┐   │
│  │                                                                      │   │
│  │  DOKS Worker Nodes (all pools)     10.10.16.0/20                    │   │
│  │  Managed PostgreSQL                10.10.x.x (DO-assigned)          │   │
│  │  Managed Valkey                    10.10.x.x (DO-assigned)          │   │
│  │  Managed Kafka                     10.10.x.x (DO-assigned)          │   │
│  │  Temporal Droplet                  10.10.32.x                       │   │
│  │  Vault Droplet                     10.10.32.x                       │   │
│  │  Elasticsearch Droplet(s)          10.10.32.x                       │   │
│  │                                                                      │   │
│  │  All inter-service traffic stays within VPC (free, unmetered)       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### F.2 Ingress Path

```
Client Browser / Teams Bot / API Consumer
         │
         ▼
    Cloudflare (WAF + CDN)
         │  HTTPS (proxied)
         ▼
    DO Load Balancer (:443)
         │  TLS termination or passthrough
         ▼
    Kong Ingress Controller (DOKS pod)
         │  JWT validation, rate limiting, tenant routing
         ├── /portal/*    → customer-portal (Next.js)
         ├── /analyst/*   → analyst-portal (Next.js)
         ├── /api/v1/*    → backend microservices
         ├── /mcp/*       → MCP orchestration server
         └── /bot/*       → Teams bot webhook endpoint
```

### F.3 Cloud Firewall Rules

#### Rule Set: `fw-doks-nodes`
Applied to: All DOKS worker nodes

| Direction | Protocol | Port | Source | Action | Purpose |
|-----------|----------|------|--------|--------|---------|
| Inbound | TCP | 30443 | DO Load Balancer | Allow | Ingress to Kong |
| Inbound | TCP | 10250 | DOKS control plane | Allow | Kubelet API |
| Inbound | TCP | All | VPC CIDR (10.10.0.0/16) | Allow | Inter-node pod traffic |
| Inbound | TCP | 22 | Bastion IP only | Allow | Emergency SSH |
| Inbound | ALL | ALL | 0.0.0.0/0 | Deny | Default deny |
| Outbound | TCP | 5432 | Managed PG private IP | Allow | Database access |
| Outbound | TCP | 6379 | Managed Valkey private IP | Allow | Cache access |
| Outbound | TCP | 9092-9094 | Managed Kafka private IPs | Allow | Event bus |
| Outbound | TCP | 443 | 0.0.0.0/0 | Allow | External APIs (Claude, scanner APIs) |
| Outbound | TCP | 80,443 | Scan target CIDRs | Allow | Scanner outbound (scan-workers only) |

#### Rule Set: `fw-data-droplets`
Applied to: Temporal, Vault, Elasticsearch Droplets

| Direction | Protocol | Port | Source | Action | Purpose |
|-----------|----------|------|--------|--------|---------|
| Inbound | TCP | 7233-7243 | DOKS VPC CIDR | Allow | Temporal gRPC |
| Inbound | TCP | 8200 | DOKS VPC CIDR | Allow | Vault API |
| Inbound | TCP | 9200 | DOKS VPC CIDR | Allow | Elasticsearch |
| Inbound | TCP | 22 | Bastion IP only | Allow | SSH |
| Inbound | ALL | ALL | 0.0.0.0/0 | Deny | Default deny |
| Outbound | TCP | 5432 | Managed PG private IP | Allow | Temporal → PG |
| Outbound | TCP | 443 | 0.0.0.0/0 | Allow | Updates, DO metadata |

### F.4 Admin Access

- **No public IPs** on DOKS worker nodes or data Droplets
- **Bastion Droplet** (basic-1vcpu-1gb, $6/mo): only resource with SSH open to the internet, locked to operator IP allowlist via Cloud Firewall
- **kubectl access**: via `doctl kubernetes cluster kubeconfig` over DO API (authenticated, no direct API server exposure needed)
- **VPN alternative**: WireGuard on bastion for persistent admin tunnel

---

## G. Storage Design

### G.1 What Goes Where

| Data Category | Storage Service | Sizing (MVP → Prod) | Retention | Encryption |
|---------------|----------------|---------------------|-----------|-----------|
| **Engagement/user/asset/finding records** | Managed PostgreSQL | 60 GB → 250 GB | Indefinite (RLS per tenant) | At rest (DO-managed) + TLS in transit |
| **Finding full-text search index** | Elasticsearch (Block Storage) | 200 GB → 1 TB | ILM: hot 30d → warm 90d → delete 1yr | Disk encryption on volume |
| **Scan raw results** (XML/JSON/SARIF) | Spaces (Standard) | 50 GB → 500 GB | 90 days, then Cold Storage | SSE (server-side) |
| **Generated reports** (PDF/DOCX) | Spaces (Standard) | 10 GB → 100 GB | Per customer contract | SSE + pre-signed URLs for download |
| **Evidence files / screenshots** | Spaces (Standard) | 20 GB → 200 GB | Engagement lifecycle + 90d | SSE |
| **Mobile APK/IPA uploads** | Spaces (Standard) | 5 GB → 50 GB | Scan lifecycle (ephemeral) | SSE |
| **Source code snapshots** (Fortify) | Spaces (Standard) | 10 GB → 100 GB | Scan lifecycle + 30d | SSE |
| **Audit logs** (7-year retention) | Spaces (Cold Storage) | 10 GB → 500 GB+ | 7 years (compliance) | SSE, immutable lifecycle policy |
| **Database backups** | Spaces (Standard) + DO auto-backup | Included | 7-day window (DO) + 30d manual | SSE |
| **Kafka events** | Managed Kafka (internal) | Included in cluster | 7-day retention on topics | DO-managed |
| **Temporal workflow state** | Block Storage (Temporal Droplet) | 50 GB → 200 GB | Active workflows + 30d archive | Disk encryption |
| **Vault secrets** | Block Storage (Vault Droplet) | 20 GB → 50 GB | Active lifecycle | Vault-managed AES-256-GCM |
| **Container images** | DO Container Registry | 500 MB → 5 GB | Latest 10 tags per service | DO-managed |

### G.2 Spaces Bucket Structure

```
vapt-platform-prod/
├── scan-results/
│   └── {tenant_id}/{engagement_id}/{scan_job_id}/
│       ├── raw/          # Scanner output (XML, JSON, SARIF)
│       └── normalized/   # Post-processing output
├── reports/
│   └── {tenant_id}/{engagement_id}/{report_id}/
│       ├── draft/        # AI-generated drafts
│       └── final/        # Approved, signed reports
├── evidence/
│   └── {tenant_id}/{engagement_id}/
│       └── {finding_id}/ # Screenshots, PoC files
├── uploads/
│   └── {tenant_id}/
│       ├── mobile/       # APK/IPA files
│       └── source/       # Code snapshots
├── backups/
│   ├── postgresql/       # pg_dump exports
│   └── elasticsearch/    # Snapshot repos
└── logs/
    └── audit/            # Immutable audit trail → moved to Cold Storage after 90d
```

---

## H. Security Controls

### H.1 Network Security

| Control | Implementation | Notes |
|---------|---------------|-------|
| **DDoS protection** | Cloudflare (L3/L4/L7) | Absorbs volumetric attacks before they hit DO |
| **WAF** | Cloudflare Pro OWASP ruleset | Blocks SQLi, XSS, path traversal at edge |
| **TLS 1.3** | Cloudflare edge + DO LB (end-to-end) | Minimum TLS 1.2; prefer 1.3 |
| **VPC isolation** | All resources in private VPC | No public IPs on compute/data |
| **Cloud Firewall** | Per-role firewall rule sets | Default-deny inbound; explicit allow per service |
| **Service mesh (optional)** | Linkerd (lighter than Istio) on DOKS | mTLS pod-to-pod; defer to production tier |

### H.2 Authentication & Authorization

| Control | Implementation |
|---------|---------------|
| **IdP** | Keycloak (self-hosted on DOKS, 2 replicas) — OIDC/SAML for both portals |
| **MFA** | Enforced via Keycloak for all MSSP users; TOTP or WebAuthn |
| **RBAC + ABAC** | 7 roles (platform_admin → customer_user) enforced at API gateway + service level |
| **API authentication** | JWT tokens (short-lived, 15-min) + refresh tokens (24h) |
| **Service-to-service** | Kubernetes service accounts + network policies; optionally mTLS via Linkerd |
| **Tenant isolation** | PostgreSQL RLS on every table; all queries filtered by tenant_id from JWT |

### H.3 Secrets Management

| Control | Implementation |
|---------|---------------|
| **Customer credentials** | HashiCorp Vault (dedicated Droplet) — KV v2 + Transit engine |
| **Application secrets** | Kubernetes Secrets (encrypted at rest via DOKS etcd encryption) or Sealed Secrets |
| **Database credentials** | Vault dynamic secrets or DO managed DB connection strings (rotated via Vault) |
| **Vault auto-unseal** | Transit auto-unseal using a second Vault instance, or use DO-managed PG as Vault backend with Shamir keys stored offline |
| **Credential leases** | Time-boxed (1h TTL) for scanner credential checkout; auto-revoke on expiry |

### H.4 Data Security

| Control | Implementation |
|---------|---------------|
| **Encryption at rest** | DO Managed DBs (automatic), Spaces (SSE), Block Storage (disk-level) |
| **Encryption in transit** | TLS everywhere — DB connections, Kafka, Redis, inter-service |
| **Tenant data isolation** | PostgreSQL RLS, Kafka tenant_id headers, Spaces path-based isolation |
| **Backup encryption** | pg_dump encrypted before upload to Spaces; Vault backup encrypted |
| **PII handling** | Credentials never logged; finding data scoped by tenant_id |

### H.5 Scanner Execution Isolation

| Control | Implementation |
|---------|---------------|
| **Dedicated node pool** | `scan-workers` pool with taint `workload=scan:NoSchedule` |
| **Resource limits** | Per-scan: 4 vCPU / 8 GB RAM / 10 GB ephemeral disk |
| **Network egress** | Kubernetes NetworkPolicy: egress only to approved scan target CIDRs |
| **No inter-pod comms** | NetworkPolicy denies all ingress between scan pods |
| **Ephemeral storage** | emptyDir volumes; destroyed when scan Job completes |
| **TTL enforcement** | K8s Job `activeDeadlineSeconds: 14400` (4 hours) |
| **Credential isolation** | Vault lease checked out per-scan, revoked on completion |

### H.6 Audit & Compliance

| Control | Implementation |
|---------|---------------|
| **Application audit log** | Every bot command, MCP tool call, finding change → PostgreSQL `audit_events` table |
| **Infrastructure audit** | DO audit log (API actions), DOKS audit log (kubectl commands) |
| **Vault audit** | All secret access logged to file backend → shipped to Spaces Cold Storage |
| **Long-term retention** | 7-year retention on Spaces Cold Storage for compliance |
| **Immutability** | Spaces lifecycle policy: no delete for cold-storage audit objects |

---

## I. Monitoring and Backup Strategy

### I.1 Observability Stack (Self-Hosted on DOKS)

The platform architecture specifies Prometheus + Grafana + Loki + Tempo. These run on the `system` node pool:

| Component | Deployment | Storage | Purpose |
|-----------|-----------|---------|---------|
| **Prometheus** | StatefulSet (1 replica MVP, 2 prod) | 50 GB Block Storage PVC | Metrics collection from all services |
| **Grafana** | Deployment (1 replica) | 1 GB PVC | Dashboards — 40+ panels per architecture spec |
| **Loki** | StatefulSet (1 replica MVP, 2 prod) | Spaces backend (S3-compat) | Log aggregation via Promtail DaemonSet |
| **Tempo** | Deployment (1 replica) | Spaces backend | Distributed tracing (OpenTelemetry) |
| **Alertmanager** | Deployment (1 replica) | — | Alert routing → PagerDuty/Slack/Email |

### I.2 DO Native Monitoring (Supplementary)

| Feature | Configuration |
|---------|--------------|
| **Droplet alerts** | CPU > 85% for 5m, Disk > 80%, Memory > 90% — on all Droplets |
| **DOKS alerts** | Node NotReady, pod CrashLoopBackOff — via Prometheus |
| **Database alerts** | DO built-in: connections > 80%, replication lag > 10s, disk > 80% |
| **Uptime checks** | External HTTPS checks: customer portal, analyst portal, API gateway, Teams bot webhook — 1-min intervals |
| **Load Balancer** | Health check failures → alert |

### I.3 Key Grafana Dashboards

| Dashboard | Key Panels |
|-----------|-----------|
| **Platform Overview** | Active engagements, concurrent scans, finding rate, API latency p99 |
| **Scan Operations** | Queue depth, active scans per scanner, scan duration distribution, failure rate |
| **Database Health** | PostgreSQL connections, query latency, replication lag, table sizes |
| **Kafka Metrics** | Consumer lag per topic, partition distribution, throughput |
| **SLA Tracking** | Finding triage SLA compliance, report delivery SLA, scan start latency |
| **AI Pipeline** | Claude API token usage, inference latency, cache hit rate |
| **Cost Monitor** | Node count over time, Spaces usage growth, bandwidth consumption |

### I.4 Backup Strategy

| Component | Backup Method | Frequency | Retention | Validation |
|-----------|--------------|-----------|-----------|-----------|
| **PostgreSQL** | DO automated backup + manual pg_dump to Spaces | Auto: daily; Manual: before deploys | DO: 7 days; Manual: 30 days | Weekly restore test to staging |
| **Elasticsearch** | Snapshot to Spaces (S3 repo) | Daily | 30 days | Monthly restore test |
| **Vault** | `vault operator raft snapshot` → Spaces | Every 6 hours | 30 days | Weekly unseal + restore test |
| **Temporal** | Backed by PostgreSQL (covered above) | Via PG backup | Via PG retention | With PG restore |
| **Spaces objects** | Cross-region replication (Spaces feature) | Continuous | Same as source | Quarterly spot-check |
| **DOKS cluster config** | GitOps (Flux/ArgoCD) — cluster state in Git | Every commit | Git history | Cluster rebuild from Git |
| **Droplet snapshots** | DO Snapshots for Vault/Temporal/ES Droplets | Weekly | 4 snapshots | Monthly boot test |

---

## J. Estimated Monthly Infrastructure Profile by Tier

### Summary Table

| Component | MVP (~$) | Production (~$) | HA Production (~$) |
|-----------|---------|-----------------|-------------------|
| **DOKS nodes (typical)** | $378–$630 | $1,048–$2,016 | $2,142–$4,500 |
| **DOKS control plane HA** | $0 | $40 | $40 |
| **Managed PostgreSQL** | $75 | $225 | $550 |
| **Managed Valkey** | $30 | $120 | $250 |
| **Managed Kafka** | $147 | $597 | $1,194 |
| **Droplets (Temporal/Vault/ES)** | $177 | $556 | $1,532 |
| **Load Balancer** | $12 | $12 | $24 (2x) |
| **Spaces (Standard)** | $5 | $10 | $20 |
| **Spaces (Cold)** | $1 | $2 | $5 |
| **Container Registry** | $5 | $12 | $12 |
| **Block Storage** | $27 | $65 | $175 |
| **Reserved IPs** | $5 | $10 | $10 |
| **Bastion Droplet** | $6 | $6 | $6 |
| **Cloudflare** | $20 | $20 | $20 |
| | | | |
| **TOTAL (typical load)** | **~$890** | **~$2,740** | **~$6,380** |
| **TOTAL (peak load)** | **~$1,300** | **~$4,750** | **~$11,000** |

### Cost Optimization Notes

- **Scale-to-zero** on scan-workers saves 30-50% on scan pool costs during off-hours
- **Reserved/committed nodes** (if DO offers): potential 20-30% discount on fixed pools
- **Spaces vs Block Storage**: use Spaces wherever possible ($0.02/GB vs $0.10/GB)
- **Kafka** is the single most expensive managed service — defer to production; use Redis Pub/Sub for MVP if needed
- **Elasticsearch** can be deferred for MVP — use PostgreSQL full-text search initially

---

## K. Risks / Bottlenecks / Scaling Notes

### K.1 DigitalOcean-Specific Limitations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **No native WAF** | Perimeter security gap | Cloudflare mandatory in front of DO LB |
| **No native secrets manager** | Must self-host Vault | Dedicated Droplet with Raft HA; consider porting to Vault HCP if budget allows |
| **No gVisor/Kata runtime on DOKS** | Cannot sandbox scan workers at kernel level like architecture specifies | Use Kubernetes NetworkPolicy + resource limits + ephemeral storage for isolation. Consider Firecracker on dedicated Droplets for high-security scan isolation. |
| **Single-region DOKS** | No multi-AZ within a DO datacenter | DOKS distributes nodes across available hypervisors but DO does not guarantee AZ-level isolation like AWS/Azure. Mitigate: multi-node pools + PDB (PodDisruptionBudgets). |
| **No managed Elasticsearch** | Must self-host | Dedicated Droplet(s) with Block Storage. Alternative: use Elastic Cloud SaaS and peer via private networking, or use PostgreSQL full-text search for MVP. |
| **No managed Temporal** | Must self-host | Dedicated Droplet. Temporal Cloud SaaS is an alternative ($200+/mo). |
| **Block Storage single-attach** | Volume can only attach to one Droplet | Use Spaces for shared storage; Block Storage only for single-Droplet stateful services |
| **Managed Kafka minimum 3 nodes** | $147/mo floor even for low throughput | Acceptable for production; for MVP, consider NATS JetStream or Redis Streams as lighter alternative |

### K.2 Scaling Bottlenecks

| Bottleneck | Trigger Point | Resolution |
|-----------|---------------|-----------|
| **PostgreSQL write throughput** | >50 concurrent engagements with heavy write patterns | Upgrade to 8-16 vCPU plan; add connection pooling (PgBouncer in DOKS); eventual sharding via Citus |
| **Elasticsearch indexing** | >100K findings ingested per hour | Add data nodes; increase Block Storage; tune bulk indexing batch size |
| **Kafka consumer lag** | Findings normalization can't keep up with scan completion rate | Scale findings-normalization-svc HPA; add Kafka partitions |
| **Scan worker node scaling** | >15 concurrent scans | DOKS node pool auto-scaler; may take 2-5min to provision new nodes |
| **AI/Report generation** | Claude API rate limits; report rendering memory pressure | Dedicated ai-report node pool with larger instances; queue-based backpressure |
| **Spaces throughput** | Large report downloads or scan result uploads | Built-in CDN for reads; multi-part upload for writes |

### K.3 What to Defer Initially (MVP Cost Savings)

| Component | Defer Until | MVP Alternative |
|-----------|-----------|-----------------|
| **Managed Kafka** | Production launch | Redis Streams or NATS JetStream ($0 additional — runs in DOKS) |
| **Elasticsearch** | >10 engagements with search needs | PostgreSQL `tsvector` full-text search + GIN indexes |
| **Dedicated AI node pool** | Report generation SLA matters | Run AI/report services on app pool (smaller instances) |
| **Vault HA (3-node)** | Production launch | Single Vault Droplet with automated snapshot backups |
| **Linkerd service mesh** | Production hardening | Kubernetes NetworkPolicy for basic pod-to-pod restrictions |
| **Tempo (tracing)** | Debug/performance needs arise | Application logging with correlation IDs |
| **Cloudflare Pro** | If you need OWASP ruleset | Cloudflare Free (basic DDoS only) |

### K.4 What Should NOT Be Compromised

| Component | Reason |
|-----------|--------|
| **Managed PostgreSQL with standby** | Data is irreplaceable. Even MVP needs automated backups + failover. |
| **VPC + Cloud Firewall** | Baseline network security. Free and non-negotiable. |
| **Separate scan-worker node pool** | Scan isolation is a security requirement for MSSP. Mixing scan and app workloads is unacceptable. |
| **Spaces for object storage** | Reports and evidence must persist outside ephemeral pods. |
| **TLS everywhere** | Cloudflare + DO LB + cert-manager gives free end-to-end TLS. |
| **HashiCorp Vault** | Customer credentials cannot live in K8s Secrets. Vault is the minimum for MSSP credential handling. |
| **Container Registry** | Don't pull from public Docker Hub in production. Private DOCR required. |

---

## L. Final Recommended Setup for Your Platform

### Phase 1: MVP / Pilot (Month 1-3)

**Goal:** Get the platform running for internal testing and 1-3 pilot customers.

```
Infrastructure:
├── 1× DOKS cluster (no HA control plane)
│   ├── system pool:       2× gp-2vcpu-8gb         ($126/mo)
│   ├── app pool:          2-4× gp-4vcpu-16gb      ($252-$504/mo)
│   └── scan-workers pool: 0-2× c-4vcpu-8gb        ($0-$168/mo)
├── Managed PostgreSQL:    2 vCPU / 4 GB + standby  ($75/mo)
├── Managed Valkey:        1 vCPU / 2 GB single     ($30/mo)
├── Redis Streams (in-DOKS) instead of Kafka         ($0)
├── 1× Temporal Droplet:   gp-2vcpu-8gb             ($68/mo)
├── 1× Vault Droplet:      basic-2vcpu-4gb          ($26/mo)
├── PostgreSQL full-text search instead of ES         ($0)
├── Spaces Standard:       250 GB                    ($5/mo)
├── 1× DO Load Balancer                              ($12/mo)
├── 1× Bastion Droplet:    basic-1vcpu-1gb           ($6/mo)
├── Container Registry:    Basic                      ($5/mo)
├── Cloudflare Free                                   ($0/mo)
│
└── Total: ~$605-$1,020/mo
```

**What you skip:** Managed Kafka, Elasticsearch, AI-dedicated nodes, service mesh, tracing.
**What you keep:** PostgreSQL HA, Vault, scan worker isolation, VPC, firewall, TLS.

### Phase 2: Production Launch (Month 4-6)

**Goal:** Support 10-20 concurrent engagements with production SLAs.

```
Upgrades from Phase 1:
├── DOKS HA control plane                             (+$40/mo)
├── app pool → 4-8× gp-4vcpu-16gb                    (+$252-$504/mo)
├── scan-workers → 0-6× c-8vcpu-16gb                 (+$168-$1,008/mo)
├── Add ai-report pool: 1-3× gp-8vcpu-32gb           (+$252-$756/mo)
├── Replace Redis Streams → Managed Kafka 3-node      (+$147-$597/mo)
├── Add Elasticsearch Droplet: gp-4vcpu-16gb          (+$136/mo)
├── PostgreSQL upgrade: 4 vCPU / 8 GB + read replica  (+$150/mo)
├── Valkey upgrade: 2 vCPU / 4 GB HA                  (+$90/mo)
├── Vault upgrade: gp-2vcpu-8gb                       (+$37/mo)
├── Cloudflare Pro                                     (+$20/mo)
├── Add Linkerd service mesh                           ($0 — open source)
│
└── Total: ~$2,700-$4,750/mo
```

### Phase 3: HA Production (Month 7+)

**Goal:** 30-50 concurrent engagements, strict uptime, compliance audits.

```
Upgrades from Phase 2:
├── Vault HA (3-node Raft)                            (+$136/mo)
├── Elasticsearch cluster (3 nodes)                   (+$700/mo)
├── Temporal HA (2 nodes)                             (+$136/mo)
├── Kafka 6-node                                      (+$597/mo)
├── PostgreSQL 8 vCPU / 16 GB + 2 read replicas      (+$325/mo)
├── Valkey 4 vCPU / 8 GB HA                           (+$130/mo)
├── 2× DO Load Balancer                               (+$12/mo)
├── Spaces Cold Storage for 7-year audit retention     (+$5/mo)
│
└── Total: ~$5,800-$11,000/mo
```

---

## Appendix: Environment Separation Strategy

### Environment Design

| Aspect | Development | Staging / UAT | Production |
|--------|------------|---------------|------------|
| **DOKS cluster** | Separate cluster (`vapt-dev`) | Separate cluster (`vapt-staging`) | Separate cluster (`vapt-prod`) |
| **VPC** | Separate VPC (`vapt-dev-vpc`) | Separate VPC (`vapt-staging-vpc`) | Separate VPC (`vapt-prod-vpc`) |
| **Managed PostgreSQL** | Separate, smallest plan (1 vCPU / 1 GB, no standby) | Separate, mirrors prod plan at smaller scale | Separate, HA with standby + read replicas |
| **Managed Valkey** | Separate, smallest single-node | Separate, mirrors prod | Separate, HA |
| **Managed Kafka** | Skip (use Redis Streams) | Separate smallest 3-node | Separate, sized for production |
| **Spaces** | Separate bucket prefix (`vapt-dev/`) | Separate bucket prefix (`vapt-staging/`) | Separate bucket prefix (`vapt-prod/`) |
| **Vault** | Single dev Droplet (dev mode OK) | Shared with dev or separate small Droplet | Dedicated HA Droplet(s) |
| **Container Registry** | Shared DOCR (tag convention: `dev-*`, `staging-*`, `prod-*`) | Shared DOCR | Shared DOCR |
| **Cloudflare** | Dev subdomain (`dev.vapt.example.com`) | Staging subdomain | Production domain |

**Why separate clusters per environment:**
- Prevents accidental production impact from dev/staging workloads
- Independent node scaling and cost control
- Separate RBAC and kubeconfig per environment
- Clean blast radius for cluster upgrades

**Cost-saving exception:** Dev and staging can share a VPC if budgets are tight, but production VPC must always be isolated.

### Dev/Staging Sizing

| Component | Dev | Staging |
|-----------|-----|---------|
| DOKS nodes | 2× basic-2vcpu-4gb ($24/mo each) | 2× gp-2vcpu-8gb ($63/mo each) |
| PostgreSQL | 1 vCPU / 1 GB ($15/mo) | 2 vCPU / 4 GB ($40/mo) |
| Valkey | 1 GB single ($15/mo) | 2 GB single ($30/mo) |
| Kafka | Skip | 3-node shared ($147/mo) |
| Droplets | Skip Vault/ES (mock) | 1× Temporal + 1× Vault (smallest) |
| **Dev total** | **~$80/mo** | |
| **Staging total** | | **~$450/mo** |

---

## Appendix: Workload Placement Matrix

| Workload | Runs On | Node Pool | Stateful? | Notes |
|----------|---------|-----------|----------|-------|
| **Customer Portal** (Next.js SSR) | DOKS | app | No | 2-3 replicas, HPA on CPU |
| **Analyst Portal** (Next.js SSR) | DOKS | app | No | 2-3 replicas, HPA on CPU |
| **Engagement Service** (Go) | DOKS | app | No | 3 replicas, HPA on requests |
| **Asset Discovery Service** (Go) | DOKS | app | No | 2 replicas |
| **Credential Vault Service** (Go) | DOKS | app | No | 2 replicas (proxy to Vault Droplet) |
| **MCP Orchestration Server** | DOKS | app | No | 2-3 replicas, SSE connections |
| **Teams Bot Service** (Node.js) | DOKS | app | No | 2 replicas, webhook endpoint |
| **Findings Normalization** (Go) | DOKS | app | No | 3 replicas, Kafka consumer, HPA on lag |
| **AI Analyst Assistant** (Python) | DOKS | ai-report | No | 2-3 replicas, memory-intensive (Claude API calls) |
| **Reporting Service** (Python) | DOKS | ai-report | No | 2 replicas, memory-intensive (PDF rendering) |
| **Analyst Workflow Service** (Go) | DOKS | app | No | 3 replicas |
| **Compliance Engine** (Go) | DOKS | app | No | 2 replicas |
| **Notification Service** (Go) | DOKS | app | No | 2 replicas |
| **Scan Orchestrator** (Go, Temporal worker) | DOKS | app | No | 3 replicas, connects to Temporal Droplet |
| **Burp Suite Connector** | DOKS | scan-workers | No | 2-8 replicas, HPA on active scans |
| **Tenable Connector** | DOKS | scan-workers | No | 2-6 replicas |
| **Fortify Connector** | DOKS | scan-workers | No | 2-8 replicas |
| **MobSF Connector** | DOKS | scan-workers | No | 1-4 replicas |
| **Keycloak** (IAM) | DOKS | system | Yes (PG-backed) | 2 replicas |
| **Kong Ingress Controller** | DOKS | system | No | 2 replicas |
| **Prometheus** | DOKS | system | Yes (PVC) | 1-2 replicas |
| **Grafana** | DOKS | system | Yes (PVC) | 1 replica |
| **Loki** | DOKS | system | Yes (Spaces backend) | 1-2 replicas |
| **Temporal Server** | Dedicated Droplet | N/A | Yes (PG + Block Storage) | Single or HA pair |
| **HashiCorp Vault** | Dedicated Droplet | N/A | Yes (Raft + Block Storage) | Single → 3-node HA |
| **Elasticsearch** | Dedicated Droplet | N/A | Yes (Block Storage) | Single → 3-node cluster |

---

## Appendix: Tool Hosting Strategy

### Burp Suite Enterprise

| Aspect | Recommendation |
|--------|---------------|
| **Hosting** | **API integration only** — do NOT self-host Burp Suite on DO |
| **Why** | Burp Suite Enterprise is licensed per-install, requires Windows/.NET for the Enterprise server, and costs $8,000-$40,000+/yr. Self-hosting on DO Droplets adds significant complexity. |
| **How it works** | The Burp Connector service (runs in DOKS scan-workers pool) calls the **Burp Suite Enterprise REST API** to create scans, monitor progress, and collect results. The Burp Enterprise server itself runs at your MSSP's existing infrastructure or PortSwigger's cloud. |
| **Scaling** | The connector scales horizontally (2-8 pods) to manage concurrent API calls. The actual scan compute is on the Burp Enterprise side. |
| **Alternative** | If you need self-hosted DAST: consider ZAP (open source) running as K8s Jobs in the scan-workers pool, using CPU-Optimized nodes. |

### Tenable.io

| Aspect | Recommendation |
|--------|---------------|
| **Hosting** | **SaaS API integration only** — Tenable.io is cloud-native |
| **How it works** | The Tenable Connector (DOKS scan-workers pool) calls the **Tenable.io REST API** to launch infrastructure scans, poll status, and fetch results. |
| **Scanner agents** | If scanning internal networks not reachable from Tenable cloud, deploy **Nessus Scanner agents** on dedicated Droplets inside the VPC or at customer sites. Not typically needed for internet-facing targets. |
| **Scaling** | Connector scales by API calls, not compute. The actual scanning is Tenable's cloud. |

### Fortify (Micro Focus / OpenText)

| Aspect | Recommendation |
|--------|---------------|
| **Hosting** | **Hybrid — Fortify SSC (API) + self-hosted ScanCentral SAST worker** |
| **Why** | Fortify SAST requires a local scan engine to analyze source code. The Fortify Software Security Center (SSC) can be SaaS or self-hosted. |
| **Recommended setup** | Use **Fortify on Demand (FoD)** SaaS API if available under your license. If self-hosting: run Fortify ScanCentral SAST worker on a **dedicated CPU-Optimized Droplet** (`c-8vcpu-16gb`, $168/mo) because SAST analysis is CPU-intensive. |
| **DOKS integration** | The Fortify Connector runs in DOKS scan-workers pool, calling the Fortify SSC/FoD API. Source code is uploaded from Spaces. |
| **Scaling** | 1-2 ScanCentral worker Droplets for MVP; scale by adding Droplets for concurrent code scans. |

### MobSF (Mobile Security Framework)

| Aspect | Recommendation |
|--------|---------------|
| **Hosting** | **Self-hosted on DOKS scan-workers pool** |
| **Why** | MobSF is open source (no licensing), runs as a Docker container, and processes APK/IPA files locally. Perfect for K8s deployment. |
| **How it works** | MobSF Connector runs as a Deployment in scan-workers pool. For each mobile scan, it pulls the APK/IPA from Spaces, runs MobSF static analysis, and streams results back to the findings pipeline. |
| **Resources** | Per instance: 2 vCPU / 4 GB RAM. 1-4 replicas based on demand. |
| **Dynamic analysis** | MobSF dynamic analysis requires an Android emulator, which needs nested virtualization — **not supported on DO**. Use static analysis only, or offload dynamic analysis to an external environment. |
| **Scaling** | HPA on the MobSF Connector deployment; CPU-Optimized nodes handle the analysis load. |

---

*Document generated for AI-Driven VAPT Orchestration Platform — DigitalOcean Infrastructure Blueprint*
*Architecture version: aligned with ARCHITECTURE.md, MICROSERVICES.md, KUBERNETES_DEPLOYMENT.md, SCAN_ORCHESTRATION_WORKFLOWS.md, SECURITY_ARCHITECTURE.md*
