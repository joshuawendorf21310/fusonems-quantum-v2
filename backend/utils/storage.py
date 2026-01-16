import os
from dataclasses import dataclass

from core.config import settings


@dataclass
class StoredObject:
    key: str
    size: int
    content_type: str


class StorageBackend:
    def save_bytes(self, key: str, data: bytes, content_type: str) -> StoredObject:
        raise NotImplementedError

    def write_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> StoredObject:
        return self.save_bytes(key, data, content_type)

    def read_bytes(self, key: str) -> bytes:
        raise NotImplementedError


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _resolve_path(self, key: str) -> str:
        return os.path.join(self.base_dir, key)

    def save_bytes(self, key: str, data: bytes, content_type: str) -> StoredObject:
        path = self._resolve_path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(data)
        return StoredObject(key=key, size=len(data), content_type=content_type)

    def write_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> StoredObject:
        return self.save_bytes(key, data, content_type)

    def read_bytes(self, key: str) -> bytes:
        path = self._resolve_path(key)
        with open(path, "rb") as handle:
            return handle.read()


class S3StorageBackend(StorageBackend):
    def __init__(self) -> None:
        import boto3

        self.bucket = settings.DOCS_S3_BUCKET
        self.client = boto3.client(
            "s3",
            region_name=settings.DOCS_S3_REGION or None,
            endpoint_url=settings.DOCS_S3_ENDPOINT or None,
            aws_access_key_id=settings.DOCS_S3_ACCESS_KEY or None,
            aws_secret_access_key=settings.DOCS_S3_SECRET_KEY or None,
        )

    def save_bytes(self, key: str, data: bytes, content_type: str) -> StoredObject:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return StoredObject(key=key, size=len(data), content_type=content_type)

    def write_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> StoredObject:
        return self.save_bytes(key, data, content_type)

    def read_bytes(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()


def get_storage_backend() -> StorageBackend:
    backend = settings.DOCS_STORAGE_BACKEND.lower()
    if backend == "s3":
        return S3StorageBackend()
    return LocalStorageBackend(settings.DOCS_STORAGE_LOCAL_DIR)


def build_storage_key(org_id: int, filename: str) -> str:
    safe_name = filename.replace("..", "").replace("/", "_")
    return f"org_{org_id}/{safe_name}"
