from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from a .env file if present


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database settings
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    # Storage
    upload_dir: str = "uploads/" # Local storage directory for uploaded files
    max_file_size: int = os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024)  # 10 MB default

    # OpenRouter API
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "your_default_api_key")
    openrouter_base_url: str = "https://openrouter.ai/api/v1/"
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "gpt-4o-mini")

    # App settings
    app_name: str = "Document Analyzer API"
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Cache settings to avoid reading .env multiple times."""
    return Settings()