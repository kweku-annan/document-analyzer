from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache



class Settings(BaseSettings):
    """Application setting loaded from environment variables"""

    # Database settings
    database_url: str

    # Storage
    upload_dir: str = "uploads"  # Local storage directory for uploaded files
    max_file_size_mb: int = 5242880

    # OpenRouter API
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str

    # App settings
    app_name: str = "Document Analyzer API"
    debug: bool = True

    # Storage (Minio)
    # Minio/S3 Configuration
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "documents"
    s3_region: str = "us-east-1"
    s3_use_ssl: bool = False
    storage_type: str = "minio"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    """Cache settings to avoid reading .env multiple times."""
    return Settings()