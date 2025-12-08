from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document"""
    id: int
    filename: str
    file_size: int
    file_type: str
    message: str

    model_config = ConfigDict(from_attributes=True)


class DocumentAnalysisResponse(BaseModel):
    """Response after analyzing a document"""
    id: int
    summary: Optional[str] = None
    document_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(None, validation_alias="result_metadata", serialization_alias="metadata")
    is_analyzed: str

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(BaseModel):
    """Complete document information"""
    id: int
    filename: str
    file_size: int
    file_type: str
    file_path: str
    extracted_text: Optional[str] = None
    summary: Optional[str] = None
    document_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(None, validation_alias="result_metadata", serialization_alias="metadata")
    is_analyzed: str
    analysis_error: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str


class DocumentDeleteResponse(BaseModel):
    """Response after deleting a document"""
    message: str
    id: int
    filename: str
    file_deleted_from_storage: bool


class DocumentListResponse(BaseModel):
    """Paginated response for listing documents"""
    documents: List[DocumentDetailResponse]
    total: int
    skip: int
    limit: int
    message: Optional[str] = None


class BulkDeleteResponse(BaseModel):
    """Response after deleting all documents"""
    message: str
    deleted_count: int
    total_documents: int
    warning: Optional[str] = None
    failed_deletions: Optional[list] = None