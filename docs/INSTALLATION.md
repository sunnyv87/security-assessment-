# Installation Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Backend Services](#backend-services)
4. [Frontend Applications](#frontend-applications)
5. [Infrastructure Dependencies](#infrastructure-dependencies)
6. [Development Tools](#development-tools)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|---|---|---|
| Python | 3.12+ | Backend services |
| Node.js | 20+ (LTS) | Frontend applications |
| Docker | 24+ | Container builds and local infra |
| kubectl | 1.28+ | Kubernetes cluster management |
| Helm | 3.14+ | Kubernetes package management |
| Git | 2.40+ | Version control |

### Optional (Production)

| Software | Version | Purpose |
|---|---|---|
| Istio CLI (`istioctl`) | 1.20+ | Service mesh management |
| Vault CLI | 1.15+ | Secrets management |
| `kyverno` CLI | 1.11+ | Policy testing |
| `stern` | 1.28+ | Multi-pod log tailing |
| AWS CLI | 2.x | Cloud infrastructure (if using AWS) |

### System Requirements

| Environment | CPU | Memory | Disk |
|---|---|---|---|
| Local development | 4 cores | 16 GB | 50 GB |
| CI/CD runner | 8 cores | 32 GB | 100 GB |
| Production cluster (min) | 48 cores | 192 GB | 1 TB SSD |

---

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd security-assessment-
```

### 2. Python Environment Setup

Create a virtual environment per service (recommended) or a shared one:

```bash
# Per-service (recommended)
cd backend/services/ai-analyst-assistant
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cd ../security-services
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .

cd ../reporting-service
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Node.js Environment Setup

```bash
cd frontend/analyst-portal
npm install
```

### 4. Local Infrastructure (Docker Compose)

For local development, spin up required infrastructure:

```bash
# PostgreSQL
docker run -d --name vapt-postgres \
  -e POSTGRES_USER=vapt \
  -e POSTGRES_PASSWORD=devpassword \
  -e POSTGRES_DB=vapt_platform \
  -p 5432:5432 \
  postgres:16-alpine

# Redis
docker run -d --name vapt-redis \
  -p 6379:6379 \
  redis:7-alpine

# Kafka (using Redpanda for local dev)
docker run -d --name vapt-kafka \
  -p 9092:9092 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  redpandadata/redpanda:latest \
  redpanda start --smp 1 --memory 1G --overprovisioned

# Elasticsearch
docker run -d --name vapt-elasticsearch \
  -e discovery.type=single-node \
  -e xpack.security.enabled=false \
  -e ES_JAVA_OPTS="-Xms512m -Xmx512m" \
  -p 9200:9200 \
  elasticsearch:8.12.0

# MinIO
docker run -d --name vapt-minio \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  -p 9000:9000 -p 9001:9001 \
  minio/minio:latest server /data --console-address ":9001"
```

### 5. Vault (Optional for Local Dev)

In development mode, Vault is optional — credential management services use mock responses. To run Vault locally:

```bash
docker run -d --name vapt-vault \
  -e VAULT_DEV_ROOT_TOKEN_ID=dev-root-token \
  -p 8200:8200 \
  hashicorp/vault:1.15 server -dev

# Enable required backends
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=dev-root-token
vault secrets enable transit
vault secrets enable -path=secret kv-v2
```

---

## Backend Services

### AI Analyst Assistant

```bash
cd backend/services/ai-analyst-assistant
source .venv/bin/activate

# Set required environment variables
export AI_ASSISTANT_ENVIRONMENT=development
export AI_ASSISTANT_ANTHROPIC_API_KEY=sk-ant-...  # Your Anthropic API key
export AI_ASSISTANT_DATABASE_URL=postgresql+asyncpg://vapt:devpassword@localhost:5432/vapt_platform
export AI_ASSISTANT_REDIS_URL=redis://localhost:6379/0
export AI_ASSISTANT_KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Run the service
uvicorn src.main:app --reload --port 8090

# Run tests
pytest tests/ -v

# Run linter
ruff check src/

# Run type checker
mypy src/
```

### Security Services

```bash
cd backend/services/security-services
source .venv/bin/activate

export SECURITY_ENVIRONMENT=development
export SECURITY_DB_HOST=localhost
export SECURITY_DB_PASSWORD=devpassword
export SECURITY_REDIS_URL=redis://localhost:6379/3
export SECURITY_KAFKA_BOOTSTRAP_SERVERS=localhost:9092

uvicorn src.main:app --reload --port 8092

# Run tests
pytest tests/ -v
```

### Reporting Service

```bash
cd backend/services/reporting-service
source .venv/bin/activate

export REPORT_ENVIRONMENT=development
export REPORT_DATABASE_URL=postgresql+asyncpg://vapt:devpassword@localhost:5432/vapt_platform
export REPORT_MINIO_ENDPOINT=localhost:9000
export REPORT_MINIO_ACCESS_KEY=minioadmin
export REPORT_MINIO_SECRET_KEY=minioadmin
export REPORT_MINIO_USE_SSL=false
export REPORT_KAFKA_BOOTSTRAP_SERVERS=localhost:9092

uvicorn src.main:app --reload --port 8091

# Run tests
pytest tests/ -v
```

---

## Frontend Applications

### Analyst Portal

```bash
cd frontend/analyst-portal

# Create .env.local
cat > .env.local << 'EOF'
API_GATEWAY_URL=http://localhost:8080
NEXT_PUBLIC_WS_URL=ws://localhost:8081
NEXT_PUBLIC_KEYCLOAK_URL=http://localhost:8180
NEXT_PUBLIC_KEYCLOAK_REALM=vapt
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=analyst-portal
EOF

# Development server
npm run dev          # Starts on http://localhost:3000

# Type checking
npm run type-check

# Linting
npm run lint

# Unit tests
npm run test

# E2E tests (requires running backend)
npm run test:e2e

# Production build
npm run build
npm run start
```

---

## Infrastructure Dependencies

### Kubernetes Operators (Production)

These operators must be installed in the cluster before deploying the platform:

```bash
# Strimzi Kafka Operator
helm repo add strimzi https://strimzi.io/charts/
helm install strimzi-kafka strimzi/strimzi-kafka-operator -n kafka-system --create-namespace

# CloudNativePG Operator
helm repo add cnpg https://cloudnative-pg.github.io/charts
helm install cnpg cnpg/cloudnative-pg -n cnpg-system --create-namespace

# Kong Ingress Controller
helm repo add kong https://charts.konghq.com
helm install kong kong/ingress -n ingress-system --create-namespace \
  -f infrastructure/k8s/ingress/kong-gateway.yaml

# Istio Service Mesh
istioctl install --set profile=default -y
kubectl label namespace vapt-platform istio-injection=enabled
kubectl label namespace vapt-data istio-injection=enabled

# Kyverno Policy Engine
helm repo add kyverno https://kyverno.github.io/kyverno/
helm install kyverno kyverno/kyverno -n kyverno --create-namespace

# Prometheus Stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

### Database Initialization

```bash
# Connect to PostgreSQL
psql -h localhost -U vapt -d vapt_platform

# Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";  -- pgvector for RAG embeddings

# Enable Row-Level Security on all tenant-scoped tables
ALTER TABLE findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE engagements ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
-- (Apply to all tenant-scoped tables)
```

---

## Development Tools

### Code Quality

```bash
# Python — Ruff (linting + formatting)
ruff check backend/services/  # Lint
ruff format backend/services/  # Format

# Python — MyPy (type checking)
mypy backend/services/ai-analyst-assistant/src/
mypy backend/services/security-services/src/

# TypeScript — ESLint + type-check
cd frontend/analyst-portal
npm run lint
npm run type-check
```

### Testing

```bash
# Backend unit tests
cd backend/services/ai-analyst-assistant && pytest tests/ -v --cov=src
cd backend/services/security-services && pytest tests/ -v --cov=src

# Frontend unit tests
cd frontend/analyst-portal && npm run test

# Frontend E2E tests
cd frontend/analyst-portal && npm run test:e2e
```

### Docker Builds

```bash
# Build individual service images
cd backend/services/ai-analyst-assistant
docker build -t vapt-registry/ai-analyst-assistant:1.0.0 .

cd backend/services/reporting-service
docker build -t vapt-registry/reporting-service:1.0.0 .

cd backend/services/security-services
docker build -t vapt-registry/security-services:1.0.0 .

cd frontend/analyst-portal
docker build -t vapt-registry/analyst-portal:1.0.0 .
```

### Health Checks

Once services are running, verify with:

```bash
# AI Analyst Assistant
curl http://localhost:8090/v1/health

# Security Services
curl http://localhost:8092/api/v1/security/health

# Reporting Service
curl http://localhost:8091/api/v1/reports/health
```
