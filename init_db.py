"""
Script to initialize the database tables.
Run this once to create all tables.
"""
from app.database import Base, engine
from app.models import Document
from app.config import get_settings
import os

def init_database():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

    # Create uploads directory if it doesn't exist
    settings = get_settings()
    uploads_dir = settings.upload_dir
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
        print(f"Created '{uploads_dir}' directory for file uploads.")
    else:
        print(f"'{uploads_dir}' directory already exists.")

if __name__ == "__main__":
    init_database()