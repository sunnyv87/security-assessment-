"""Immutable audit logging service with hash chain integrity."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

import structlog
from aiokafka import AIOKafkaProducer
from redis import asyncio as aioredis

from src.config.settings import settings
from src.models.domain import AuditCategory, AuditEvent

logger = structlog.get_logger()


class AuditLogger:
    """Produces immutable audit events to Kafka with SHA-256 hash chain.

    Every audit event includes a hash of the previous event, forming a
    tamper-evident chain. Any modification to historical events breaks
    the chain, which is detectable during verification.

    Events flow: Application → AuditLogger → Kafka → Elasticsearch + S3 (WORM)
    """

    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None
        self._redis: aioredis.Redis | None = None
        self._last_hash: str = "GENESIS"

    async def start(self) -> None:
        """Initialize Kafka producer and Redis for hash chain state."""
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            acks="all",  # Wait for all replicas to acknowledge
            enable_idempotence=True,  # Exactly-once semantics
        )
        await self._producer.start()

        self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)

        # Recover last hash from Redis
        last_hash = await self._redis.get("audit:last_hash")
        if last_hash:
            self._last_hash = last_hash

        logger.info("audit_logger_started")

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
        if self._redis:
            await self._redis.close()

    # ── Event Production ──

    async def log(
        self,
        category: AuditCategory,
        action: str,
        *,
        actor_id: str,
        tenant_id: str,
        actor_email: str = "",
        actor_roles: list[str] | None = None,
        resource_type: str = "",
        resource_id: str = "",
        engagement_id: str = "",
        source_ip: str = "",
        user_agent: str = "",
        result: str = "success",
        reason: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Create and publish an immutable audit event."""
        event = AuditEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            category=category,
            action=action,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_roles=actor_roles or [],
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            engagement_id=engagement_id,
            source_ip=source_ip,
            user_agent=user_agent,
            result=result,
            reason=reason,
            metadata=metadata or {},
            previous_hash=self._last_hash,
        )

        # Compute hash chain
        if settings.audit_hash_chain_enabled:
            event.event_hash = self._compute_hash(event)
            self._last_hash = event.event_hash

            # Persist last hash to Redis
            if self._redis:
                await self._redis.set("audit:last_hash", self._last_hash)

        # Publish to Kafka
        if self._producer:
            await self._producer.send(
                settings.kafka_audit_topic,
                value=event.model_dump(),
                key=tenant_id.encode("utf-8"),
            )

        logger.info(
            "audit_event",
            event_id=event.id,
            category=category,
            action=action,
            actor=actor_id,
            tenant=tenant_id,
            result=result,
        )

        return event

    # ── Convenience Methods for Common Events ──

    async def log_auth_success(self, actor_id: str, tenant_id: str, **kwargs) -> AuditEvent:
        return await self.log(
            AuditCategory.AUTH, "auth.login_success",
            actor_id=actor_id, tenant_id=tenant_id, **kwargs,
        )

    async def log_auth_failure(self, actor_id: str, tenant_id: str, reason: str, **kwargs) -> AuditEvent:
        return await self.log(
            AuditCategory.AUTH, "auth.login_failure",
            actor_id=actor_id, tenant_id=tenant_id, result="denied", reason=reason, **kwargs,
        )

    async def log_permission_denied(
        self, actor_id: str, tenant_id: str, permission: str, **kwargs
    ) -> AuditEvent:
        return await self.log(
            AuditCategory.ACCESS, "access.permission_denied",
            actor_id=actor_id, tenant_id=tenant_id,
            result="denied", reason=f"Missing permission: {permission}",
            metadata={"required_permission": permission}, **kwargs,
        )

    async def log_cross_tenant_attempt(
        self, actor_id: str, actor_tenant: str, target_tenant: str, **kwargs
    ) -> AuditEvent:
        return await self.log(
            AuditCategory.SECURITY, "security.cross_tenant_attempt",
            actor_id=actor_id, tenant_id=actor_tenant,
            result="denied", reason=f"Cross-tenant access to {target_tenant}",
            metadata={"target_tenant_id": target_tenant}, **kwargs,
        )

    async def log_credential_checkout(
        self, actor_id: str, tenant_id: str, credential_id: str, **kwargs
    ) -> AuditEvent:
        return await self.log(
            AuditCategory.CREDENTIAL, "credential.checkout",
            actor_id=actor_id, tenant_id=tenant_id,
            resource_type="credential", resource_id=credential_id, **kwargs,
        )

    async def log_credential_checkin(
        self, actor_id: str, tenant_id: str, credential_id: str, **kwargs
    ) -> AuditEvent:
        return await self.log(
            AuditCategory.CREDENTIAL, "credential.checkin",
            actor_id=actor_id, tenant_id=tenant_id,
            resource_type="credential", resource_id=credential_id, **kwargs,
        )

    async def log_scan_launched(
        self, actor_id: str, tenant_id: str, scan_id: str, engagement_id: str, **kwargs
    ) -> AuditEvent:
        return await self.log(
            AuditCategory.SCAN, "scan.launched",
            actor_id=actor_id, tenant_id=tenant_id,
            resource_type="scan", resource_id=scan_id,
            engagement_id=engagement_id, **kwargs,
        )

    async def log_scan_window_violation(
        self, actor_id: str, tenant_id: str, engagement_id: str, **kwargs
    ) -> AuditEvent:
        return await self.log(
            AuditCategory.SCAN, "scan.window_violation",
            actor_id=actor_id, tenant_id=tenant_id,
            engagement_id=engagement_id, result="denied",
            reason="Scan outside permitted window", **kwargs,
        )

    async def log_report_approved(
        self, actor_id: str, tenant_id: str, report_id: str, **kwargs
    ) -> AuditEvent:
        return await self.log(
            AuditCategory.REPORT, "report.approved",
            actor_id=actor_id, tenant_id=tenant_id,
            resource_type="report", resource_id=report_id, **kwargs,
        )

    async def log_report_delivered(
        self, actor_id: str, tenant_id: str, report_id: str, **kwargs
    ) -> AuditEvent:
        return await self.log(
            AuditCategory.REPORT, "report.delivered",
            actor_id=actor_id, tenant_id=tenant_id,
            resource_type="report", resource_id=report_id, **kwargs,
        )

    async def log_ip_denied(
        self, source_ip: str, tenant_id: str, list_type: str, **kwargs
    ) -> AuditEvent:
        return await self.log(
            AuditCategory.SECURITY, "security.ip_denied",
            actor_id="unknown", tenant_id=tenant_id,
            result="denied", reason=f"IP {source_ip} not in {list_type} allowlist",
            metadata={"blocked_ip": source_ip, "list_type": list_type},
            source_ip=source_ip, **kwargs,
        )

    async def log_emergency_override(
        self, actor_id: str, tenant_id: str, engagement_id: str,
        justification: str, approvers: list[str], **kwargs
    ) -> AuditEvent:
        return await self.log(
            AuditCategory.ADMIN, "admin.emergency_scan_override",
            actor_id=actor_id, tenant_id=tenant_id,
            engagement_id=engagement_id,
            metadata={"justification": justification, "approvers": approvers},
            **kwargs,
        )

    # ── Hash Chain ──

    @staticmethod
    def _compute_hash(event: AuditEvent) -> str:
        """Compute SHA-256 hash of event concatenated with previous hash."""
        canonical = json.dumps(
            {
                "id": event.id,
                "timestamp": event.timestamp.isoformat(),
                "category": event.category,
                "action": event.action,
                "actor_id": event.actor_id,
                "tenant_id": event.tenant_id,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "result": event.result,
                "previous_hash": event.previous_hash,
            },
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def verify_chain(events: list[AuditEvent]) -> tuple[bool, str]:
        """Verify the integrity of a sequence of audit events.

        Returns:
            (is_valid, error_message)
        """
        for i, event in enumerate(events):
            # Recompute hash
            expected_hash = AuditLogger._compute_hash(event)
            if expected_hash != event.event_hash:
                return False, f"Event {event.id} hash mismatch at index {i}"

            # Check chain continuity
            if i > 0 and event.previous_hash != events[i - 1].event_hash:
                return False, f"Chain break at event {event.id} (index {i})"

        return True, ""


# ── Audit Event Taxonomy ──
# Complete list of audit actions produced by the platform

AUDIT_EVENT_TAXONOMY = {
    AuditCategory.AUTH: [
        "auth.login_success",
        "auth.login_failure",
        "auth.logout",
        "auth.token_refresh",
        "auth.mfa_challenge",
        "auth.mfa_success",
        "auth.mfa_failure",
        "auth.api_key_created",
        "auth.api_key_revoked",
        "auth.session_expired",
    ],
    AuditCategory.ACCESS: [
        "access.permission_denied",
        "access.resource_accessed",
        "access.bulk_export",
        "access.report_downloaded",
        "access.api_rate_limited",
    ],
    AuditCategory.DATA: [
        "data.finding_created",
        "data.finding_updated",
        "data.finding_deleted",
        "data.severity_overridden",
        "data.evidence_uploaded",
        "data.evidence_deleted",
    ],
    AuditCategory.SCAN: [
        "scan.launched",
        "scan.completed",
        "scan.failed",
        "scan.cancelled",
        "scan.window_violation",
        "scan.emergency_override",
        "scan.scope_modified",
        "scan.target_added",
        "scan.target_removed",
    ],
    AuditCategory.REPORT: [
        "report.generated",
        "report.submitted_for_review",
        "report.approved",
        "report.rejected",
        "report.delivered",
        "report.downloaded",
        "report.regenerated",
    ],
    AuditCategory.CREDENTIAL: [
        "credential.created",
        "credential.checkout",
        "credential.checkin",
        "credential.rotated",
        "credential.expired",
        "credential.deleted",
        "credential.access_denied",
    ],
    AuditCategory.ADMIN: [
        "admin.user_created",
        "admin.user_deactivated",
        "admin.role_assigned",
        "admin.role_revoked",
        "admin.tenant_created",
        "admin.tenant_suspended",
        "admin.tenant_offboarded",
        "admin.ip_allowlist_updated",
        "admin.scan_window_updated",
        "admin.emergency_scan_override",
        "admin.config_changed",
    ],
    AuditCategory.SECURITY: [
        "security.cross_tenant_attempt",
        "security.ip_denied",
        "security.brute_force_detected",
        "security.anomalous_access_pattern",
        "security.credential_exposure_detected",
        "security.container_escape_attempt",
        "security.privilege_escalation_attempt",
    ],
}
