from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""
    id: int
    filename: str
    file_type: str
    file_size: int
    message: str

    class Config:
        from_attributes = True


class DocumentAnalysisResponse(BaseModel):
    """Response after a analyzing a document."""
    id: int
    summary: Optional[str] = None
    document_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_analyzed: str

    class Config:
        from_attributes = True


class DocumentDetailResponse(BaseModel):
    """Complete document information"""
    id: int
    filename: str
    file_type: str
    file_size: int
    file_path: str
    extracted_text: Optional[str] = None
    summary: Optional[str] = None
    document_type: Optional[str] = None
    document_metadata: Optional[Dict[str, Any]] = None
    is_analyzed: str
    analysis_error: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ErrorResponse(BaseModel):
    """Standard error response model."""
    detail: str