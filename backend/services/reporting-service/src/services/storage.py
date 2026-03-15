"""MinIO/S3 storage service for report files."""

from __future__ import annotations

import hashlib
import io
from datetime import timedelta

import structlog
from minio import Minio
from minio.error import S3Error

from src.config.settings import settings

logger = structlog.get_logger()


class StorageService:
    """Manages report file storage in MinIO/S3 with tenant isolation."""

    def __init__(self) -> None:
        self._client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_use_ssl,
        )

    def _bucket_name(self, tenant_id: str) -> str:
        """Tenant-isolated bucket name."""
        return f"{settings.minio_bucket_prefix}-{tenant_id}"

    def _ensure_bucket(self, bucket: str) -> None:
        """Create bucket if it doesn't exist."""
        try:
            if not self._client.bucket_exists(bucket):
                self._client.make_bucket(bucket)
                logger.info("bucket_created", bucket=bucket)
        except S3Error:
            logger.exception("bucket_creation_failed", bucket=bucket)

    def upload_report(
        self,
        tenant_id: str,
        report_id: str,
        file_data: bytes,
        content_type: str,
        filename: str,
    ) -> tuple[str, str, int]:
        """Upload a report file to MinIO.

        Returns:
            Tuple of (file_path, file_hash, file_size).
        """
        bucket = self._bucket_name(tenant_id)
        self._ensure_bucket(bucket)

        file_path = f"reports/{report_id}/{filename}"
        file_hash = hashlib.sha256(file_data).hexdigest()
        file_size = len(file_data)

        self._client.put_object(
            bucket,
            file_path,
            io.BytesIO(file_data),
            length=file_size,
            content_type=content_type,
        )

        logger.info(
            "report_uploaded",
            bucket=bucket,
            path=file_path,
            size=file_size,
            hash=file_hash[:16],
        )

        return file_path, file_hash, file_size

    def get_presigned_url(
        self,
        tenant_id: str,
        file_path: str,
        engagement_id: str | None = None,
    ) -> str:
        """Generate a pre-signed download URL (time-limited).

        Used for customer portal downloads. URL expires after configured TTL.

        Args:
            tenant_id: The tenant requesting the URL.
            file_path: Object path within the tenant bucket.
            engagement_id: Optional engagement ID to verify the caller has
                access to the requested file.

        Raises:
            ValueError: If file_path does not start with the expected prefix
                or the engagement_id does not match.
        """
        # Validate file_path starts with expected prefix
        expected_prefix = "reports/"
        if not file_path.startswith(expected_prefix):
            logger.warning(
                "presigned_url_invalid_path",
                tenant_id=tenant_id,
                file_path_prefix=file_path[:20],
            )
            raise ValueError(
                f"Invalid file path: must start with '{expected_prefix}'"
            )

        # If engagement_id is provided, verify the file belongs to that engagement
        if engagement_id and f"/{engagement_id}/" not in file_path:
            logger.warning(
                "presigned_url_ownership_mismatch",
                tenant_id=tenant_id,
                engagement_id=engagement_id,
            )
            raise ValueError(
                "File does not belong to the specified engagement"
            )

        bucket = self._bucket_name(tenant_id)
        ttl = timedelta(seconds=settings.presigned_url_ttl_seconds)

        url = self._client.presigned_get_object(bucket, file_path, expires=ttl)

        # Log a hash of the URL instead of the full presigned URL
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        logger.info(
            "presigned_url_generated",
            bucket=bucket,
            path=file_path,
            url_hash=url_hash,
        )
        return url

    def delete_report(self, tenant_id: str, file_path: str) -> None:
        """Delete a report file from storage."""
        bucket = self._bucket_name(tenant_id)
        try:
            self._client.remove_object(bucket, file_path)
            logger.info("report_deleted", bucket=bucket, path=file_path)
        except S3Error:
            logger.exception("report_delete_failed", bucket=bucket, path=file_path)
