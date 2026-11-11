from dataclasses import dataclass
from typing import Any, Sequence

from sqlalchemy.orm import Session

from app.services.keyword_retrieval_service import (
    KeywordRetrievedChunk,
    keyword_search,
)
from app.services.retrieval_service import (
    RetrievedChunk,
    semantic_search,
)


@dataclass
class HybridRetrievedChunk:
    chunk_id: int
    document_id: int
    document_name: str
    page_number: int
    chunk_index: int
    content: str
    rrf_score: float
    semantic_rank: int | None
    keyword_rank: int | None


def reciprocal_rank_fusion(
    semantic_results: Sequence[Any],
    keyword_results: Sequence[Any],
    k: int = 60,
    rrf_k: int | None = None,
) -> list[HybridRetrievedChunk]:
    """
    Combine semantic and keyword rankings using Reciprocal Rank Fusion (RRF).

    Formula:
        RRF(d) = sum_{r in R} (1 / (k + rank_r(d)))
    """
    actual_k = rrf_k if rrf_k is not None else k
    if actual_k <= 0:
        raise ValueError("RRF constant must be greater than zero.")

    fused_results: dict[int, dict[str, Any]] = {}

    for rank, item in enumerate(semantic_results, start=1):
        cid = item.chunk_id
        fused_results[cid] = {
            "chunk_id": cid,
            "document_id": item.document_id,
            "document_name": item.document_name,
            "page_number": item.page_number,
            "chunk_index": item.chunk_index,
            "content": item.content,
            "rrf_score": 1.0 / (actual_k + rank),
            "semantic_rank": rank,
            "keyword_rank": None,
        }

    for rank, item in enumerate(keyword_results, start=1):
        cid = item.chunk_id
        if cid in fused_results:
            existing = fused_results[cid]
            if (
                existing["document_id"] != item.document_id
                or existing["document_name"] != item.document_name
                or existing["page_number"] != item.page_number
                or existing["chunk_index"] != item.chunk_index
                or existing["content"] != item.content
            ):
                raise ValueError(
                    f"Conflicting chunk metadata detected for chunk {cid}."
                )

            existing["rrf_score"] += 1.0 / (actual_k + rank)
            existing["keyword_rank"] = rank
        else:
            fused_results[cid] = {
                "chunk_id": cid,
                "document_id": item.document_id,
                "document_name": item.document_name,
                "page_number": item.page_number,
                "chunk_index": item.chunk_index,
                "content": item.content,
                "rrf_score": 1.0 / (actual_k + rank),
                "semantic_rank": None,
                "keyword_rank": rank,
            }

    # Deterministic sorting: highest RRF score first, ties broken by chunk_id ascending
    sorted_items = sorted(
        fused_results.values(),
        key=lambda x: (-x["rrf_score"], x["chunk_id"]),
    )

    return [
        HybridRetrievedChunk(
            chunk_id=item["chunk_id"],
            document_id=item["document_id"],
            document_name=item["document_name"],
            page_number=item["page_number"],
            chunk_index=item["chunk_index"],
            content=item["content"],
            rrf_score=item["rrf_score"],
            semantic_rank=item["semantic_rank"],
            keyword_rank=item["keyword_rank"],
        )
        for item in sorted_items
    ]


def hybrid_search(
    db: Session,
    query: str,
    user_id: int,
    top_k: int = 5,
    candidate_k: int = 20,
    rrf_k: int = 60,
    k: int | None = None,
) -> list[HybridRetrievedChunk]:
    """
    Perform hybrid retrieval combining semantic and keyword search via RRF.
    """
    if k is not None:
        rrf_k = k

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if user_id <= 0:
        raise ValueError("Invalid user ID.")

    if not 1 <= top_k <= 50:
        raise ValueError("top_k must be between 1 and 50.")

    if candidate_k <= 0:
        raise ValueError("candidate_k must be greater than zero.")

    if rrf_k <= 0:
        raise ValueError("RRF constant must be greater than zero.")

    search_limit = min(candidate_k, 50)

    semantic_results = semantic_search(
        db=db,
        query=query,
        user_id=user_id,
        top_k=search_limit,
    )

    keyword_results = keyword_search(
        db=db,
        query=query,
        user_id=user_id,
        top_k=search_limit,
    )

    fused_results = reciprocal_rank_fusion(
        semantic_results=semantic_results,
        keyword_results=keyword_results,
        k=rrf_k,
    )

    return fused_results[:top_k]

