
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.hybrid_retrieval_service import (
    HybridRetrievedChunk,
    hybrid_search,
)
from app.services.reranking_service import (
    RerankedChunk,
    rerank_chunks,
)


def retrieve_and_rerank(
    db: Session,
    query: str,
    user_id: int,
    top_k: int = 5,
    candidate_k: int = 20,
    rrf_k: int = 60,
) -> list[RerankedChunk]:
    """
    Execute hybrid retrieval followed by Gemini reranking.

    Steps:
    1. Retrieve candidate chunks using semantic and keyword search.
    2. Combine retrieval rankings using RRF.
    3. Rerank candidates using Gemini.
    4. Return the final top-K relevant chunks.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if user_id <= 0:
        raise ValueError("Invalid user ID.")

    if not 1 <= top_k <= 50:
        raise ValueError("top_k must be between 1 and 50.")

    if not top_k <= candidate_k <= 50:
        raise ValueError(
            "candidate_k must be at least top_k and at most 50."
        )

    if candidate_k > settings.reranking_max_candidates:
        raise ValueError(
            f"candidate_k cannot exceed "
            f"{settings.reranking_max_candidates}."
        )

    if rrf_k <= 0:
        raise ValueError("rrf_k must be greater than zero.")

    # Step 1: Retrieve a larger candidate pool.
    hybrid_results: list[HybridRetrievedChunk] = hybrid_search(
        db=db,
        query=query,
        user_id=user_id,
        top_k=candidate_k,
        candidate_k=candidate_k,
        rrf_k=rrf_k,
    )

    # Step 2: Handle empty retrieval without calling Gemini.
    if not hybrid_results:
        return []

    # Step 3: Rerank the retrieved candidates.
    final_results = rerank_chunks(
        query=query,
        chunks=hybrid_results,
        top_k=top_k,
    )

    return final_results
