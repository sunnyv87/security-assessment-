"""Configuration for security enforcement services."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Security services configuration loaded from environment."""

    service_name: str = "security-services"
    api_port: int = 8092

    # Keycloak OIDC
    keycloak_url: str = "https://keycloak.vapt-security.svc.cluster.local:8443"
    keycloak_realm: str = "vapt"
    keycloak_jwks_url: str = ""
    keycloak_client_id: str = "vapt-platform"
    keycloak_admin_client_id: str = "admin-cli"
    jwt_algorithm: str = "RS256"
    jwt_audience: str = "vapt-platform"

    # PostgreSQL
    db_host: str = "vapt-pgbouncer-rw.vapt-data.svc.cluster.local"
    db_port: int = 5432
    db_name: str = "vapt_platform"
    db_user: str = "vapt_security"
    db_password: str = ""
    db_ssl_mode: str = "require"

    # HashiCorp Vault
    vault_addr: str = "https://vault.vapt-data.svc.cluster.local:8200"
    vault_auth_method: str = "kubernetes"
    vault_role: str = "security-services"
    vault_mount_transit: str = "transit"
    vault_mount_kv: str = "secret"
    vault_credential_ttl: int = 3600  # 1 hour default lease

    # Redis
    redis_url: str = "redis://redis-master.vapt-data.svc.cluster.local:6379/3"
    rbac_cache_ttl: int = 300  # 5 min
    ip_allowlist_cache_ttl: int = 60  # 1 min

    # Kafka
    kafka_bootstrap_servers: str = "vapt-kafka-kafka-bootstrap.vapt-data.svc.cluster.local:9092"
    kafka_audit_topic: str = "audit.events"
    kafka_consumer_group: str = "security-services"

    # Audit
    audit_hash_chain_enabled: bool = True
    audit_retention_days: int = 2555  # 7 years

    # Scan window defaults
    scan_window_default_timezone: str = "UTC"
    scan_emergency_override_requires_approval: bool = True
    scan_emergency_override_approvers_required: int = 2

    # IP allowlist
    ip_allowlist_max_entries_per_tenant: int = 500
    scanner_egress_nat_mode: str = "shared_pool"  # shared_pool | dedicated_nat

    @property
    def jwks_url(self) -> str:
        if self.keycloak_jwks_url:
            return self.keycloak_jwks_url
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect/certs"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?ssl={self.db_ssl_mode}"
        )

    model_config = {"env_prefix": "SECURITY_"}


settings = Settings()
