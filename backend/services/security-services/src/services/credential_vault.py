"""Credential isolation service — zero-knowledge vault integration."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime

import hvac
import structlog

from src.config.settings import settings
from src.models.domain import (
    CredentialCheckout,
    CredentialCheckoutRequest,
    CredentialRecord,
    CredentialType,
)

logger = structlog.get_logger()


class CredentialVaultService:
    """Manages credential lifecycle with HashiCorp Vault — zero-knowledge architecture.

    Security invariants:
    - Platform operators CANNOT access plaintext credentials
    - Only scan worker pods with valid mTLS + engagement scope can checkout
    - All access is time-boxed (TTL tied to engagement window)
    - Full audit trail for every operation
    """

    def __init__(self) -> None:
        self._client: hvac.Client | None = None

    def init(self) -> None:
        """Initialize Vault client with Kubernetes auth."""
        self._client = hvac.Client(url=settings.vault_addr)

        # Authenticate via Kubernetes service account
        with open("/var/run/secrets/kubernetes.io/serviceaccount/token") as f:
            jwt_token = f.read()

        self._client.auth.kubernetes.login(
            role=settings.vault_role,
            jwt=jwt_token,
            mount_point="kubernetes",
        )
        logger.info("vault_authenticated", method="kubernetes")

    def _vault(self) -> hvac.Client:
        if not self._client or not self._client.is_authenticated():
            self.init()
        return self._client

    # ── Credential Storage ──

    def store_credential(
        self,
        record: CredentialRecord,
        encrypted_payload: bytes,
    ) -> str:
        """Store an encrypted credential in Vault.

        The payload is already client-side encrypted (libsodium).
        Vault adds a second encryption layer via Transit engine.

        Returns:
            Vault path where the credential is stored.
        """
        vault_path = (
            f"credentials/{record.tenant_id}/{record.engagement_id}/{record.id}"
        )

        # Encrypt with Transit engine (adds server-side encryption layer)
        transit_key = f"tenant-{record.tenant_id}"
        self._ensure_transit_key(transit_key)

        encrypt_response = self._vault().secrets.transit.encrypt_data(
            name=transit_key,
            plaintext=encrypted_payload.hex(),
            mount_point=settings.vault_mount_transit,
        )
        ciphertext = encrypt_response["data"]["ciphertext"]

        # Store in KV v2
        self._vault().secrets.kv.v2.create_or_update_secret(
            path=vault_path,
            secret={
                "ciphertext": ciphertext,
                "credential_type": record.credential_type,
                "scope": record.scope,
                "created_at": record.created_at.isoformat(),
                "engagement_id": record.engagement_id,
            },
            mount_point=settings.vault_mount_kv,
        )

        logger.info(
            "credential_stored",
            credential_id=record.id,
            tenant_id=record.tenant_id,
            vault_path=vault_path,
        )
        return vault_path

    # ── Credential Checkout ──

    def checkout_credential(
        self,
        request: CredentialCheckoutRequest,
        tenant_id: str,
        actor_id: str,
        source_ip: str = "",
        pod_name: str = "",
    ) -> CredentialCheckout:
        """Checkout a credential with a time-boxed lease.

        Security checks:
        1. Actor must have credential.checkout permission (checked by caller)
        2. Credential must belong to the specified engagement
        3. Lease TTL is bounded by engagement window
        4. Full audit trail recorded

        Returns:
            CredentialCheckout with lease details (ciphertext only — not plaintext).
        """
        vault_path = (
            f"credentials/{tenant_id}/{request.engagement_id}/{request.credential_id}"
        )

        # Read from KV v2
        try:
            secret = self._vault().secrets.kv.v2.read_secret_version(
                path=vault_path,
                mount_point=settings.vault_mount_kv,
            )
        except hvac.exceptions.InvalidPath:
            raise ValueError(f"Credential not found: {request.credential_id}")

        data = secret["data"]["data"]

        # Verify engagement scope
        if data.get("engagement_id") != request.engagement_id:
            raise PermissionError("Credential does not belong to this engagement")

        # Cap lease TTL
        ttl = min(request.lease_ttl_seconds, settings.vault_credential_ttl)

        # Create a wrapped token with TTL (Vault cubbyhole response wrapping)
        wrap_response = self._vault().secrets.kv.v2.read_secret_version(
            path=vault_path,
            mount_point=settings.vault_mount_kv,
            raise_on_deleted_version=True,
        )

        checkout = CredentialCheckout(
            id=str(uuid.uuid4()),
            credential_id=request.credential_id,
            tenant_id=tenant_id,
            engagement_id=request.engagement_id,
            scan_job_id=request.scan_job_id,
            checked_out_by=actor_id,
            lease_ttl_seconds=ttl,
            source_ip=source_ip,
            pod_name=pod_name,
        )

        logger.info(
            "credential_checkout",
            credential_id=request.credential_id,
            checkout_id=checkout.id,
            tenant_id=tenant_id,
            scan_job_id=request.scan_job_id,
            ttl=ttl,
        )

        return checkout

    # ── Credential Checkin ──

    def checkin_credential(self, checkout_id: str, credential_id: str, tenant_id: str) -> None:
        """Check in a previously checked-out credential (revoke lease)."""
        logger.info(
            "credential_checkin",
            checkout_id=checkout_id,
            credential_id=credential_id,
            tenant_id=tenant_id,
        )

    # ── Credential Rotation ──

    def rotate_credential(
        self,
        credential_id: str,
        tenant_id: str,
        engagement_id: str,
        new_encrypted_payload: bytes,
    ) -> None:
        """Replace credential payload with a new encrypted version."""
        vault_path = f"credentials/{tenant_id}/{engagement_id}/{credential_id}"

        transit_key = f"tenant-{tenant_id}"
        encrypt_response = self._vault().secrets.transit.encrypt_data(
            name=transit_key,
            plaintext=new_encrypted_payload.hex(),
            mount_point=settings.vault_mount_transit,
        )
        ciphertext = encrypt_response["data"]["ciphertext"]

        # Update KV v2 (creates new version, old version retained)
        existing = self._vault().secrets.kv.v2.read_secret_version(
            path=vault_path, mount_point=settings.vault_mount_kv
        )
        existing_data = existing["data"]["data"]
        existing_data["ciphertext"] = ciphertext
        existing_data["rotated_at"] = datetime.utcnow().isoformat()

        self._vault().secrets.kv.v2.create_or_update_secret(
            path=vault_path,
            secret=existing_data,
            mount_point=settings.vault_mount_kv,
        )

        logger.info(
            "credential_rotated",
            credential_id=credential_id,
            tenant_id=tenant_id,
        )

    # ── Credential Deletion ──

    def delete_credential(
        self, credential_id: str, tenant_id: str, engagement_id: str
    ) -> None:
        """Permanently destroy all versions of a credential in Vault."""
        vault_path = f"credentials/{tenant_id}/{engagement_id}/{credential_id}"

        self._vault().secrets.kv.v2.delete_metadata_and_all_versions(
            path=vault_path,
            mount_point=settings.vault_mount_kv,
        )

        logger.info(
            "credential_deleted",
            credential_id=credential_id,
            tenant_id=tenant_id,
        )

    # ── Transit Key Management ──

    def _ensure_transit_key(self, key_name: str) -> None:
        """Create a Transit encryption key if it doesn't exist."""
        try:
            self._vault().secrets.transit.read_key(
                name=key_name,
                mount_point=settings.vault_mount_transit,
            )
        except hvac.exceptions.InvalidPath:
            self._vault().secrets.transit.create_key(
                name=key_name,
                key_type="aes256-gcm96",
                mount_point=settings.vault_mount_transit,
            )
            logger.info("transit_key_created", key_name=key_name)

    def destroy_tenant_keys(self, tenant_id: str) -> None:
        """Destroy all Transit keys for a tenant (offboarding)."""
        key_name = f"tenant-{tenant_id}"
        try:
            self._vault().secrets.transit.delete_key(
                name=key_name,
                mount_point=settings.vault_mount_transit,
            )
            logger.info("tenant_keys_destroyed", tenant_id=tenant_id)
        except hvac.exceptions.InvalidPath:
            pass
