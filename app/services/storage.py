"""Handles saving files to the local filesystem."""
import os
import shutil
from pathlib import Path
from datetime import datetime
from app.config import get_settings

settings = get_settings()


class StorageService:
    """
    Service for handling file storage operations.
    Currently uses local filesystem, but can be easily switched to S3/Minio.
    """

    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        # Create upload directory if it doesn't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_content: bytes, original_filename: str) -> str:
        """
        Save uploaded file to local storage.

        Args:
            file_content: The file content as bytes.
            original_filename: The original filename.
        :param file_content:
        :param original_filename:
        :return:
        """
        # Create a unique filename to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_parts = original_filename.rsplit(".", 1)
        base_name = filename_parts[0]
        extension = filename_parts[1] if len(filename_parts) > 1 else ""

        unique_filename = f"{base_name}_{timestamp}.{extension}"
        file_path = self.upload_dir / unique_filename

        # Write file to disk
        with open(file_path, "wb") as f:
            f.write(file_content)

        return str(file_path)

    def get_file_path(self, relative_path: str) -> Path:
        """
        Get full path to a stored file.
        Args:
            relative_path: The relative path of the file in storage.
        :param relative_path:
        :return:
        """
        return Path(relative_path)

    def file_exists(self, relative_path: str) -> bool:
        """
        Check if a file exists in storage.
        Args:
            relative_path: The relative path of the file in storage.
        :param relative_path:
        """

        return self.get_file_path(relative_path).exists()

    def delete_file(self, relative_path: str) -> bool:
        """
        Delete a file from storage.
        :param relative_path:
        :return:
        """
        file_path = self.get_file_path(relative_path)
        if file_path.exists():
            file_path.unlink()
            return True
        return False


# Singleton instance
storage_service = StorageService()
