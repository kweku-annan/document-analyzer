"""Test script to verify config loads correctly"""
from app.config import get_settings

def test_config():
    """Test that all config values are loaded correctly"""
    settings = get_settings()
    
    print("✅ Config loaded successfully!")
    print("\n📊 Configuration Values:")
    print(f"  - Database URL: {settings.database_url[:30]}...")
    print(f"  - OpenRouter Model: {settings.openrouter_model}")
    print(f"  - Max File Size (MB): {settings.max_file_size_mb}")
    print(f"  - Storage Type: {settings.storage_type}")
    print(f"  - S3 Endpoint: {settings.s3_endpoint_url}")
    print(f"  - S3 Bucket: {settings.s3_bucket_name}")
    print(f"  - Upload Directory: {settings.upload_dir}")
    print(f"  - App Name: {settings.app_name}")
    print(f"  - Debug Mode: {settings.debug}")
    
    return settings

if __name__ == "__main__":
    test_config()

