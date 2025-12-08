from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class Document(Base):
    """
    Database model for storing document information.

    This table stores:
    - File metadata (name, type, size)
    - Extracted text content
    - AI analysis results (summary, document type, metadata)
    """
    __tablename__ = "documents"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # File information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False) # Path where the file is stored
    file_type = Column(String(50), nullable=False)  # e.g., 'pdf', 'docx'
    file_size = Column(Integer, nullable=False)     # Size in bytes

    # Extracted content
    extracted_text = Column(Text, nullable=True)  # Full text extracted from the document

    # AI analysis results
    summary = Column(Text, nullable=True)   # AI-generated summary of the document
    document_type = Column(String(100), nullable=True)
    result_metadata = Column(JSON, nullable=True)  # Additional metadata extracted by AI (date, sender, amount, etc.)

    # Analysis status
    is_analyzed = Column(String(20), default="pending") # 'pending', 'completed', 'failed'
    analysis_error = Column(Text, nullable=True) # Error message if analysis failed

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', file_type='{self.file_type}', is_analyzed='{self.is_analyzed}')>"