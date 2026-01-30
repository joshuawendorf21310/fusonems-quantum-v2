import io
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, BinaryIO, Dict, Any
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config

from core.config import settings
from utils.logger import logger
from .path_utils import build_storage_path, validate_system, validate_object_type


@dataclass
class FileMetadata:
    file_path: str
    size: int
    mime_type: str
    uploaded_at: datetime
    original_filename: str


@dataclass
class UploadContext:
    org_id: str
    system: str
    object_type: str
    object_id: str
    user_id: Optional[int] = None
    role: Optional[str] = None
    ip_address: Optional[str] = None
    device_info: Optional[str] = None
    related_object_type: Optional[str] = None
    related_object_id: Optional[str] = None


class StorageService:

    def __init__(self):
        self.bucket_name = settings.SPACES_BUCKET
        self.endpoint = settings.SPACES_ENDPOINT
        self.region = settings.SPACES_REGION

        if not all([self.bucket_name, self.endpoint, self.region]):
            logger.warning("DigitalOcean Spaces not fully configured, storage operations may fail")

        self.client = None
        if settings.SPACES_ACCESS_KEY and settings.SPACES_SECRET_KEY:
            self._init_client()

    def _init_client(self):
        try:
            self.client = boto3.client(
                's3',
                endpoint_url=self.endpoint,
                region_name=self.region,
                aws_access_key_id=settings.SPACES_ACCESS_KEY,
                aws_secret_access_key=settings.SPACES_SECRET_KEY,
                config=Config(signature_version='s3v4')
            )
            logger.info("DigitalOcean Spaces client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Spaces client: {e}")
            raise

    def _ensure_client(self):
        if not self.client:
            raise RuntimeError("Storage service not properly configured. Check SPACES_* environment variables.")

    def upload_file(
        self,
        file_data: bytes,
        filename: str,
        context: UploadContext,
        mime_type: str = "application/octet-stream",
        add_timestamp: bool = True
    ) -> FileMetadata:
        self._ensure_client()

        if not validate_system(context.system):
            raise ValueError(f"Invalid system: {context.system}")

        if not validate_object_type(context.system, context.object_type):
            raise ValueError(f"Invalid object_type '{context.object_type}' for system '{context.system}'")

        file_path = build_storage_path(
            org_id=context.org_id,
            system=context.system,
            object_type=context.object_type,
            object_id=context.object_id,
            filename=filename,
            add_timestamp=add_timestamp
        )

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=file_path,
                Body=file_data,
                ContentType=mime_type,
                ACL='private',
                Metadata={
                    'original-filename': filename,
                    'uploaded-by': str(context.user_id) if context.user_id else 'system',
                    'org-id': context.org_id,
                    'system': context.system,
                    'object-type': context.object_type,
                    'object-id': context.object_id
                }
            )

            logger.info(f"File uploaded successfully: {file_path}")

            metadata = FileMetadata(
                file_path=file_path,
                size=len(file_data),
                mime_type=mime_type,
                uploaded_at=datetime.utcnow(),
                original_filename=filename
            )

            return metadata

        except ClientError as e:
            logger.error(f"Failed to upload file to Spaces: {e}")
            raise RuntimeError(f"File upload failed: {str(e)}")

    def generate_signed_url(
        self,
        file_path: str,
        expires_in: int = 600,
        context: Optional[UploadContext] = None
    ) -> str:
        self._ensure_client()

        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_path
                },
                ExpiresIn=expires_in
            )

            logger.info(f"Generated signed URL for {file_path}, expires in {expires_in}s")
            return url

        except ClientError as e:
            logger.error(f"Failed to generate signed URL: {e}")
            raise RuntimeError(f"Signed URL generation failed: {str(e)}")

    def download_file(self, file_path: str) -> bytes:
        self._ensure_client()

        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Failed to download file from Spaces: {e}")
            raise RuntimeError(f"File download failed: {str(e)}")

    def delete_file(self, file_path: str, context: Optional[UploadContext] = None) -> bool:
        self._ensure_client()

        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            logger.info(f"File deleted from Spaces: {file_path}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file from Spaces: {e}")
            raise RuntimeError(f"File deletion failed: {str(e)}")

    def file_exists(self, file_path: str) -> bool:
        self._ensure_client()

        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise

    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        self._ensure_client()

        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return {
                'size': response['ContentLength'],
                'mime_type': response.get('ContentType'),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            logger.error(f"Failed to get file metadata: {e}")
            raise RuntimeError(f"Metadata retrieval failed: {str(e)}")

    def list_files(self, prefix: str, max_keys: int = 1000) -> list[Dict[str, Any]]:
        self._ensure_client()

        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified']
                })

            return files
        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            raise RuntimeError(f"File listing failed: {str(e)}")


_storage_service_instance: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    global _storage_service_instance
    if _storage_service_instance is None:
        _storage_service_instance = StorageService()
    return _storage_service_instance
