
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models import Document, User
from app.schemas.document import DocumentResponse, DocumentTextResponse
from app.services.document_processing_service import process_document
from app.services.document_service import create_document


router = APIRouter(prefix="/documents", tags=["Documents"])


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
