from dataclasses import dataclass
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk


class KeywordRetrievalError(Exception):
    """Raised when keyword retrieval fails."""


@dataclass
class KeywordRetrievedChunk:
    chunk_id: int
    document_id: int
    document_name: str
    page_number: int
    chunk_index: int
    content: str
    rank_score: float


def keyword_search(
    db: Session,
    query: str,
    user_id: int,
    top_k: int = 5,
) -> list[KeywordRetrievedChunk]:
    """
    Retrieve document chunks using PostgreSQL full-text search.
    Only searches indexed documents belonging to the user.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if user_id <= 0:
        raise ValueError("Invalid user ID.")

    if not 1 <= top_k <= 50:
        raise ValueError("top_k must be between 1 and 50.")

    try:
        ts_query = func.websearch_to_tsquery("simple", query)
        rank = func.ts_rank_cd(DocumentChunk.search_vector, ts_query).label("rank")

        results = (
            db.query(DocumentChunk, Document, rank)
            .join(
                Document,
                DocumentChunk.document_id == Document.id,
            )
            .filter(
                Document.user_id == user_id,
                Document.status == "processed",
                Document.indexing_status == "indexed",
                DocumentChunk.search_vector.op("@@")(ts_query),
            )
            .order_by(desc("rank"), DocumentChunk.id.asc())
            .limit(top_k)
            .all()
        )

        retrieved_chunks = []
        for chunk, document, rank_score in results:
            retrieved_chunks.append(
                KeywordRetrievedChunk(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    document_name=document.original_filename,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    rank_score=float(rank_score),
                )
            )

        return retrieved_chunks

    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise KeywordRetrievalError(
            "Document keyword retrieval failed."
        ) from exc

