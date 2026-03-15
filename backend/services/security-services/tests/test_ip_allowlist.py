"""Tests for IP allowlist enforcement."""

import pytest

from src.models.domain import IPAllowlistType
from src.services.ip_allowlist import IPAllowlistService


@pytest.fixture
def service():
    return IPAllowlistService()


class TestIPAllowlist:
    def test_add_valid_ipv4_cidr(self, service):
        entry = service.add_entry(
            tenant_id="t-1",
            list_type=IPAllowlistType.PLATFORM_ACCESS,
            cidr="10.0.0.0/24",
            description="Office network",
        )
        assert entry.cidr == "10.0.0.0/24"

    def test_add_valid_ipv6_cidr(self, service):
        entry = service.add_entry(
            tenant_id="t-1",
            list_type=IPAllowlistType.PLATFORM_ACCESS,
            cidr="2001:db8::/32",
        )
        assert entry.cidr == "2001:db8::/32"

    def test_reject_invalid_cidr(self, service):
        with pytest.raises(ValueError, match="Invalid CIDR"):
            service.add_entry(
                tenant_id="t-1",
                list_type=IPAllowlistType.PLATFORM_ACCESS,
                cidr="not-an-ip",
            )

    def test_reject_duplicate_cidr(self, service):
        service.add_entry(
            tenant_id="t-1",
            list_type=IPAllowlistType.PLATFORM_ACCESS,
            cidr="10.0.0.0/24",
        )
        with pytest.raises(ValueError, match="Duplicate"):
            service.add_entry(
                tenant_id="t-1",
                list_type=IPAllowlistType.PLATFORM_ACCESS,
                cidr="10.0.0.0/24",
            )

    def test_ip_in_allowlist_allowed(self, service):
        service.add_entry(
            tenant_id="t-1",
            list_type=IPAllowlistType.PLATFORM_ACCESS,
            cidr="192.168.1.0/24",
        )
        result = service.check_platform_access("192.168.1.50", "t-1")
        assert result.allowed is True

    def test_ip_not_in_allowlist_denied(self, service):
        service.add_entry(
            tenant_id="t-1",
            list_type=IPAllowlistType.PLATFORM_ACCESS,
            cidr="192.168.1.0/24",
        )
        result = service.check_platform_access("10.0.0.1", "t-1")
        assert result.allowed is False

    def test_cross_tenant_ip_not_matched(self, service):
        service.add_entry(
            tenant_id="t-1",
            list_type=IPAllowlistType.PLATFORM_ACCESS,
            cidr="192.168.1.0/24",
        )
        # Different tenant — should not match
        result = service.check_platform_access("192.168.1.50", "t-2")
        assert result.allowed is False

    def test_scan_target_scoped_to_engagement(self, service):
        service.add_entry(
            tenant_id="t-1",
            list_type=IPAllowlistType.SCAN_TARGET,
            cidr="203.0.113.0/24",
            engagement_id="eng-1",
        )
        # Same engagement — allowed
        result = service.check_scan_target("203.0.113.10", "t-1", "eng-1")
        assert result.allowed is True

        # Different engagement — denied
        result = service.check_scan_target("203.0.113.10", "t-1", "eng-2")
        assert result.allowed is False

    def test_tenant_wide_entry_applies_to_all_engagements(self, service):
        service.add_entry(
            tenant_id="t-1",
            list_type=IPAllowlistType.SCAN_TARGET,
            cidr="198.51.100.0/24",
            engagement_id=None,  # Tenant-wide
        )
        result = service.check_scan_target("198.51.100.50", "t-1", "eng-any")
        assert result.allowed is True

    def test_validate_scan_targets_bulk(self, service):
        service.add_entry(
            tenant_id="t-1",
            list_type=IPAllowlistType.SCAN_TARGET,
            cidr="10.0.0.0/8",
            engagement_id="eng-1",
        )
        results = service.validate_scan_targets(
            ["10.0.0.1", "10.0.0.2", "192.168.1.1"],
            "t-1", "eng-1",
        )
        assert results["10.0.0.1"].allowed is True
        assert results["10.0.0.2"].allowed is True
        assert results["192.168.1.1"].allowed is False

    def test_remove_entry_stops_matching(self, service):
        entry = service.add_entry(
            tenant_id="t-1",
            list_type=IPAllowlistType.PLATFORM_ACCESS,
            cidr="172.16.0.0/16",
        )
        assert service.check_platform_access("172.16.1.1", "t-1").allowed is True

        service.remove_entry(entry.id, "t-1")
        assert service.check_platform_access("172.16.1.1", "t-1").allowed is False
