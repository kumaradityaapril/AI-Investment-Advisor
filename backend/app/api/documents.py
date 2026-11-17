from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models import Document, DocumentChunk, User
from app.schemas.document import (
    DocumentIndexResponse,
    DocumentResponse,
    DocumentTextResponse,
)
from app.services.document_indexing_service import index_document
from app.services.document_processing_service import process_document
from app.services.document_service import create_document


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get(
    "",
    response_model=list[DocumentResponse],
    status_code=status.HTTP_200_OK,
)
def get_user_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[DocumentResponse]:
    """List all uploaded financial documents for the authenticated user."""
    results = (
        db.query(
            Document,
            func.count(DocumentChunk.id).label("chunk_count"),
        )
        .outerjoin(DocumentChunk, Document.id == DocumentChunk.document_id)
        .filter(Document.user_id == current_user.id)
        .group_by(Document.id)
        .order_by(Document.created_at.desc())
        .all()
    )

    response_list: list[DocumentResponse] = []
    for doc, chunk_count in results:
        doc_res = DocumentResponse(
            id=doc.id,
            original_filename=doc.original_filename,
            filename=doc.original_filename,
            content_type=doc.content_type,
            file_size_bytes=doc.file_size_bytes,
            status=doc.status,  # type: ignore
            indexing_status=doc.indexing_status,  # type: ignore
            uploaded_at=doc.created_at,
            created_at=doc.created_at,
            indexed_at=doc.indexed_at,
            chunk_count=chunk_count or 0,
        )
        response_list.append(doc_res)
    return response_list


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    file: Annotated[UploadFile, File()],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Document:
    """Upload a PDF financial document for the authenticated user."""
    return create_document(
        db=db,
        user_id=current_user.id,
        file=file,
    )


@router.post(
    "/{document_id}/process",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
)
def process_uploaded_document(
    document_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Document:
    """Extract and save text from an uploaded PDF."""
    return process_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
    )


@router.post(
    "/{document_id}/index",
    response_model=DocumentIndexResponse,
    status_code=status.HTTP_200_OK,
)
def index_uploaded_document(
    document_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Generate and persist embeddings for an authenticated user's document."""
    document = index_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
    )
    chunk_count = (
        db.query(func.count(DocumentChunk.id))
        .filter(DocumentChunk.document_id == document_id)
        .scalar()
    )
    return {
        "id": document.id,
        "indexing_status": document.indexing_status,
        "indexed_at": document.indexed_at,
        "chunk_count": chunk_count or 0,
    }


@router.get(
    "/{document_id}/text",
    response_model=DocumentTextResponse,
)
def get_extracted_document_text(
    document_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Document:
    """Retrieve extracted text for an authenticated user's document."""
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
        .first()
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    if document.status != "processed" or not document.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document text is not available yet.",
        )
    return document
