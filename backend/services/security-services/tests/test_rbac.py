"""Tests for RBAC enforcement — permission checks, tenant isolation, MFA."""

import pytest

from src.models.domain import (
    Permission,
    RBACContext,
    Role,
    ROLE_PERMISSIONS,
)
from src.services.rbac_enforcer import RBACEnforcer


@pytest.fixture
def enforcer():
    return RBACEnforcer()


def _make_context(
    roles: list[Role],
    tenant_id: str = "tenant-1",
    engagement_ids: list[str] | None = None,
    mfa_verified: bool = True,
) -> RBACContext:
    permissions: set[Permission] = set()
    for role in roles:
        permissions.update(ROLE_PERMISSIONS.get(role, set()))
    return RBACContext(
        user_id="user-1",
        tenant_id=tenant_id,
        roles=roles,
        permissions=permissions,
        engagement_ids=engagement_ids or [],
        mfa_verified=mfa_verified,
    )


class TestRolePermissions:
    """Verify role → permission mappings."""

    def test_platform_admin_has_all_permissions(self):
        perms = ROLE_PERMISSIONS[Role.PLATFORM_ADMIN]
        assert perms == set(Permission)

    def test_customer_viewer_is_read_only(self):
        perms = ROLE_PERMISSIONS[Role.CUSTOMER_VIEWER]
        write_perms = {
            Permission.ENGAGEMENT_CREATE,
            Permission.FINDING_UPDATE,
            Permission.SCAN_LAUNCH,
            Permission.REPORT_APPROVE,
            Permission.CREDENTIAL_CREATE,
        }
        for wp in write_perms:
            assert wp not in perms

    def test_analyst_cannot_approve_reports(self):
        perms = ROLE_PERMISSIONS[Role.ANALYST]
        assert Permission.REPORT_APPROVE not in perms

    def test_lead_analyst_can_approve_reports(self):
        perms = ROLE_PERMISSIONS[Role.LEAD_ANALYST]
        assert Permission.REPORT_APPROVE in perms

    def test_scanner_operator_can_checkout_credentials(self):
        perms = ROLE_PERMISSIONS[Role.SCANNER_OPERATOR]
        assert Permission.CREDENTIAL_CHECKOUT in perms

    def test_analyst_cannot_checkout_credentials(self):
        perms = ROLE_PERMISSIONS[Role.ANALYST]
        assert Permission.CREDENTIAL_CHECKOUT not in perms

    def test_customer_admin_cannot_launch_scans(self):
        perms = ROLE_PERMISSIONS[Role.CUSTOMER_ADMIN]
        assert Permission.SCAN_LAUNCH not in perms

    def test_customer_admin_can_manage_credentials(self):
        perms = ROLE_PERMISSIONS[Role.CUSTOMER_ADMIN]
        assert Permission.CREDENTIAL_CREATE in perms
        assert Permission.CREDENTIAL_ROTATE in perms
        assert Permission.CREDENTIAL_DELETE in perms


class TestTenantIsolation:
    """Verify cross-tenant access is blocked."""

    def test_same_tenant_access_allowed(self, enforcer):
        ctx = _make_context([Role.ANALYST], tenant_id="t-1")
        assert enforcer.check_permission(
            ctx, Permission.FINDING_READ, resource_tenant_id="t-1",
        )

    def test_cross_tenant_access_denied(self, enforcer):
        ctx = _make_context([Role.ANALYST], tenant_id="t-1")
        assert not enforcer.check_permission(
            ctx, Permission.FINDING_READ, resource_tenant_id="t-2",
        )

    def test_platform_admin_can_cross_tenant(self, enforcer):
        ctx = _make_context([Role.PLATFORM_ADMIN], tenant_id="t-1")
        assert enforcer.check_permission(
            ctx, Permission.FINDING_READ, resource_tenant_id="t-2",
        )


class TestMFAEnforcement:
    """Verify MFA is required for sensitive operations."""

    def test_credential_checkout_requires_mfa(self, enforcer):
        ctx = _make_context([Role.SCANNER_OPERATOR], mfa_verified=False)
        assert not enforcer.check_sensitive_permission(
            ctx, Permission.CREDENTIAL_CHECKOUT,
        )

    def test_credential_checkout_allowed_with_mfa(self, enforcer):
        ctx = _make_context([Role.SCANNER_OPERATOR], mfa_verified=True)
        assert enforcer.check_sensitive_permission(
            ctx, Permission.CREDENTIAL_CHECKOUT,
        )

    def test_report_deliver_requires_mfa(self, enforcer):
        ctx = _make_context([Role.LEAD_ANALYST], mfa_verified=False)
        assert not enforcer.check_sensitive_permission(
            ctx, Permission.REPORT_DELIVER,
        )

    def test_finding_read_does_not_require_mfa(self, enforcer):
        ctx = _make_context([Role.ANALYST], mfa_verified=False)
        assert enforcer.check_sensitive_permission(
            ctx, Permission.FINDING_READ,
        )


class TestEngagementAssignment:
    """Verify analysts can only access assigned engagements."""

    def test_assigned_analyst_can_access(self, enforcer):
        ctx = _make_context(
            [Role.ANALYST],
            engagement_ids=["eng-1", "eng-2"],
        )
        assert enforcer.check_permission(
            ctx, Permission.FINDING_READ, resource_engagement_id="eng-1",
        )

    def test_unassigned_analyst_denied(self, enforcer):
        ctx = _make_context(
            [Role.ANALYST],
            engagement_ids=["eng-1"],
        )
        assert not enforcer.check_permission(
            ctx, Permission.FINDING_READ, resource_engagement_id="eng-3",
        )

    def test_engagement_manager_bypasses_assignment(self, enforcer):
        ctx = _make_context(
            [Role.ENGAGEMENT_MANAGER],
            engagement_ids=[],  # Not assigned but has manager role
        )
        assert enforcer.check_permission(
            ctx, Permission.FINDING_READ, resource_engagement_id="eng-3",
        )
