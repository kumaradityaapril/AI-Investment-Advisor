from collections.abc import Sequence
import math

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import DocumentChunk as DocumentChunkModel
from app.services.document_chunking_service import DocumentChunk


def replace_document_chunks(
    db: Session,
    document_id: int,
    chunks: Sequence[DocumentChunk],
    embeddings: list[list[float]],
) -> int:
    """
    Atomically replace all stored chunks for a document.

    The caller owns the database transaction and must commit or roll
    back after this function returns or raises.
    """
    if not chunks:
        raise ValueError("Cannot index a document without chunks.")

    if len(chunks) != len(embeddings):
        raise ValueError(
            "The number of chunks must match the number of embeddings."
        )

    chunk_records = []

    for chunk, embedding in zip(chunks, embeddings):
        page_number = chunk.get("page_number")
        chunk_index = chunk.get("chunk_index")
        content = chunk.get("content")

        if not isinstance(page_number, int) or page_number < 1:
            raise ValueError("Invalid page number in document chunk.")

        if not isinstance(chunk_index, int) or chunk_index < 0:
            raise ValueError("Invalid chunk index in document chunk.")

        if not isinstance(content, str) or not content.strip():
            raise ValueError("Document chunk content cannot be empty.")

        if len(embedding) != settings.embedding_dimensions:
            raise ValueError("Embedding dimension mismatch.")

        if not all(math.isfinite(value) for value in embedding):
            raise ValueError("Embedding contains invalid numeric values.")

        chunk_records.append(
            DocumentChunkModel(
                document_id=document_id,
                chunk_index=chunk_index,
                page_number=page_number,
                content=content,
                embedding=embedding,
            )
        )

    # Delete and insert happen in the caller's transaction.
    # A rollback restores the previously stored chunks.
    db.query(DocumentChunkModel).filter(
        DocumentChunkModel.document_id == document_id
    ).delete(synchronize_session=False)

    db.add_all(chunk_records)
    db.flush()

    return len(chunk_records)
