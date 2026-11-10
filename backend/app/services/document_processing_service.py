from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Document
from app.services.pdf_extraction_service import (
    PDFExtractionError,
    extract_pdf_text,
)


def _get_upload_directory() -> Path:
    """Resolve the configured document upload directory."""
    directory = Path(settings.upload_dir)
    if not directory.is_absolute():
        directory = Path(__file__).resolve().parents[2] / directory
    return directory


def process_document(
    db: Session,
    document_id: int,
    user_id: int,
) -> Document:
    """Extract PDF text and save it against the user's document."""
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == user_id,
        )
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    if document.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is already being processed.",
        )

    if document.status == "processed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document has already been processed.",
        )

    document.status = "processing"
    db.commit()
    db.refresh(document)

    file_path = _get_upload_directory() / document.stored_filename

    try:
        extracted_text = extract_pdf_text(file_path)
        document.extracted_text = extracted_text
        document.status = "processed"
        db.commit()
        db.refresh(document)
        return document
    except PDFExtractionError:
        db.rollback()
        document = (
            db.query(Document)
            .filter(
                Document.id == document_id,
                Document.user_id == user_id,
            )
            .first()
        )
        if document is not None:
            document.status = "failed"
            db.commit()
        raise
    except Exception:
        db.rollback()
        document = (
            db.query(Document)
            .filter(
                Document.id == document_id,
                Document.user_id == user_id,
            )
            .first()
        )
        if document is not None:
            document.status = "failed"
            db.commit()
        raise

