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


class ErrorResponse(BaseModel):
    """Standard error response model."""
    detail: str