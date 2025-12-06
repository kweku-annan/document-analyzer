from pydantic_settings import BaseSettings
from functools import lru_cache



class Settings(BaseSettings):
    """Application setting loaded from environment variables"""

    # Database settings
    DATABASE_URL: str

    # Storage
    upload_dir: str = "uploads/" # Local storage directory for uploaded files
    MAX_FILE_SIZE_MB: int

    # OpenRouter API
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str

    # App settings
    app_name: str = "Document Analyzer API"
    debug: bool = True

    # Storage (Minio)
    S3_ENDPOINT: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET_NAME: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Cache settings to avoid reading .env multiple times."""
    return Settings()