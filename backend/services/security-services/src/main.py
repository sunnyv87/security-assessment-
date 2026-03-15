"""FastAPI application entry point for Security Services."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from src.api import routes
from src.config.settings import settings
from src.middleware.csrf import CSRFMiddleware
from src.services.audit_logger import AuditLogger
from src.services.credential_vault import CredentialVaultService
from src.services.ip_allowlist import IPAllowlistService
from src.services.rbac_enforcer import RBACEnforcer
from src.services.scan_window import ScanWindowEnforcer

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initializes all security services."""
    # Initialize services
    rbac_enforcer = RBACEnforcer()
    await rbac_enforcer.init()
    routes.rbac = rbac_enforcer

    audit_logger = AuditLogger()
    await audit_logger.start()
    routes.audit = audit_logger

    credential_vault = CredentialVaultService()
    try:
        credential_vault.init()
    except Exception:
        logger.warning("vault_unavailable_running_without_credentials")
    routes.credential_vault = credential_vault

    scan_window_enforcer = ScanWindowEnforcer()
    routes.scan_windows = scan_window_enforcer

    ip_allowlist_svc = IPAllowlistService()
    await ip_allowlist_svc.init()
    routes.ip_allowlist = ip_allowlist_svc

    logger.info("security_services_started", port=settings.api_port)

    yield

    # Shutdown
    await audit_logger.stop()
    await rbac_enforcer.close()
    await ip_allowlist_svc.close()
    logger.info("security_services_stopped")


app = FastAPI(
    title="VAPT Security Services",
    description="RBAC enforcement, credential vault, audit logging, scan windows, IP allowlisting",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CSRFMiddleware)
app.include_router(routes.router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.service_name}
