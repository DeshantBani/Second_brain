"""Thin wrapper around MinIO (self-hosted, S3-API-compatible object storage). Written
against the same client code you'd use for AWS S3, pointed at our own instance - no
cloud-vendor-specific service anywhere in this stack."""
import io
from functools import lru_cache

from minio import Minio
from minio.error import S3Error

from app.config import get_settings


@lru_cache
def get_minio_client() -> Minio:
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
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def put_text(storage_key: str, text: str, content_type: str = "text/markdown") -> str:
    settings = get_settings()
    client = get_minio_client()
    ensure_bucket()
    data = text.encode("utf-8")
    client.put_object(
        settings.minio_bucket,
        storage_key,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return storage_key


def get_text(storage_key: str) -> str:
    settings = get_settings()
    client = get_minio_client()
    try:
        response = client.get_object(settings.minio_bucket, storage_key)
        try:
            return response.read().decode("utf-8")
        finally:
            response.close()
            response.release_conn()
    except S3Error as exc:
        raise FileNotFoundError(f"storage key not found: {storage_key}") from exc
