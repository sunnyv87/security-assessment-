"""Domain models for security enforcement services."""

from __future__ import annotations

from datetime import datetime, time
from enum import StrEnum
from ipaddress import IPv4Network, IPv6Network
from typing import Any

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
# RBAC Models
# ═══════════════════════════════════════════════════════════


class Role(StrEnum):
    PLATFORM_ADMIN = "platform_admin"
    TENANT_ADMIN = "tenant_admin"
    ENGAGEMENT_MANAGER = "engagement_manager"
    LEAD_ANALYST = "lead_analyst"
    ANALYST = "analyst"
    SCANNER_OPERATOR = "scanner_operator"
    CUSTOMER_ADMIN = "customer_admin"
    CUSTOMER_VIEWER = "customer_viewer"


class Permission(StrEnum):
    # Engagement
    ENGAGEMENT_CREATE = "engagement.create"
    ENGAGEMENT_READ = "engagement.read"
    ENGAGEMENT_UPDATE = "engagement.update"
    ENGAGEMENT_DELETE = "engagement.delete"
    ENGAGEMENT_CLOSE = "engagement.close"

    # Scan
    SCAN_LAUNCH = "scan.launch"
    SCAN_READ = "scan.read"
    SCAN_CANCEL = "scan.cancel"
    SCAN_CONFIGURE = "scan.configure"

    # Finding
    FINDING_READ = "finding.read"
    FINDING_UPDATE = "finding.update"
    FINDING_VALIDATE = "finding.validate"
    FINDING_TRIAGE = "finding.triage"
    FINDING_EXPORT = "finding.export"

    # Report
    REPORT_CREATE = "report.create"
    REPORT_READ = "report.read"
    REPORT_APPROVE = "report.approve"
    REPORT_DELIVER = "report.deliver"
    REPORT_DOWNLOAD = "report.download"

    # Credential
    CREDENTIAL_CREATE = "credential.create"
    CREDENTIAL_READ_METADATA = "credential.read_metadata"
    CREDENTIAL_CHECKOUT = "credential.checkout"
    CREDENTIAL_ROTATE = "credential.rotate"
    CREDENTIAL_DELETE = "credential.delete"

    # Admin
    ADMIN_MANAGE_USERS = "admin.manage_users"
    ADMIN_MANAGE_TENANTS = "admin.manage_tenants"
    ADMIN_VIEW_AUDIT_LOGS = "admin.view_audit_logs"
    ADMIN_MANAGE_IP_ALLOWLIST = "admin.manage_ip_allowlist"
    ADMIN_MANAGE_SCAN_WINDOWS = "admin.manage_scan_windows"
    ADMIN_EMERGENCY_OVERRIDE = "admin.emergency_override"

    # AI
    AI_ANALYZE = "ai.analyze"
    AI_DRAFT_REPORT = "ai.draft_report"

    # Compliance
    COMPLIANCE_READ = "compliance.read"
    COMPLIANCE_MANAGE = "compliance.manage"


