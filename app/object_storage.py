# object_storage.py
from typing import Dict, Any, BinaryIO
from minio import Minio, error
from urllib3 import BaseHTTPResponse, HTTPResponse
from app.config import Settings
from app.log_producer import LogProducer


class MinIOStorage:
    def __init__(self, settings: Settings, log_producer: LogProducer):
        """
        Initialize the MinIO storage backend with a MinIO client and bucket name.
        """
        # Construct the endpoint string from host and port
        self.endpoint = f"{settings.MINIO_HOST}:{settings.MINIO_PORT}"

        self.minio = Minio(
            endpoint=self.endpoint,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE,
            region=settings.MINIO_REGION if settings.MINIO_REGION else None
        )

        self.bucket = settings.MINIO_BUCKET
        self.log_producer = log_producer

        # Create bucket if it doesn't exist and auto-create is enabled
        if settings.MINIO_AUTO_CREATE_BUCKET:
            self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """
        Ensure the configured bucket exists, creating it if necessary.
        """
        try:
            if not self.minio.bucket_exists(self.bucket):
                self.log_producer.log_info(f"Creating bucket: {self.bucket}")
                self.minio.make_bucket(self.bucket)
                self.log_producer.log_info(f"Successfully created bucket: {self.bucket}")
        except error.MinioException as e:
            self.log_producer.log_error(f"Error ensuring bucket exists: {e}")
            raise

    def store_document(
        self, object_name: str, metadata: Dict[str, Any], content: BinaryIO, size: int,
        content_type: str = "application/octet-stream"
    ) -> None:
        """
        Upload a document to the specified bucket.
        """
        try:
            self.minio.put_object(
                bucket_name=self.bucket,
                object_name=object_name,
                data=content,
                length=size,
                metadata=metadata,
                content_type=content_type
            )
            self.log_producer.log_info(f"Successfully stored document: {object_name}")
        except error.MinioException as e:
            self.log_producer.log_error(f"MinIO error storing document {object_name}: {e}")
            raise

    def download_document(
        self, object_name: str, offset: int = 0, size: int = 0
    ) -> HTTPResponse | BaseHTTPResponse:
        """
        Download a document from the specified bucket.
        """
        try:
            response = self.minio.get_object(self.bucket, object_name, offset, size)
            self.log_producer.log_info(f"Successfully downloaded document: {object_name}")
            return response
        except error.MinioException as e:
            self.log_producer.log_error(f"MinIO error downloading document {object_name}: {e}")
            raise

    def delete_document(self, object_name: str) -> None:
        """
        Delete an object from the specified bucket.
        """
        try:
            self.minio.remove_object(self.bucket, object_name)
            self.log_producer.log_info(f"Successfully deleted document: {object_name}")
        except error.MinioException as e:
            self.log_producer.log_error(f"Error deleting object {object_name} from MinIO: {e}")
            raise

    def get_document_metadata(self, object_name: str) -> Dict[str, Any]:
        """
        Get metadata for a specific object.
        """
        try:
            stat = self.minio.stat_object(self.bucket, object_name)
            return {
                "size": stat.size,
                "etag": stat.etag,
                "last_modified": stat.last_modified,
                "metadata": stat.metadata
            }
        except error.MinioException as e:
            self.log_producer.log_error(f"Error getting metadata for {object_name}: {e}")
            raise

    def list_documents(self, prefix: str = "", recursive: bool = True) -> list:
        """
        List all documents in the bucket, optionally filtered by prefix.
        """
        try:
            objects = self.minio.list_objects(self.bucket, prefix=prefix, recursive=recursive)
            return [{"object_name": obj.object_name, "size": obj.size,
                    "last_modified": obj.last_modified} for obj in objects]
        except error.MinioException as e:
            self.log_producer.log_error(f"Error listing documents: {e}")
            raise

import boto3
from typing import Dict, Any
from botocore.exceptions import ClientError
from app.base import ObjectStorage

class S3Storage(ObjectStorage):
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        region_name: str = "us-east-1",
        bucket: str = "bucket",
    ):
        """
        Initialize the S3 storage backend with the necessary credentials and bucket name.
        """
        if not bucket:
            raise ValueError("Bucket name is required.")

        self.s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
        )
        self.bucket = bucket  # Pass in the bucket name

    def store_document(
        self, object_name: str, metadata: Dict[str, Any], data: bytes, size: int
    ) -> None:
        try:
            self.s3.put_object(Bucket=self.bucket, Key=object_name, Body=data)
        except ClientError as e:
            print(f"Error storing object {object_name} in S3: {e}")
            raise  # Re-raise if you need the caller to handle the error

    def download_document(
        self, object_name: str, offset: int = 0, size: int = 0
    ) -> None:
        range_param = None
        if size > 0:
            # Create the range header in the format "bytes=start_byte-end_byte"
            end_byte = offset + size - 1
            range_param = f"bytes={offset}-{end_byte}"

        try:
            if range_param:
                response = self.s3.get_object(
                    Bucket=self.bucket, Key=object_name, Range=range_param
                )
            else:
                response = self.s3.get_object(Bucket=self.bucket, Key=object_name)
            return response["Body"].read()
        except ClientError as e:
            print(f"Error downloading object {object_name} from S3: {e}")
            raise  # Re-raise if you need the caller to handle the error

    def delete_document(self, object_name: str) -> bool:
        """
        Delete object from the specified bucket.
        """
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=object_name)
            return True
        except ClientError as e:
            print(f"Error deleting object {object_name} from S3: {e}")
            raise  # Re-raise the error for further handling
