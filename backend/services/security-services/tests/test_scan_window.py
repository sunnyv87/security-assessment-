"""Tests for scan window enforcement."""

from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

import pytest

from src.models.domain import DayOfWeek, EmergencyOverrideRequest
from src.services.scan_window import ScanWindowEnforcer


@pytest.fixture
def enforcer():
    return ScanWindowEnforcer()


class TestScanWindowCheck:
    def test_no_window_allows_scanning(self, enforcer):
        result = enforcer.check_window("eng-no-window")
        assert result.allowed is True

    def test_within_window_allowed(self, enforcer):
        enforcer.create_window(
            tenant_id="t-1",
            engagement_id="eng-1",
            timezone="UTC",
            allowed_days=[DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY,
                          DayOfWeek.THURSDAY, DayOfWeek.FRIDAY],
            start_time=time(0, 0),
            end_time=time(23, 59),
        )
        result = enforcer.check_window("eng-1")
        # Should be allowed on any weekday with 00:00-23:59 window
        assert result.allowed is True

    def test_outside_hours_denied(self, enforcer):
        enforcer.create_window(
            tenant_id="t-1",
            engagement_id="eng-2",
            timezone="UTC",
            start_time=time(9, 0),
            end_time=time(10, 0),  # Very narrow window
        )
        # Check at 23:00 UTC — outside window
        check_time = datetime(2026, 3, 16, 23, 0, tzinfo=timezone.utc)  # Monday
        result = enforcer.check_window("eng-2", check_time=check_time)
        assert result.allowed is False
        assert "After scan window" in result.reason

    def test_blackout_date_denied(self, enforcer):
        enforcer.create_window(
            tenant_id="t-1",
            engagement_id="eng-3",
            timezone="UTC",
            start_time=time(0, 0),
            end_time=time(23, 59),
            blackout_dates=["2026-03-16"],
        )
        check_time = datetime(2026, 3, 16, 12, 0, tzinfo=timezone.utc)
        result = enforcer.check_window("eng-3", check_time=check_time)
        assert result.allowed is False
        assert "Blackout" in result.reason

    def test_weekend_denied_if_not_allowed(self, enforcer):
        enforcer.create_window(
            tenant_id="t-1",
            engagement_id="eng-4",
            timezone="UTC",
            allowed_days=[DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY,
                          DayOfWeek.THURSDAY, DayOfWeek.FRIDAY],
            start_time=time(0, 0),
            end_time=time(23, 59),
        )
        # 2026-03-15 is a Sunday
        check_time = datetime(2026, 3, 15, 12, 0, tzinfo=timezone.utc)
        result = enforcer.check_window("eng-4", check_time=check_time)
        assert result.allowed is False
        assert "Sunday" in result.reason


class TestEmergencyOverride:
    def test_override_requires_two_approvers(self, enforcer):
        with pytest.raises(PermissionError, match="requires 2 approvers"):
            enforcer.request_emergency_override(
                EmergencyOverrideRequest(
                    engagement_id="eng-1",
                    justification="Critical vulnerability in production",
                    approver_ids=["approver-1"],
                ),
                tenant_id="t-1",
                requestor_id="requestor-1",
            )

    def test_requestor_cannot_self_approve(self, enforcer):
        with pytest.raises(PermissionError, match="cannot approve their own"):
            enforcer.request_emergency_override(
                EmergencyOverrideRequest(
                    engagement_id="eng-1",
                    justification="test",
                    approver_ids=["requestor-1", "approver-2"],
                ),
                tenant_id="t-1",
                requestor_id="requestor-1",
            )

    def test_valid_override_grants_access(self, enforcer):
        enforcer.create_window(
            tenant_id="t-1",
            engagement_id="eng-override",
            timezone="UTC",
            allowed_days=[],  # No days allowed
            start_time=time(0, 0),
            end_time=time(0, 1),
        )

        # Without override — denied
        result = enforcer.check_window("eng-override")
        assert result.allowed is False

        # Grant override
        enforcer.request_emergency_override(
            EmergencyOverrideRequest(
                engagement_id="eng-override",
                justification="Incident response",
                approver_ids=["approver-1", "approver-2"],
                duration_hours=4,
            ),
            tenant_id="t-1",
            requestor_id="requestor-1",
        )

        # With override — allowed
        result = enforcer.check_window("eng-override")
        assert result.allowed is True
        assert "Emergency override" in result.reason