# Complete role → permission mapping
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.PLATFORM_ADMIN: set(Permission),  # All permissions

    Role.TENANT_ADMIN: {
        Permission.ENGAGEMENT_CREATE, Permission.ENGAGEMENT_READ,
        Permission.ENGAGEMENT_UPDATE, Permission.ENGAGEMENT_CLOSE,
        Permission.SCAN_LAUNCH, Permission.SCAN_READ, Permission.SCAN_CANCEL,
        Permission.SCAN_CONFIGURE,
        Permission.FINDING_READ, Permission.FINDING_EXPORT,
        Permission.REPORT_CREATE, Permission.REPORT_READ, Permission.REPORT_APPROVE,
        Permission.REPORT_DELIVER, Permission.REPORT_DOWNLOAD,
        Permission.CREDENTIAL_CREATE, Permission.CREDENTIAL_READ_METADATA,
        Permission.CREDENTIAL_ROTATE, Permission.CREDENTIAL_DELETE,
        Permission.ADMIN_MANAGE_USERS, Permission.ADMIN_VIEW_AUDIT_LOGS,
        Permission.ADMIN_MANAGE_IP_ALLOWLIST, Permission.ADMIN_MANAGE_SCAN_WINDOWS,
        Permission.AI_ANALYZE, Permission.AI_DRAFT_REPORT,
        Permission.COMPLIANCE_READ, Permission.COMPLIANCE_MANAGE,
    },

    Role.ENGAGEMENT_MANAGER: {
        Permission.ENGAGEMENT_CREATE, Permission.ENGAGEMENT_READ,
        Permission.ENGAGEMENT_UPDATE, Permission.ENGAGEMENT_CLOSE,
        Permission.SCAN_LAUNCH, Permission.SCAN_READ, Permission.SCAN_CANCEL,
        Permission.SCAN_CONFIGURE,
        Permission.FINDING_READ, Permission.FINDING_EXPORT,
        Permission.REPORT_CREATE, Permission.REPORT_READ, Permission.REPORT_APPROVE,
        Permission.REPORT_DELIVER, Permission.REPORT_DOWNLOAD,
        Permission.CREDENTIAL_CREATE, Permission.CREDENTIAL_READ_METADATA,
        Permission.ADMIN_MANAGE_SCAN_WINDOWS,
        Permission.AI_ANALYZE, Permission.AI_DRAFT_REPORT,
        Permission.COMPLIANCE_READ,
    },

    Role.LEAD_ANALYST: {
        Permission.ENGAGEMENT_READ, Permission.ENGAGEMENT_UPDATE,
        Permission.SCAN_LAUNCH, Permission.SCAN_READ, Permission.SCAN_CANCEL,
        Permission.FINDING_READ, Permission.FINDING_UPDATE, Permission.FINDING_VALIDATE,
        Permission.FINDING_TRIAGE, Permission.FINDING_EXPORT,
        Permission.REPORT_CREATE, Permission.REPORT_READ, Permission.REPORT_APPROVE,
        Permission.REPORT_DELIVER, Permission.REPORT_DOWNLOAD,
        Permission.CREDENTIAL_READ_METADATA,
        Permission.AI_ANALYZE, Permission.AI_DRAFT_REPORT,
        Permission.COMPLIANCE_READ,
    },

    Role.ANALYST: {
        Permission.ENGAGEMENT_READ,
        Permission.SCAN_LAUNCH, Permission.SCAN_READ,
        Permission.FINDING_READ, Permission.FINDING_UPDATE, Permission.FINDING_VALIDATE,
        Permission.FINDING_TRIAGE,
        Permission.REPORT_CREATE, Permission.REPORT_READ, Permission.REPORT_DOWNLOAD,
        Permission.CREDENTIAL_READ_METADATA,
        Permission.AI_ANALYZE, Permission.AI_DRAFT_REPORT,
        Permission.COMPLIANCE_READ,
    },

    Role.SCANNER_OPERATOR: {
        Permission.ENGAGEMENT_READ,
        Permission.SCAN_LAUNCH, Permission.SCAN_READ, Permission.SCAN_CANCEL,
        Permission.SCAN_CONFIGURE,
        Permission.FINDING_READ,
        Permission.CREDENTIAL_CHECKOUT, Permission.CREDENTIAL_READ_METADATA,
    },

    Role.CUSTOMER_ADMIN: {
        Permission.ENGAGEMENT_CREATE, Permission.ENGAGEMENT_READ,
        Permission.FINDING_READ, Permission.FINDING_EXPORT,
        Permission.REPORT_READ, Permission.REPORT_DOWNLOAD,
        Permission.CREDENTIAL_CREATE, Permission.CREDENTIAL_READ_METADATA,
        Permission.CREDENTIAL_ROTATE, Permission.CREDENTIAL_DELETE,
        Permission.ADMIN_MANAGE_IP_ALLOWLIST,
        Permission.COMPLIANCE_READ,
    },

    Role.CUSTOMER_VIEWER: {
        Permission.ENGAGEMENT_READ,
        Permission.FINDING_READ,
        Permission.REPORT_READ, Permission.REPORT_DOWNLOAD,
        Permission.COMPLIANCE_READ,
    },
}


class TokenClaims(BaseModel):
    """Decoded JWT claims from Keycloak."""
    sub: str  # user ID
    iss: str
    aud: str | list[str]
    tenant_id: str
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    email: str = ""
    name: str = ""
    mfa_verified: bool = False
    engagement_ids: list[str] = Field(default_factory=list)
    iat: int = 0
    exp: int = 0


class RBACContext(BaseModel):
    """Resolved RBAC context for a request."""
    user_id: str
    tenant_id: str
    roles: list[Role]
    permissions: set[Permission]
    engagement_ids: list[str]
    mfa_verified: bool
    source_ip: str = ""


# ═══════════════════════════════════════════════════════════
# Credential Isolation Models
# ═══════════════════════════════════════════════════════════


class CredentialType(StrEnum):
    USERNAME_PASSWORD = "username_password"
    API_KEY = "api_key"
    SSH_KEY = "ssh_key"
    OAUTH_TOKEN = "oauth_token"
    CERTIFICATE = "certificate"
    AWS_ROLE = "aws_role"


class CredentialScope(StrEnum):
    SCANNER = "scanner"
    TARGET_AUTH = "target_auth"
    CLOUD_API = "cloud_api"
    CICD = "cicd"


class CredentialRecord(BaseModel):
    """Credential metadata (never contains plaintext secrets)."""
    id: str
    tenant_id: str
    engagement_id: str
    name: str
    credential_type: CredentialType
    scope: CredentialScope
    vault_path: str
    linked_asset_ids: list[str] = Field(default_factory=list)
    created_by: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_rotated_at: datetime | None = None
    expires_at: datetime | None = None
    checkout_count: int = 0
    is_active: bool = True


