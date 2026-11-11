
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk
from app.services.embedding_service import (
    EmbeddingGenerationError,
    generate_query_embedding,
)


class RetrievalError(Exception):
    """Raised when document retrieval fails."""


@dataclass
class RetrievedChunk:
    chunk_id: int
    document_id: int
    document_name: str
    page_number: int
    chunk_index: int
    content: str
    distance: float
    similarity: float


def semantic_search(
    db: Session,
    query: str,
    user_id: int,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    """
    Retrieve the most semantically relevant document chunks
    belonging to the authenticated user.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if user_id <= 0:
        raise ValueError("Invalid user ID.")

    if not 1 <= top_k <= 50:
        raise ValueError("top_k must be between 1 and 50.")

    try:
        query_embedding = generate_query_embedding(query)

        distance = DocumentChunk.embedding.cosine_distance(
            query_embedding
        ).label("distance")

        results = (
            db.query(DocumentChunk, Document, distance)
            .join(
                Document,
                DocumentChunk.document_id == Document.id,
            )
            .filter(
                Document.user_id == user_id,
                Document.status == "processed",
                Document.indexing_status == "indexed",
            )
            .order_by(distance.asc())
            .limit(top_k)
            .all()
        )

        retrieved_chunks = []

        for chunk, document, chunk_distance in results:
            chunk_distance = float(chunk_distance)

            similarity = max(
                0.0,
                min(1.0, 1.0 - chunk_distance),
            )

            retrieved_chunks.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    document_name=document.original_filename,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    distance=chunk_distance,
                    similarity=similarity,
                )
            )

        return retrieved_chunks

    except EmbeddingGenerationError as exc:
        raise RetrievalError(
            "Failed to generate the search query embedding."
        ) from exc

    except Exception as exc:
        if isinstance(exc, (ValueError,)):
            raise

        raise RetrievalError(
            "Document semantic retrieval failed."
        ) from exc
