from __future__ import annotations

import uuid
from io import BytesIO

from minio import Minio
from minio.error import S3Error

from core.config import settings


class MinioService:
    def __init__(self) -> None:
        self._client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        if not self._client.bucket_exists(settings.minio_bucket):
            self._client.make_bucket(settings.minio_bucket)

    def upload(self, data: bytes, filename: str, content_type: str = "application/octet-stream") -> str:
        object_key = f"knowledge/{uuid.uuid4()}/{filename}"
        self._client.put_object(
            settings.minio_bucket,
            object_key,
            BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return object_key

    def download(self, object_key: str) -> bytes:
        response = self._client.get_object(settings.minio_bucket, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete(self, object_key: str) -> None:
        try:
            self._client.remove_object(settings.minio_bucket, object_key)
        except S3Error:
            pass