class CredentialCheckout(BaseModel):
    """Record of a credential checkout event."""
    id: str
    credential_id: str
    tenant_id: str
    engagement_id: str
    scan_job_id: str
    checked_out_by: str
    checked_out_at: datetime = Field(default_factory=datetime.utcnow)
    lease_ttl_seconds: int = 3600
    lease_id: str = ""
    checked_in_at: datetime | None = None
    source_ip: str = ""
    pod_name: str = ""


class CredentialCheckoutRequest(BaseModel):
    credential_id: str
    engagement_id: str
    scan_job_id: str
    lease_ttl_seconds: int = 3600


# ═══════════════════════════════════════════════════════════
# Audit Logging Models
# ═══════════════════════════════════════════════════════════


class AuditCategory(StrEnum):
    AUTH = "auth"
    ACCESS = "access"
    DATA = "data"
    SCAN = "scan"
    REPORT = "report"
    CREDENTIAL = "credential"
    ADMIN = "admin"
    SECURITY = "security"


class AuditEvent(BaseModel):
    """Immutable audit log entry."""
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    category: AuditCategory
    action: str  # e.g. "auth.login_success", "credential.checkout"
    actor_id: str
    actor_email: str = ""
    actor_roles: list[str] = Field(default_factory=list)
    tenant_id: str
    resource_type: str = ""  # e.g. "finding", "report", "credential"
    resource_id: str = ""
    engagement_id: str = ""
    source_ip: str = ""
    user_agent: str = ""
    result: str = "success"  # success, denied, error
    reason: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    previous_hash: str = ""
    event_hash: str = ""


# ═══════════════════════════════════════════════════════════
# Scan Window Models
# ═══════════════════════════════════════════════════════════


class DayOfWeek(StrEnum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class ScanWindow(BaseModel):
    """Defines when scans are permitted for an engagement."""
    id: str
    tenant_id: str
    engagement_id: str
    name: str = "Default Scan Window"
    timezone: str = "UTC"
    allowed_days: list[DayOfWeek] = Field(
        default_factory=lambda: [
            DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY,
            DayOfWeek.THURSDAY, DayOfWeek.FRIDAY,
        ]
    )
    start_time: time = Field(default=time(9, 0))  # 09:00
    end_time: time = Field(default=time(18, 0))    # 18:00
    blackout_dates: list[str] = Field(default_factory=list)  # ISO dates
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    is_active: bool = True
    created_by: str = ""


class ScanWindowCheckResult(BaseModel):
    """Result of checking if a scan is within allowed window."""
    allowed: bool
    reason: str = ""
    next_window_start: datetime | None = None
    current_window_end: datetime | None = None


class EmergencyOverrideRequest(BaseModel):
    """Request to override scan window restrictions."""
    engagement_id: str
    justification: str
    duration_hours: int = 4
    approver_ids: list[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════
# IP Allowlist Models
# ═══════════════════════════════════════════════════════════


class IPAllowlistType(StrEnum):
    PLATFORM_ACCESS = "platform_access"    # Analyst/admin access IPs
    SCAN_SOURCE = "scan_source"            # Scanner egress IPs
    SCAN_TARGET = "scan_target"            # Customer-approved target ranges


class IPAllowlistEntry(BaseModel):
    """Single IP allowlist entry."""
    id: str
    tenant_id: str
    engagement_id: str | None = None  # null = tenant-wide
    list_type: IPAllowlistType
    cidr: str  # IPv4 or IPv6 CIDR notation
    description: str = ""
    created_by: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    is_active: bool = True


class IPCheckResult(BaseModel):
    """Result of checking an IP against allowlists."""
    allowed: bool
    matched_entry_id: str | None = None
    list_type: IPAllowlistType | None = None
    reason: str = ""


# ═══════════════════════════════════════════════════════════
# API Request/Response Models
# ═══════════════════════════════════════════════════════════


class CreateScanWindowRequest(BaseModel):
    engagement_id: str
    name: str = "Default Scan Window"
    timezone: str = "UTC"
    allowed_days: list[DayOfWeek] = Field(
        default_factory=lambda: [
            DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY,
            DayOfWeek.THURSDAY, DayOfWeek.FRIDAY,
        ]
    )
    start_time: str = "09:00"
    end_time: str = "18:00"
    blackout_dates: list[str] = Field(default_factory=list)
    effective_from: str | None = None
    effective_until: str | None = None


class AddIPAllowlistRequest(BaseModel):
    engagement_id: str | None = None
    list_type: IPAllowlistType
    cidr: str
    description: str = ""
    expires_at: str | None = None


class AuditQueryRequest(BaseModel):
    tenant_id: str | None = None
    category: AuditCategory | None = None
    actor_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    limit: int = 100
    offset: int = 0
