"""Tests for audit logging — hash chain integrity verification."""

import pytest

from src.models.domain import AuditCategory, AuditEvent
from src.services.audit_logger import AuditLogger


class TestAuditHashChain:
    def test_hash_chain_valid(self):
        events = []
        prev_hash = "GENESIS"

        for i in range(5):
            event = AuditEvent(
                id=f"event-{i}",
                category=AuditCategory.AUTH,
                action="auth.login_success",
                actor_id=f"user-{i}",
                tenant_id="t-1",
                previous_hash=prev_hash,
            )
            event.event_hash = AuditLogger._compute_hash(event)
            prev_hash = event.event_hash
            events.append(event)

        is_valid, error = AuditLogger.verify_chain(events)
        assert is_valid is True
        assert error == ""

    def test_tampered_event_detected(self):
        events = []
        prev_hash = "GENESIS"

        for i in range(5):
            event = AuditEvent(
                id=f"event-{i}",
                category=AuditCategory.AUTH,
                action="auth.login_success",
                actor_id=f"user-{i}",
                tenant_id="t-1",
                previous_hash=prev_hash,
            )
            event.event_hash = AuditLogger._compute_hash(event)
            prev_hash = event.event_hash
            events.append(event)

        # Tamper with event 2
        events[2].action = "auth.login_failure"

        is_valid, error = AuditLogger.verify_chain(events)
        assert is_valid is False
        assert "hash mismatch" in error

    def test_chain_break_detected(self):
        events = []
        prev_hash = "GENESIS"

        for i in range(5):
            event = AuditEvent(
                id=f"event-{i}",
                category=AuditCategory.AUTH,
                action="auth.login_success",
                actor_id=f"user-{i}",
                tenant_id="t-1",
                previous_hash=prev_hash,
            )
            event.event_hash = AuditLogger._compute_hash(event)
            prev_hash = event.event_hash
            events.append(event)

        # Break chain by modifying previous_hash of event 3
        events[3].previous_hash = "TAMPERED"
        events[3].event_hash = AuditLogger._compute_hash(events[3])

        is_valid, error = AuditLogger.verify_chain(events)
        assert is_valid is False
        assert "Chain break" in error

    def test_single_event_chain_valid(self):
        event = AuditEvent(
            id="event-0",
            category=AuditCategory.CREDENTIAL,
            action="credential.checkout",
            actor_id="scanner-1",
            tenant_id="t-1",
            previous_hash="GENESIS",
        )
        event.event_hash = AuditLogger._compute_hash(event)

        is_valid, error = AuditLogger.verify_chain([event])
        assert is_valid is True

    def test_empty_chain_valid(self):
        is_valid, error = AuditLogger.verify_chain([])
        assert is_valid is True
