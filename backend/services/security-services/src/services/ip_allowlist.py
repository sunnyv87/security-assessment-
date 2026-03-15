"""IP allowlist enforcement — 3-tier allowlisting with CIDR support."""

from __future__ import annotations

import uuid
from datetime import datetime
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network, ip_address, ip_network

import structlog
from redis import asyncio as aioredis

from src.config.settings import settings
from src.models.domain import (
    IPAllowlistEntry,
    IPAllowlistType,
    IPCheckResult,
)

logger = structlog.get_logger()


class IPAllowlistService:
    """Three-tier IP allowlisting service.

    Tier 1: Platform Access — analyst/admin workstation IPs
    Tier 2: Scan Source — scanner egress NAT IPs (shown to customers)
    Tier 3: Scan Target — customer-approved target IP/CIDR ranges
    """

    def __init__(self) -> None:
        self._redis: aioredis.Redis | None = None
        # In-memory store for demo; production uses PostgreSQL + Redis cache
        self._entries: dict[str, IPAllowlistEntry] = {}

    async def init(self) -> None:
        self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()

    # ── Entry Management ──

    def add_entry(
        self,
        tenant_id: str,
        list_type: IPAllowlistType,
        cidr: str,
        *,
        engagement_id: str | None = None,
        description: str = "",
        created_by: str = "",
        expires_at: datetime | None = None,
    ) -> IPAllowlistEntry:
        """Add a CIDR range to an allowlist.

        Validates:
        - CIDR format (IPv4 or IPv6)
        - Maximum entries per tenant
        - No duplicate CIDRs
        """
        # Validate CIDR
        try:
            network = ip_network(cidr, strict=False)
        except ValueError as e:
            raise ValueError(f"Invalid CIDR notation: {cidr} — {e}")

        # Normalize CIDR
        normalized_cidr = str(network)

        # Check tenant entry limit
        tenant_entries = [
            e for e in self._entries.values()
            if e.tenant_id == tenant_id and e.is_active
        ]
        if len(tenant_entries) >= settings.ip_allowlist_max_entries_per_tenant:
            raise ValueError(
                f"Maximum entries ({settings.ip_allowlist_max_entries_per_tenant}) "
                f"reached for tenant {tenant_id}"
            )

        # Check for duplicates
        for existing in tenant_entries:
            if (
                existing.cidr == normalized_cidr
                and existing.list_type == list_type
                and existing.engagement_id == engagement_id
            ):
                raise ValueError(f"Duplicate entry: {normalized_cidr} already exists")

        entry = IPAllowlistEntry(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            engagement_id=engagement_id,
            list_type=list_type,
            cidr=normalized_cidr,
            description=description,
            created_by=created_by,
            expires_at=expires_at,
        )
        self._entries[entry.id] = entry

        logger.info(
            "ip_allowlist_entry_added",
            entry_id=entry.id,
            tenant_id=tenant_id,
            list_type=list_type,
            cidr=normalized_cidr,
        )
        return entry

    def remove_entry(self, entry_id: str, tenant_id: str) -> None:
        """Soft-delete an allowlist entry."""
        entry = self._entries.get(entry_id)
        if not entry or entry.tenant_id != tenant_id:
            raise ValueError("Entry not found")
        entry.is_active = False
        logger.info("ip_allowlist_entry_removed", entry_id=entry_id)

    # ── IP Checking ──

    def check_ip(
        self,
        ip_str: str,
        tenant_id: str,
        list_type: IPAllowlistType,
        engagement_id: str | None = None,
    ) -> IPCheckResult:
        """Check if an IP address is in the specified allowlist.

        Checks both tenant-wide and engagement-specific entries.
        Expired entries are skipped.
        """
        try:
            addr = ip_address(ip_str)
        except ValueError:
            return IPCheckResult(
                allowed=False,
                reason=f"Invalid IP address: {ip_str}",
            )

        now = datetime.utcnow()
        matching_entries = [
            e for e in self._entries.values()
            if e.tenant_id == tenant_id
            and e.list_type == list_type
            and e.is_active
            and (e.expires_at is None or e.expires_at > now)
            and (e.engagement_id is None or e.engagement_id == engagement_id)
        ]

        for entry in matching_entries:
            try:
                network = ip_network(entry.cidr, strict=False)
                if addr in network:
                    return IPCheckResult(
                        allowed=True,
                        matched_entry_id=entry.id,
                        list_type=list_type,
                        reason=f"Matched {entry.cidr} ({entry.description})",
                    )
            except ValueError:
                continue

        return IPCheckResult(
            allowed=False,
            list_type=list_type,
            reason=f"IP {ip_str} not in {list_type} allowlist for tenant {tenant_id}",
        )

    def check_platform_access(self, ip_str: str, tenant_id: str) -> IPCheckResult:
        """Check if an IP is allowed for platform access (analyst/admin)."""
        return self.check_ip(ip_str, tenant_id, IPAllowlistType.PLATFORM_ACCESS)

    def check_scan_source(self, ip_str: str, tenant_id: str) -> IPCheckResult:
        """Check if an IP is a valid scan source (scanner egress)."""
        return self.check_ip(ip_str, tenant_id, IPAllowlistType.SCAN_SOURCE)

    def check_scan_target(
        self, ip_str: str, tenant_id: str, engagement_id: str
    ) -> IPCheckResult:
        """Check if an IP is an approved scan target for an engagement."""
        return self.check_ip(
            ip_str, tenant_id, IPAllowlistType.SCAN_TARGET,
            engagement_id=engagement_id,
        )

    # ── Bulk Operations ──

    def list_entries(
        self,
        tenant_id: str,
        list_type: IPAllowlistType | None = None,
        engagement_id: str | None = None,
        active_only: bool = True,
    ) -> list[IPAllowlistEntry]:
        """List allowlist entries for a tenant."""
        results = []
        for entry in self._entries.values():
            if entry.tenant_id != tenant_id:
                continue
            if active_only and not entry.is_active:
                continue
            if list_type and entry.list_type != list_type:
                continue
            if engagement_id and entry.engagement_id != engagement_id:
                continue
            results.append(entry)
        return results

    def get_scanner_egress_ips(self, tenant_id: str) -> list[str]:
        """Get all registered scanner egress IPs for a tenant.

        These are the IPs that customers must allowlist in their firewalls.
        """
        entries = self.list_entries(
            tenant_id, list_type=IPAllowlistType.SCAN_SOURCE
        )
        return [e.cidr for e in entries]

    def validate_scan_targets(
        self,
        target_ips: list[str],
        tenant_id: str,
        engagement_id: str,
    ) -> dict[str, IPCheckResult]:
        """Validate a list of scan targets against the engagement allowlist.

        Returns a map of IP → check result.
        """
        results = {}
        for ip_str in target_ips:
            results[ip_str] = self.check_scan_target(ip_str, tenant_id, engagement_id)
        return results
