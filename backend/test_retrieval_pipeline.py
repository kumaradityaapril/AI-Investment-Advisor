
from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.services.hybrid_retrieval_service import HybridRetrievedChunk
from app.services.reranking_service import RerankedChunk
from app.services.retrieval_pipeline_service import retrieve_and_rerank


def make_hybrid_chunk(chunk_id: int) -> HybridRetrievedChunk:
    return HybridRetrievedChunk(
        chunk_id=chunk_id,
        document_id=1,
        document_name="annual_report.pdf",
        page_number=chunk_id,
        chunk_index=chunk_id - 1,
        content=f"Financial information for chunk {chunk_id}.",
        rrf_score=0.02,
        semantic_rank=chunk_id,
        keyword_rank=chunk_id,
    )


def make_reranked_chunk(chunk_id: int, score: float) -> RerankedChunk:
    return RerankedChunk(
        chunk_id=chunk_id,
        document_id=1,
        document_name="annual_report.pdf",
        page_number=chunk_id,
        chunk_index=chunk_id - 1,
        content=f"Financial information for chunk {chunk_id}.",
        rrf_score=0.02,
        semantic_rank=chunk_id,
        keyword_rank=chunk_id,
        relevance_score=score,
        rerank_rank=1,
    )


def run_tests():
    db = MagicMock()
    candidates = [make_hybrid_chunk(i) for i in range(1, 6)]
    final_results = [
        make_reranked_chunk(3, 98),
        make_reranked_chunk(1, 90),
    ]

    # 1. Hybrid retrieval runs before reranking.
    with (
        patch(
            "app.services.retrieval_pipeline_service.hybrid_search",
            return_value=candidates,
        ) as mock_hybrid,
        patch(
            "app.services.retrieval_pipeline_service.rerank_chunks",
            return_value=final_results,
        ) as mock_rerank,
    ):
        results = retrieve_and_rerank(
            db=db,
            query="Explain profitability in FY2025",
            user_id=10,
            top_k=2,
            candidate_k=5,
            rrf_k=60,
        )

    mock_hybrid.assert_called_once_with(
        db=db,
        query="Explain profitability in FY2025",
        user_id=10,
        top_k=5,
        candidate_k=5,
        rrf_k=60,
    )

    mock_rerank.assert_called_once_with(
        query="Explain profitability in FY2025",
        chunks=candidates,
        top_k=2,
    )

    assert results == final_results

    print("PASS: Hybrid retrieval and reranking connected correctly")

    # 2. Empty retrieval skips Gemini reranking.
    with (
        patch(
            "app.services.retrieval_pipeline_service.hybrid_search",
            return_value=[],
        ),
        patch(
            "app.services.retrieval_pipeline_service.rerank_chunks"
        ) as mock_rerank,
    ):
        results = retrieve_and_rerank(
            db=db,
            query="Unknown financial information",
            user_id=10,
        )

    assert results == []
    mock_rerank.assert_not_called()

    print("PASS: Empty retrieval skips Gemini reranking")

    # 3. Invalid query rejected before retrieval.
    with patch(
        "app.services.retrieval_pipeline_service.hybrid_search"
    ) as mock_hybrid:
        try:
            retrieve_and_rerank(
                db=db,
                query="   ",
                user_id=10,
            )
            raise AssertionError("Expected empty query rejection")
        except ValueError:
            pass

        mock_hybrid.assert_not_called()

    print("PASS: Invalid query rejected before retrieval")

    # 4. Invalid user ID rejected.
    for invalid_user_id in [0, -1]:
        try:
            retrieve_and_rerank(
                db=db,
                query="Revenue",
                user_id=invalid_user_id,
            )
            raise AssertionError("Expected invalid user ID rejection")
        except ValueError:
            pass

    print("PASS: Invalid user IDs rejected")

    # 5. Invalid top_k rejected.
    for invalid_top_k in [0, 51]:
        try:
            retrieve_and_rerank(
                db=db,
                query="Revenue",
                user_id=10,
                top_k=invalid_top_k,
            )
            raise AssertionError("Expected invalid top_k rejection")
        except ValueError:
            pass

    print("PASS: Invalid top-K values rejected")

    # 6. Candidate count must be at least top_k.
    try:
        retrieve_and_rerank(
            db=db,
            query="Revenue",
            user_id=10,
            top_k=5,
            candidate_k=3,
        )
        raise AssertionError("Expected invalid candidate count rejection")
    except ValueError:
        pass

    print("PASS: Candidate count must be at least top-K")

    # 7. Candidate count cannot exceed the supported maximum.
    try:
        retrieve_and_rerank(
            db=db,
            query="Revenue",
            user_id=10,
            top_k=5,
            candidate_k=51,
        )
        raise AssertionError("Expected candidate limit rejection")
    except ValueError:
        pass

    print("PASS: Maximum candidate limit enforced")

    # 8. Candidate count respects configured reranker limit.
    with patch.object(
        settings,
        "reranking_max_candidates",
        10,
    ):
        try:
            retrieve_and_rerank(
                db=db,
                query="Revenue",
                user_id=10,
                top_k=5,
                candidate_k=20,
            )
            raise AssertionError("Expected configured limit rejection")
        except ValueError:
            pass

    print("PASS: Configured reranking candidate limit enforced")

    # 9. Invalid RRF constant rejected.
    try:
        retrieve_and_rerank(
            db=db,
            query="Revenue",
            user_id=10,
            rrf_k=0,
        )
        raise AssertionError("Expected invalid RRF constant rejection")
    except ValueError:
        pass

    print("PASS: Invalid RRF constant rejected")

    # 10. Hybrid retrieval failure propagates.
    with patch(
        "app.services.retrieval_pipeline_service.hybrid_search",
        side_effect=RuntimeError("Simulated retrieval failure"),
    ):
        try:
            retrieve_and_rerank(
                db=db,
                query="Revenue",
                user_id=10,
            )
            raise AssertionError("Expected retrieval failure")
        except RuntimeError as exc:
            assert "retrieval failure" in str(exc)

    print("PASS: Hybrid retrieval failures propagated")

    # 11. Reranking failure propagates.
    with (
        patch(
            "app.services.retrieval_pipeline_service.hybrid_search",
            return_value=candidates,
        ),
        patch(
            "app.services.retrieval_pipeline_service.rerank_chunks",
            side_effect=RuntimeError("Simulated reranking failure"),
        ),
    ):
        try:
            retrieve_and_rerank(
                db=db,
                query="Revenue",
                user_id=10,
            )
            raise AssertionError("Expected reranking failure")
        except RuntimeError as exc:
            assert "reranking failure" in str(exc)

    print("PASS: Reranking failures propagated")

    print("\nALL RETRIEVAL PIPELINE UNIT TESTS PASSED!")


if __name__ == "__main__":
    run_tests()
