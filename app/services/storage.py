import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from pathlib import Path
from datetime import datetime
from io import BytesIO
from app.config import get_settings

settings = get_settings()


class StorageService:
    """
    Unified storage service that supports both local filesystem and Minio/S3.
    Automatically uses the storage type specified in configuration.
    """
    
    def __init__(self):
        self.storage_type = settings.storage_type.lower()
        self.upload_dir = Path(settings.upload_dir)
        
        if self.storage_type == "minio":
            # Initialize Minio/S3 client
            self.s3_client = boto3.client(
                's3',
                endpoint_url=settings.s3_endpoint_url,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                config=Config(signature_version='s3v4'),
                region_name=settings.s3_region,
                use_ssl=settings.s3_use_ssl
            )
            self.bucket_name = settings.s3_bucket_name
            self._ensure_bucket_exists()
        else:
            # Create local upload directory if it doesn't exist
            self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def _ensure_bucket_exists(self):
        """
        Ensure the Minio bucket exists, create it if not.
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✓ Bucket '{self.bucket_name}' exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    print(f"✓ Created bucket '{self.bucket_name}'")
                except ClientError as create_error:
                    print(f"✗ Failed to create bucket: {create_error}")
                    raise
            else:
                print(f"✗ Error checking bucket: {e}")
                raise
    
    def save_file(self, file_content: bytes, original_filename: str) -> str:
        """
        Save uploaded file to storage (Minio or local).
        
        Args:
            file_content: The file content as bytes
            original_filename: Original name of the uploaded file
            
        Returns:
            str: Storage key/path where file is saved
        """
        # Create a unique filename to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_parts = original_filename.rsplit('.', 1)
        base_name = filename_parts[0]
        extension = filename_parts[1] if len(filename_parts) > 1 else ''
        
        unique_filename = f"{base_name}_{timestamp}.{extension}"
        
        if self.storage_type == "minio":
            # Save to Minio
            try:
                # Use a folder structure: documents/YYYY/MM/filename
                date_folder = datetime.now().strftime("%Y/%m")
                object_key = f"documents/{date_folder}/{unique_filename}"
                
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_key,
                    Body=file_content,
                    ContentType=self._get_content_type(extension)
                )
                
                return object_key
            except ClientError as e:
                raise Exception(f"Failed to save file to Minio: {str(e)}")
        else:
            # Save to local filesystem
            file_path = self.upload_dir / unique_filename
            with open(file_path, 'wb') as f:
                f.write(file_content)
            return str(file_path)
    
    def get_file(self, file_key: str) -> bytes:
        """
        Retrieve file content from storage.
        
        Args:
            file_key: Storage key/path of the file
            
        Returns:
            bytes: File content
        """
        if self.storage_type == "minio":
            try:
                response = self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=file_key
                )
                return response['Body'].read()
            except ClientError as e:
                raise Exception(f"Failed to retrieve file from Minio: {str(e)}")
        else:
            file_path = Path(file_key)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_key}")
            with open(file_path, 'rb') as f:
                return f.read()
    
    def get_file_path(self, file_key: str) -> Path:
        """
        Get a temporary local path for a file.
        For Minio files, downloads to temp location.
        
        Args:
            file_key: Storage key/path of the file
            
        Returns:
            Path: Local file path
        """
        if self.storage_type == "minio":
            # For Minio, we need to download to a temp location
            temp_dir = Path("temp_downloads")
            temp_dir.mkdir(exist_ok=True)
            
            # Extract filename from key
            filename = file_key.split('/')[-1]
            temp_path = temp_dir / filename
            
            try:
                self.s3_client.download_file(
                    self.bucket_name,
                    file_key,
                    str(temp_path)
                )
                return temp_path
            except ClientError as e:
                raise Exception(f"Failed to download file from Minio: {str(e)}")
        else:
            return Path(file_key)
    
    def file_exists(self, file_key: str) -> bool:
        """
        Check if file exists in storage.
        
        Args:
            file_key: Storage key/path of the file
            
        Returns:
            bool: True if file exists
        """
        if self.storage_type == "minio":
            try:
                self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=file_key
                )
                return True
            except ClientError:
                return False
        else:
            return Path(file_key).exists()
    
    def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_key: Storage key/path of the file
            
        Returns:
            bool: True if file was deleted
        """
        if self.storage_type == "minio":
            try:
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=file_key
                )
                return True
            except ClientError as e:
                print(f"Failed to delete file from Minio: {e}")
                return False
        else:
            file_path = Path(file_key)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
    
    def get_file_url(self, file_key: str, expiration: int = 3600) -> str:
        """
        Generate a pre-signed URL for file access (Minio only).
        
        Args:
            file_key: Storage key of the file
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            str: Pre-signed URL
        """
        if self.storage_type == "minio":
            try:
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': file_key
                    },
                    ExpiresIn=expiration
                )
                return url
            except ClientError as e:
                raise Exception(f"Failed to generate pre-signed URL: {str(e)}")
        else:
            # For local files, return file path
            return f"file://{file_key}"
    
    def _get_content_type(self, extension: str) -> str:
        """
        Get MIME content type based on file extension.
        
        Args:
            extension: File extension
            
        Returns:
            str: MIME type
        """
        content_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'doc': 'application/msword',
            'txt': 'text/plain',
        }
        return content_types.get(extension.lower(), 'application/octet-stream')
    
    def cleanup_temp_files(self):
        """
        Clean up temporary downloaded files (for Minio).
        """
        if self.storage_type == "minio":
            temp_dir = Path("temp_downloads")
            if temp_dir.exists():
                for file in temp_dir.iterdir():
                    try:
                        file.unlink()
                    except Exception as e:
                        print(f"Failed to delete temp file {file}: {e}")


# Singleton instance
storage_service = StorageService()