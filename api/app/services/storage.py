"""Thin wrapper around MinIO (self-hosted, S3-API-compatible object storage). Written
against the same client code you'd use for AWS S3, pointed at our own instance - no
cloud-vendor-specific service anywhere in this stack.

Load-bearing note: the app never actually reads a document's content back from here -
every read path serves `Document.extracted_text`/`page_map` from Postgres (see
ingestion.py, routers/matters.py). This module only ever writes a redundant copy,
purely to satisfy the original architecture's "object storage" line item. That means
it's safe to degrade gracefully rather than fail the request: a hosted deployment
that doesn't have MinIO/S3-compatible storage configured (or reachable) still fully
works for every actual feature - ingestion just skips the extra copy and logs why.
"""
import io
import logging
from functools import lru_cache

from minio import Minio
from minio.error import S3Error

from app.config import get_settings

logger = logging.getLogger("second_brain.storage")


def _storage_configured() -> bool:
    settings = get_settings()
    return bool(settings.minio_endpoint and settings.minio_access_key and settings.minio_secret_key)


@lru_cache
def get_minio_client() -> Minio | None:
    if not _storage_configured():
        return None
    settings = get_settings()
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_use_ssl,
    )


def ensure_bucket() -> None:
    settings = get_settings()
    client = get_minio_client()
    if client is None:
        return
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def put_text(storage_key: str, text: str, content_type: str = "text/markdown") -> str:
    """Best-effort: logs and continues on any failure (not configured, unreachable,
    bucket issue) rather than failing ingestion over a non-load-bearing side write."""
    client = get_minio_client()
    if client is None:
        logger.info("object storage not configured - skipping redundant copy for %s", storage_key)
        return storage_key
    try:
        settings = get_settings()
        ensure_bucket()
        data = text.encode("utf-8")
        client.put_object(
            settings.minio_bucket,
            storage_key,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
    except Exception as exc:  # noqa: BLE001 - never let the optional copy break ingestion
        logger.warning("object storage write failed for %s, continuing without it: %s", storage_key, exc)
    return storage_key


def get_text(storage_key: str) -> str:
    """Not called anywhere in the app today (see module docstring) - kept for
    completeness/future use. Still raises clearly if ever used against unconfigured
    storage, since a caller that DOES ask for this back presumably needs the real
    thing rather than a silent empty string."""
    settings = get_settings()
    client = get_minio_client()
    if client is None:
        raise FileNotFoundError("object storage is not configured")
    try:
        response = client.get_object(settings.minio_bucket, storage_key)
        try:
            return response.read().decode("utf-8")
        finally:
            response.close()
            response.release_conn()
    except S3Error as exc:
        raise FileNotFoundError(f"storage key not found: {storage_key}") from exc
