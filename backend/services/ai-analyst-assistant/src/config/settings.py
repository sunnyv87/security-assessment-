"""Application configuration loaded from environment variables."""

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """AI Analyst Assistant service configuration."""

    # ── Service ──
    service_name: str = "ai-analyst-assistant"
    environment: str = "development"
    log_level: str = "INFO"
    api_port: int = 8090

    # ── Claude API ──
    anthropic_api_key: str = ""
    claude_model: str = "claude-opus-4-6"
    claude_max_tokens_summary: int = 2048
    claude_max_tokens_fp: int = 2048
    claude_max_tokens_priority: int = 4096
    claude_max_tokens_remediation: int = 4096
    claude_max_tokens_report: int = 16384
    claude_temperature: float = 0.1
    claude_timeout_seconds: int = 120
    claude_max_retries: int = 3

    # ── Database ──
    database_url: str = "postgresql+asyncpg://vapt@localhost:5432/vapt_platform"

    # ── Redis ──
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_summary: int = 14400       # 4 hours
    cache_ttl_fp_detection: int = 86400  # 24 hours
    cache_ttl_remediation: int = 43200   # 12 hours
    cache_ttl_report: int = 3600         # 1 hour
    cache_ttl_priority: int = 7200       # 2 hours

    # ── Kafka ──
    kafka_bootstrap_servers: str = "vapt-kafka-kafka-bootstrap.vapt-data.svc.cluster.local:9093"
    kafka_consumer_group: str = "ai-analyst-assistant"
    kafka_topic_findings_normalized: str = "finding.normalized"
    kafka_topic_findings_enriched: str = "finding.ai_enriched"

    # ── RAG / Embeddings ──
    embedding_model: str = "text-embedding-3-small"
    rag_similarity_top_k: int = 10
    rag_similarity_threshold: float = 0.75

    # ── Keycloak OIDC ──
    keycloak_url: str = "https://keycloak.vapt-security.svc.cluster.local:8443"
    keycloak_realm: str = "vapt"
    jwt_algorithm: str = "RS256"
    jwt_audience: str = "vapt-platform"
    keycloak_tls_ca_path: str = ""  # Path to CA cert for Keycloak TLS verification

    # ── Rate Limiting ──
    rate_limit_per_tenant_per_minute: int = 60
    rate_limit_per_analyst_per_minute: int = 30

    # ── Token Budget ──
    max_input_tokens: int = 100000
    max_evidence_chars: int = 4000
    max_tokens_per_tenant_per_day: int = 5_000_000

    model_config = {"env_prefix": "AI_ASSISTANT_", "env_file": ".env"}

    @model_validator(mode="after")
    def _validate_credentials(self) -> "Settings":
        """Ensure critical credentials are set in non-development environments."""
        if self.environment != "development":
            if not self.anthropic_api_key:
                raise ValueError(
                    "anthropic_api_key must be set in non-development environments"
                )
            if not self.redis_url:
                raise ValueError(
                    "redis_url must be set in non-development environments"
                )
        return self


settings = Settings()
