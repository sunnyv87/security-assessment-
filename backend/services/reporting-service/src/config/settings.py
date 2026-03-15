"""Reporting service configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration loaded from environment variables."""

    # ── Service ──
    service_name: str = "reporting-service"
    environment: str = "development"
    log_level: str = "INFO"
    api_port: int = 8091

    # ── Database ──
    database_url: str = "postgresql+asyncpg://vapt:vapt@localhost:5432/vapt_platform"

    # ── MinIO / S3 ──
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_prefix: str = "vapt-reports"
    minio_use_ssl: bool = False
    presigned_url_ttl_seconds: int = 900  # 15 minutes

    # ── Kafka ──
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_consumer_group: str = "reporting-service"
    kafka_topic_finding_validated: str = "finding.validated"
    kafka_topic_report_generated: str = "report.generated"
    kafka_topic_report_approved: str = "report.approved"

    # ── Internal Service URLs ──
    findings_service_url: str = "http://findings-service:8080"
    engagement_service_url: str = "http://engagement-service:8080"
    compliance_engine_url: str = "http://compliance-engine:8080"
    ai_assistant_url: str = "http://ai-analyst-assistant:8090"

    # ── Report Generation ──
    template_dir: str = "src/templates"
    max_concurrent_renders: int = 4
    pdf_render_timeout_seconds: int = 120
    max_report_size_mb: int = 50

    # ── Retention ──
    report_retention_days: int = 90

    model_config = {"env_prefix": "REPORT_", "env_file": ".env"}


settings = Settings()
