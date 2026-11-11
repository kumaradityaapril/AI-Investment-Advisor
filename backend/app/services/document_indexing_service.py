from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import func, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Document
from app.services.document_chunking_service import chunk_document_pages
from app.services.document_persistence_service import replace_document_chunks
from app.services.embedding_service import (
    EmbeddingGenerationError,
    generate_document_embeddings,
)
from app.services.pdf_extraction_service import (
    PDFExtractionError,
    extract_pdf_pages,
)


def _get_upload_directory() -> Path:
    """Resolve the configured document upload directory."""
    directory = Path(settings.upload_dir)

    if not directory.is_absolute():
        directory = Path(__file__).resolve().parents[2] / directory

    return directory


def _claim_document_for_indexing(
    db: Session,
    document_id: int,
    user_id: int,
) -> Document:
    """
    Atomically claim a document for indexing.

    Fails with 404 if the document does not exist for the user.
    Fails with 409 if the document is not processed, missing text,
    or already being indexed.
    """
    stmt = (
        update(Document)
        .where(
            Document.id == document_id,
            Document.user_id == user_id,
            Document.status == "processed",
            Document.extracted_text.isnot(None),
            Document.indexing_status != "indexing",
        )
        .values(
            indexing_status="indexing",
            indexing_started_at=func.now(),
        )
    )
    result = db.execute(stmt)

    if result.rowcount == 0:
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

        if document.status != "processed" or not document.extracted_text:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document must be processed before indexing.",
            )

        if document.indexing_status == "indexing":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document is already being indexed.",
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document cannot be claimed for indexing.",
        )

    db.commit()

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == user_id,
        )
        .first()
    )
    return document


def _mark_indexing_failed(
    db: Session,
    document_id: int,
    user_id: int,
) -> None:
    """Mark an indexing attempt as failed without modifying existing chunks."""
    try:
        db.rollback()

        document = (
            db.query(Document)
            .filter(
                Document.id == document_id,
                Document.user_id == user_id,
            )
            .with_for_update()
            .first()
        )

        if document is not None and document.indexing_status == "indexing":
            document.indexing_status = "failed"
            document.indexing_started_at = None
            db.commit()

    except Exception:
        db.rollback()
        # Preserve the original indexing exception.


def index_document(
    db: Session,
    document_id: int,
    user_id: int,
) -> Document:
    """
    Generate and persist embeddings for an authenticated user's document.

    Gemini requests run outside database transactions.
    Existing chunks are replaced atomically after all embeddings
    have been generated successfully.
    """
    document = _claim_document_for_indexing(
        db=db,
        document_id=document_id,
        user_id=user_id,
    )

    try:
        file_path = _get_upload_directory() / document.stored_filename

        pages = extract_pdf_pages(file_path)

        chunks = chunk_document_pages(
            pages=pages,
            chunk_size=1000,
            chunk_overlap=200,
        )

        if not chunks:
            raise PDFExtractionError(
                "No document chunks were generated."
            )

        chunk_texts = [
            chunk["content"]
            for chunk in chunks
        ]

        embeddings = generate_document_embeddings(chunk_texts)

        if len(chunks) != len(embeddings):
            raise EmbeddingGenerationError(
                "Chunk and embedding counts do not match."
            )

        document = (
            db.query(Document)
            .filter(
                Document.id == document_id,
                Document.user_id == user_id,
            )
            .with_for_update()
            .first()
        )

        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        if document.indexing_status != "indexing":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document indexing state has changed.",
            )

        replace_document_chunks(
            db=db,
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings,
        )

        document.indexing_status = "indexed"
        document.indexing_started_at = None
        document.indexed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(document)

        return document

    except Exception as exc:
        _mark_indexing_failed(
            db=db,
            document_id=document_id,
            user_id=user_id,
        )

        if isinstance(exc, HTTPException):
            raise

        if isinstance(exc, EmbeddingGenerationError):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Embedding generation failed. Please retry indexing.",
            ) from exc

        if isinstance(exc, PDFExtractionError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        if isinstance(exc, ValueError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document indexing failed.",
        ) from exc


def recover_stale_document_indexing(db: Session) -> int:
    """
    Mark documents with abandoned indexing operations as failed.

    Only documents whose indexing start timestamp is older than
    the configured timeout are eligible for recovery.

    Returns the number of documents recovered.
    """
    timeout_minutes = settings.indexing_stale_timeout_minutes
    if timeout_minutes <= 0:
        raise ValueError(
            "Indexing stale timeout must be greater than zero."
        )

    stale_cutoff = (
        datetime.now(timezone.utc)
        - timedelta(minutes=timeout_minutes)
    )

    try:
        result = db.execute(
            update(Document)
            .where(
                Document.indexing_status == "indexing",
                Document.indexing_started_at.is_not(None),
                Document.indexing_started_at < stale_cutoff,
            )
            .values(
                indexing_status="failed",
                indexing_started_at=None,
            )
            .execution_options(synchronize_session=False)
        )
        db.commit()
        return result.rowcount
    except Exception:
        db.rollback()
        raise
