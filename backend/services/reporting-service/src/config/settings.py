"""Reporting service configuration."""

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration loaded from environment variables."""

    # ── Service ──
    service_name: str = "reporting-service"
    environment: str = "development"
    log_level: str = "INFO"
    api_port: int = 8091

    # ── Database ──
    database_url: str = "postgresql+asyncpg://vapt@localhost:5432/vapt_platform"

    # ── MinIO / S3 ──
    minio_endpoint: str = "minio.vapt-data.svc.cluster.local:9000"
    minio_access_key: str = ""  # Injected via Vault or K8s Secret
    minio_secret_key: str = ""  # Injected via Vault or K8s Secret
    minio_bucket_prefix: str = "vapt-reports"
    minio_use_ssl: bool = True
    presigned_url_ttl_seconds: int = 900  # 15 minutes

    # ── Kafka ──
    kafka_bootstrap_servers: str = "vapt-kafka-kafka-bootstrap.vapt-data.svc.cluster.local:9093"
    kafka_consumer_group: str = "reporting-service"
    kafka_topic_finding_validated: str = "finding.validated"
    kafka_topic_report_generated: str = "report.generated"
    kafka_topic_report_approved: str = "report.approved"

    # ── Internal Service URLs ──
    findings_service_url: str = "https://findings-service:8080"
    engagement_service_url: str = "https://engagement-service:8080"
    compliance_engine_url: str = "https://compliance-engine:8080"
    ai_assistant_url: str = "https://ai-analyst-assistant:8090"

    # ── Service Mesh TLS ──
    service_mesh_ca_path: str = ""  # Path to service mesh CA cert for mTLS verification

    # ── Keycloak OIDC ──
    keycloak_url: str = "https://keycloak.vapt-security.svc.cluster.local:8443"
    keycloak_realm: str = "vapt"
    jwt_algorithm: str = "RS256"
    jwt_audience: str = "vapt-platform"
    keycloak_tls_ca_path: str = ""  # Path to CA cert for Keycloak TLS verification

    # ── Report Generation ──
    template_dir: str = "src/templates"
    max_concurrent_renders: int = 4
    pdf_render_timeout_seconds: int = 120
    max_report_size_mb: int = 50

    # ── Retention ──
    report_retention_days: int = 90

    model_config = {"env_prefix": "REPORT_", "env_file": ".env"}

    @model_validator(mode="after")
    def _validate_credentials(self) -> "Settings":
        """Ensure MinIO credentials are provided in non-development environments."""
        if self.environment != "development":
            missing: list[str] = []
            if not self.minio_access_key:
                missing.append("minio_access_key")
            if not self.minio_secret_key:
                missing.append("minio_secret_key")
            if missing:
                raise ValueError(
                    f"Missing required credentials for environment "
                    f"'{self.environment}': {', '.join(missing)}"
                )
        return self


settings = Settings()
