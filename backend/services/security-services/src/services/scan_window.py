"""Scan window enforcement — timezone-aware scheduling and restriction."""

from __future__ import annotations

import uuid
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import structlog

from src.models.domain import (
    DayOfWeek,
    EmergencyOverrideRequest,
    ScanWindow,
    ScanWindowCheckResult,
)

logger = structlog.get_logger()

# Day name → Python weekday number
_DAY_TO_WEEKDAY = {
    DayOfWeek.MONDAY: 0,
    DayOfWeek.TUESDAY: 1,
    DayOfWeek.WEDNESDAY: 2,
    DayOfWeek.THURSDAY: 3,
    DayOfWeek.FRIDAY: 4,
    DayOfWeek.SATURDAY: 5,
    DayOfWeek.SUNDAY: 6,
}


class ScanWindowEnforcer:
    """Enforces scan window restrictions for engagements.

    Enforcement points:
    1. API validation — reject scan.launch if outside window
    2. Temporal workflow guard — check before dispatching to connector
    3. Scanner connector pre-check — verify just before execution
    4. Periodic watchdog — suspend running scans when window expires
    """

    # In-memory store for demo; production uses PostgreSQL
    _windows: dict[str, ScanWindow] = {}
    _overrides: dict[str, datetime] = {}  # engagement_id → override_expires_at

    def create_window(
        self,
        tenant_id: str,
        engagement_id: str,
        name: str = "Default Scan Window",
        timezone: str = "UTC",
        allowed_days: list[DayOfWeek] | None = None,
        start_time: time = time(9, 0),
        end_time: time = time(18, 0),
        blackout_dates: list[str] | None = None,
        effective_from: datetime | None = None,
        effective_until: datetime | None = None,
        created_by: str = "",
    ) -> ScanWindow:
        """Create a scan window for an engagement."""
        window = ScanWindow(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            engagement_id=engagement_id,
            name=name,
            timezone=timezone,
            allowed_days=allowed_days or [
                DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY,
                DayOfWeek.THURSDAY, DayOfWeek.FRIDAY,
            ],
            start_time=start_time,
            end_time=end_time,
            blackout_dates=blackout_dates or [],
            effective_from=effective_from,
            effective_until=effective_until,
            created_by=created_by,
        )
        self._windows[engagement_id] = window
        logger.info(
            "scan_window_created",
            engagement_id=engagement_id,
            timezone=timezone,
            days=allowed_days,
            start=str(start_time),
            end=str(end_time),
        )
        return window

    def check_window(
        self,
        engagement_id: str,
        check_time: datetime | None = None,
    ) -> ScanWindowCheckResult:
        """Check if the current time is within the scan window.

        Returns a ScanWindowCheckResult with:
        - allowed: whether scanning is permitted right now
        - reason: human-readable explanation if denied
        - next_window_start: when the next window opens (if denied)
        - current_window_end: when the current window closes (if allowed)
        """
        # Check for active emergency override
        override_expires = self._overrides.get(engagement_id)
        if override_expires and datetime.utcnow() < override_expires:
            return ScanWindowCheckResult(
                allowed=True,
                reason="Emergency override active",
                current_window_end=override_expires,
            )

        window = self._windows.get(engagement_id)
        if not window:
            # No window defined → scanning allowed (unrestricted)
            return ScanWindowCheckResult(allowed=True, reason="No scan window defined")

        if not window.is_active:
            return ScanWindowCheckResult(
                allowed=False,
                reason="Scan window is deactivated",
            )

        # Convert to engagement timezone
        tz = ZoneInfo(window.timezone)
        now = check_time or datetime.utcnow()
        local_now = now.astimezone(tz) if now.tzinfo else now.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)

        # Check effective date range
        if window.effective_from:
            effective_from = window.effective_from
            if effective_from.tzinfo is None:
                effective_from = effective_from.replace(tzinfo=tz)
            if local_now < effective_from.astimezone(tz):
                return ScanWindowCheckResult(
                    allowed=False,
                    reason=f"Scan window not yet effective (starts {window.effective_from})",
                    next_window_start=effective_from,
                )

        if window.effective_until:
            effective_until = window.effective_until
            if effective_until.tzinfo is None:
                effective_until = effective_until.replace(tzinfo=tz)
            if local_now > effective_until.astimezone(tz):
                return ScanWindowCheckResult(
                    allowed=False,
                    reason="Scan window has expired",
                )

        # Check blackout dates
        local_date_str = local_now.strftime("%Y-%m-%d")
        if local_date_str in window.blackout_dates:
            return ScanWindowCheckResult(
                allowed=False,
                reason=f"Blackout date: {local_date_str}",
                next_window_start=self._find_next_window(window, local_now, tz),
            )

        # Check day of week
        current_weekday = local_now.weekday()
        allowed_weekdays = {_DAY_TO_WEEKDAY[d] for d in window.allowed_days}
        if current_weekday not in allowed_weekdays:
            day_name = local_now.strftime("%A")
            return ScanWindowCheckResult(
                allowed=False,
                reason=f"Scanning not permitted on {day_name}",
                next_window_start=self._find_next_window(window, local_now, tz),
            )

        # Check time of day
        local_time = local_now.time()
        if local_time < window.start_time:
            return ScanWindowCheckResult(
                allowed=False,
                reason=f"Before scan window (opens at {window.start_time})",
                next_window_start=datetime.combine(
                    local_now.date(), window.start_time, tzinfo=tz
                ),
            )

        if local_time >= window.end_time:
            return ScanWindowCheckResult(
                allowed=False,
                reason=f"After scan window (closed at {window.end_time})",
                next_window_start=self._find_next_window(window, local_now, tz),
            )

        # Within window
        window_end = datetime.combine(local_now.date(), window.end_time, tzinfo=tz)
        return ScanWindowCheckResult(
            allowed=True,
            reason="Within scan window",
            current_window_end=window_end,
        )

    def request_emergency_override(
        self,
        request: EmergencyOverrideRequest,
        tenant_id: str,
        requestor_id: str,
    ) -> dict:
        """Request an emergency scan override (requires dual-approval).

        In production, this would create a pending approval workflow.
        For this implementation, we validate the approver count.
        """
        from src.config.settings import settings

        required_approvers = settings.scan_emergency_override_approvers_required
        if len(request.approver_ids) < required_approvers:
            raise PermissionError(
                f"Emergency override requires {required_approvers} approvers, "
                f"got {len(request.approver_ids)}"
            )

        # Validate approvers are not the same as requestor
        if requestor_id in request.approver_ids:
            raise PermissionError("Requestor cannot approve their own override")

        expires_at = datetime.utcnow() + timedelta(hours=request.duration_hours)
        self._overrides[request.engagement_id] = expires_at

        logger.warning(
            "emergency_scan_override_granted",
            engagement_id=request.engagement_id,
            requestor=requestor_id,
            approvers=request.approver_ids,
            expires_at=expires_at.isoformat(),
            justification=request.justification,
        )

        return {
            "engagement_id": request.engagement_id,
            "override_granted": True,
            "expires_at": expires_at.isoformat(),
            "duration_hours": request.duration_hours,
        }

    def _find_next_window(
        self,
        window: ScanWindow,
        from_time: datetime,
        tz: ZoneInfo,
    ) -> datetime | None:
        """Find the next valid scan window start time."""
        allowed_weekdays = {_DAY_TO_WEEKDAY[d] for d in window.allowed_days}
        candidate = from_time + timedelta(days=1)

        for _ in range(14):  # Search up to 2 weeks
            candidate_date = candidate.date()
            date_str = candidate_date.strftime("%Y-%m-%d")

            if (
                candidate.weekday() in allowed_weekdays
                and date_str not in window.blackout_dates
            ):
                return datetime.combine(candidate_date, window.start_time, tzinfo=tz)
            candidate += timedelta(days=1)

        return None

    def get_window(self, engagement_id: str) -> ScanWindow | None:
        return self._windows.get(engagement_id)

    def deactivate_window(self, engagement_id: str) -> None:
        window = self._windows.get(engagement_id)
        if window:
            window.is_active = False
