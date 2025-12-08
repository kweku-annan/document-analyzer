from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
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
    DocumentListResponse,
    ErrorResponse
)
from app.services.storage import storage_service
from app.services.extractor import text_extractor
from app.services.analyzer import analyzer_service

settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered document analysis service",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Document Analyzer API is running",
        "version": "1.0.0"
    }


@app.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse}
    }
)
async def upload_document(
        file: UploadFile = File(..., description="PDF or DOCX file to upload (max 5MB)"),
        db: Session = Depends(get_db)
):
    """
    Upload a document (PDF or DOCX) for processing.

    Steps:
    1. Validate file type and size
    2. Save file to storage
    3. Extract text from document
    4. Save metadata to database
    """

    # 1. Validate file type
    allowed_types = ['pdf', 'docx', 'doc']
    file_extension = file.filename.split('.')[-1].lower()

    if file_extension not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '.{file_extension}' not supported. Allowed types: {', '.join(allowed_types)}"
        )

    # 2. Validate file size
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > settings.max_file_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size} bytes) exceeds maximum allowed size ({settings.max_file_size_mb} bytes)"
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )

    try:
        # 3. Save file to storage
        file_path = storage_service.save_file(file_content, file.filename)

        # 4. Extract text from document
        extracted_text = text_extractor.extract_text(
            file_path=storage_service.get_file_path(file_path),
            file_type=file_extension
        )

        # 5. Save to database
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
        # Clean up file if database operation fails
        if 'file_path' in locals():
            storage_service.delete_file(file_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )
    finally:
        # Clean up temp files if using Minio
        storage_service.cleanup_temp_files()


@app.get(
    "/documents/{document_id}",
    response_model=DocumentDetailResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """
    Get complete document information including analysis results.
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found"
        )

    return document


@app.get("/documents", response_model=DocumentListResponse)
async def list_documents(
        skip: int = 0,
        limit: int = 10,
        db: Session = Depends(get_db)
):
    """
    List all documents with pagination.
    
    Returns a structured response with:
    - List of documents
    - Total count of all documents in database
    - Pagination info (skip, limit)
    - Helpful message when no documents exist
    """
    # Get total count
    total = db.query(Document).count()
    
    # Get paginated documents
    documents = db.query(Document).offset(skip).limit(limit).all()
    
    # Create response with helpful message if empty
    message = None
    if total == 0:
        message = "No documents found. Upload your first document using POST /documents/upload"
    elif len(documents) == 0 and skip > 0:
        message = f"No documents found at this offset. Total documents available: {total}"
    
    return DocumentListResponse(
        documents=documents,
        total=total,
        skip=skip,
        limit=limit,
        message=message
    )


@app.post(
    "/documents/{document_id}/analyze",
    response_model=DocumentAnalysisResponse,
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse}
    }
)
async def analyze_document(document_id: int, db: Session = Depends(get_db)):
    """
    Analyze a document using AI (OpenRouter API).

    This endpoint:
    1. Retrieves the document from database
    2. Sends extracted text to OpenRouter LLM
    3. Receives summary, document type, and metadata
    4. Saves analysis results to database

    Note: You need to set OPENROUTER_API_KEY in .env file
    """

    # 1. Get document from database
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found"
        )

    # 2. Check if document has extracted text
    if not document.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no extracted text. Please re-upload the document."
        )

    # 3. Check if already analyzed
    if document.is_analyzed == "completed":
        return DocumentAnalysisResponse(
            id=document.id,
            summary=document.summary,
            document_type=document.document_type,
            metadata=document.metadata,
            is_analyzed=document.is_analyzed
        )

    try:
        # 4. Analyze document using OpenRouter
        analysis_result = await analyzer_service.analyze_document(document.extracted_text)

        # 5. Update document in database
        document.summary = analysis_result["summary"]
        document.document_type = analysis_result["document_type"]
        document.metadata = analysis_result["metadata"]
        document.is_analyzed = "completed"
        document.analysis_error = None

        db.commit()
        db.refresh(document)

        return DocumentAnalysisResponse(
            id=document.id,
            summary=document.summary,
            document_type=document.document_type,
            metadata=document.metadata,
            is_analyzed=document.is_analyzed
        )

    except Exception as e:
        # Save error to database
        document.is_analyzed = "failed"
        document.analysis_error = str(e)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@app.get(
    "/documents/{document_id}/download",
    responses={404: {"model": ErrorResponse}}
)
async def get_download_url(document_id: int, db: Session = Depends(get_db)):
    """
    Get a pre-signed URL to download the document file.

    For Minio storage: Returns a temporary download URL (valid for 1 hour)
    For local storage: Returns file path
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found"
        )

    try:
        download_url = storage_service.get_file_url(document.file_path)
        return {
            "id": document.id,
            "filename": document.filename,
            "download_url": download_url,
            "expires_in": "1 hour" if settings.storage_type == "minio" else "N/A"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}"
        )


@app.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse}}
)
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """
    Delete a document and its associated file from storage.

    This endpoint:
    1. Retrieves the document from database
    2. Deletes the file from storage (Minio or local)
    3. Deletes the document record from database
    """
    # 1. Get document from database
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {document_id} not found"
        )

    try:
        # 2. Delete file from storage
        file_deleted = storage_service.delete_file(document.file_path)

        # 3. Delete document record from database
        db.delete(document)
        db.commit()

        return {
            "message": "Document deleted successfully",
            "id": document_id,
            "filename": document.filename,
            "file_deleted_from_storage": file_deleted
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@app.delete(
    "/documents",
    status_code=status.HTTP_200_OK
)
async def delete_all_documents(
        confirm: bool = False,
        db: Session = Depends(get_db)
):
    """
    Delete ALL documents and their associated files from storage.

    WARNING: This is a destructive operation that cannot be undone!

    Query Parameters:
    - confirm: Must be set to true to confirm deletion

    This endpoint:
    1. Checks confirmation parameter
    2. Retrieves all documents from database
    3. Deletes all files from storage
    4. Deletes all document records from database
    """
    # Safety check: require explicit confirmation
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deletion not confirmed. Add '?confirm=true' to the URL to confirm deletion of all documents."
        )

    try:
        # 1. Get all documents
        documents = db.query(Document).all()

        if not documents:
            return {
                "message": "No documents to delete",
                "deleted_count": 0
            }

        # 2. Delete all files from storage
        deleted_count = 0
        failed_deletions = []

        for document in documents:
            try:
                storage_service.delete_file(document.file_path)
                deleted_count += 1
            except Exception as e:
                failed_deletions.append({
                    "id": document.id,
                    "filename": document.filename,
                    "error": str(e)
                })

        # 3. Delete all document records from database
        db.query(Document).delete()
        db.commit()

        response = {
            "message": f"Successfully deleted {deleted_count} document(s)",
            "deleted_count": deleted_count,
            "total_documents": len(documents)
        }

        if failed_deletions:
            response["warning"] = "Some files could not be deleted from storage"
            response["failed_deletions"] = failed_deletions

        return response

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete documents: {str(e)}"
        )