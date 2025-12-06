from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from multipart import file_path
from sqlalchemy.orm import Session
from typing import List
import os

from app.config import get_settings
from app.database import get_db
from app.models import Document
from app.schemas import (
    DocumentUploadResponse,
    DocumentAnalysisResponse,
    DocumentDetailResponse,
    ErrorResponse,
)
from app.services.storage import storage_service
from app.services.extractor import text_extractor

settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered document analysis service.",
    version="1.0.0",
)


@app.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
    }
)
async def upload_document(
        file: UploadFile = File(..., description="PDF or DOCX file to upload (max 10MB)"),
        db: Session = Depends(get_db),
):
    """
    Upload a document (PDF or DOCX) for processing.

    Steps:
    1. Validate file type and size.
    2. Save file to storage.
    3. Extract text content.
    4. Save metadata to database.
    :param file:
    :param db:
    :return:
    """

    # 1. Validate file type and size
    allowed_types = ['pdf', 'docx', 'doc']
    file_extension = file.filename.split('.')[-1].lower()

    if file_extension not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_extension}. Allowed types: {allowed_types}"
        )

    # 2. Validate file size
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {file_size} exceeds the maximum limit of {settings.max_upload_size / (1024 * 1024)} MB."
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    try:
        # Save file to storage
        file_path = storage_service.save_file(file_content, file.filename)

        # Extract text from document
        extracted_text = text_extractor.extract_text(
            file_path=storage_service.get_file_path(file_path),
            file_type=file_extension,
        )

        # Save to database
        db_document = Document(
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_extension,
            extracted_text=extracted_text,
            is_analyzed="pending"
        )

        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        return DocumentUploadResponse(
            id=db_document.id,
            filename=db_document.filename,
            file_size=db_document.file_size,
            file_type=db_document.file_type,
            message="Document uploaded successfully. Use /documents/{id}/analyze to analyze it."
        )

    except Exception as e:
        # Clean up file if database operation fails.
        if 'file_path' in locals():
            storage_service.delete_file(file_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )

@app.get(
    "/documents/{document_id}",
    response_model=DocumentDetailResponse,
    responses={
        404: {"model": ErrorResponse},
    }
)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """
    Get complete document information including analysis results.
    :param document_id:
    :param db:
    :return:
    """

    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found."
        )

    return document

@app.get("/documents", response_model=List[DocumentDetailResponse])
async def list_documents(
        skip: int = 0,
        limit: int = 10,
        db: Session = Depends(get_db)
):
    """
    List all documents with pagination
    :param skip:
    :param limit:
    :param db:
    :return:
    """

    documents = db.query(Document).offset(skip).limit(limit).all()
    return documents