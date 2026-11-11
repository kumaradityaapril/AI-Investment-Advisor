
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.services.hybrid_retrieval_service import HybridRetrievedChunk
from app.services.reranking_service import (
    RerankingError,
    RerankingItem,
    RerankingResponse,
    _validate_scores,
    rerank_chunks,
)


def make_chunk(
    chunk_id: int,
    content: str,
    rrf_score: float = 0.02,
    semantic_rank: int | None = None,
    keyword_rank: int | None = None,
) -> HybridRetrievedChunk:
    return HybridRetrievedChunk(
        chunk_id=chunk_id,
        document_id=1,
        document_name="financial-report.pdf",
        page_number=chunk_id,
        chunk_index=chunk_id - 1,
        content=content,
        rrf_score=rrf_score,
        semantic_rank=semantic_rank,
        keyword_rank=keyword_rank,
    )


def make_response(scores: dict[int, float]):
    """Create a mock Gemini structured response."""
    return SimpleNamespace(
        parsed=RerankingResponse(
            results=[
                RerankingItem(
                    chunk_id=chunk_id,
                    relevance_score=score,
                )
                for chunk_id, score in scores.items()
            ]
        )
    )


def run_tests():
    chunks = [
        make_chunk(
            1,
            "Annual revenue increased by 20 percent.",
            rrf_score=0.03,
            semantic_rank=1,
            keyword_rank=2,
        ),
        make_chunk(
            2,
            "EBITDA margin improved to 25 percent.",
            rrf_score=0.025,
            semantic_rank=2,
            keyword_rank=1,
        ),
        make_chunk(
            3,
            "The company expanded its workforce.",
            rrf_score=0.02,
            semantic_rank=3,
        ),
    ]

    # --------------------------------------------------
    # 1. Relevance score determines the final ranking.
    # --------------------------------------------------
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = make_response(
        {
            1: 70,
            2: 98,
            3: 15,
        }
    )

    with patch(
        "app.services.reranking_service._get_gemini_client",
        return_value=fake_client,
    ):
        results = rerank_chunks(
            query="Explain the company's EBITDA margin.",
            chunks=chunks,
            top_k=3,
        )

    assert [item.chunk_id for item in results] == [2, 1, 3]
    assert [item.relevance_score for item in results] == [98, 70, 15]
    assert [item.rerank_rank for item in results] == [1, 2, 3]

    print("PASS: Relevance scores determine final ranking")

    # --------------------------------------------------
    # 2. RRF score breaks relevance-score ties.
    # --------------------------------------------------
    tied_chunks = [
        make_chunk(10, "First chunk", rrf_score=0.01),
        make_chunk(11, "Second chunk", rrf_score=0.03),
    ]

    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = make_response(
        {
            10: 80,
            11: 80,
        }
    )

    with patch(
        "app.services.reranking_service._get_gemini_client",
        return_value=fake_client,
    ):
        results = rerank_chunks(
            query="Financial information",
            chunks=tied_chunks,
            top_k=2,
        )

    assert [item.chunk_id for item in results] == [11, 10]

    print("PASS: RRF score breaks relevance ties")

    # --------------------------------------------------
    # 3. Chunk ID breaks both relevance and RRF ties.
    # --------------------------------------------------
    tied_chunks = [
        make_chunk(9, "Chunk nine", rrf_score=0.02),
        make_chunk(4, "Chunk four", rrf_score=0.02),
    ]

    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = make_response(
        {
            9: 75,
            4: 75,
        }
    )

    with patch(
        "app.services.reranking_service._get_gemini_client",
        return_value=fake_client,
    ):
        results = rerank_chunks(
            query="Financial information",
            chunks=tied_chunks,
            top_k=2,
        )

    assert [item.chunk_id for item in results] == [4, 9]

    print("PASS: Chunk ID provides deterministic tie-breaking")

    # --------------------------------------------------
    # 4. Original content and metadata are preserved.
    # --------------------------------------------------
    original = chunks[0]

    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = make_response(
        {1: 95, 2: 80, 3: 20}
    )

    with patch(
        "app.services.reranking_service._get_gemini_client",
        return_value=fake_client,
    ):
        results = rerank_chunks(
            query="Revenue",
            chunks=chunks,
            top_k=3,
        )

    result = next(item for item in results if item.chunk_id == 1)

    assert result.content == original.content
    assert result.document_id == original.document_id
    assert result.document_name == original.document_name
    assert result.page_number == original.page_number
    assert result.chunk_index == original.chunk_index
    assert result.semantic_rank == original.semantic_rank
    assert result.keyword_rank == original.keyword_rank
    assert result.rrf_score == original.rrf_score

    print("PASS: Original content and metadata preserved")

    # --------------------------------------------------
    # 5. Multiple batches are processed correctly.
    # --------------------------------------------------
    batch_chunks = [
        make_chunk(
            chunk_id,
            f"Financial content for chunk {chunk_id}",
        )
        for chunk_id in range(1, 6)
    ]

    fake_client = MagicMock()

    fake_client.models.generate_content.side_effect = [
        make_response({1: 50, 2: 60}),
        make_response({3: 70, 4: 80}),
        make_response({5: 90}),
    ]

    with (
        patch(
            "app.services.reranking_service._get_gemini_client",
            return_value=fake_client,
        ),
        patch.object(
            settings,
            "reranking_batch_size",
            2,
        ),
    ):
        results = rerank_chunks(
            query="Financial performance",
            chunks=batch_chunks,
            top_k=5,
        )

    assert fake_client.models.generate_content.call_count == 3
    assert len(results) == 5
    assert [item.chunk_id for item in results] == [5, 4, 3, 2, 1]

    print("PASS: Multiple batches processed correctly")

    # --------------------------------------------------
    # 6. Duplicate chunk IDs in Gemini response rejected.
    # --------------------------------------------------
    duplicate_response = RerankingResponse(
        results=[
            RerankingItem(chunk_id=1, relevance_score=90),
            RerankingItem(chunk_id=1, relevance_score=80),
        ]
    )

    try:
        _validate_scores(
            chunks=[chunks[0]],
            response=duplicate_response,
        )
        raise AssertionError("Expected duplicate IDs to be rejected")
    except RerankingError:
        pass

    print("PASS: Duplicate chunk IDs rejected")

    # --------------------------------------------------
    # 7. Missing chunk IDs rejected.
    # --------------------------------------------------
    missing_response = RerankingResponse(
        results=[
            RerankingItem(chunk_id=1, relevance_score=90),
        ]
    )

    try:
        _validate_scores(
            chunks=chunks,
            response=missing_response,
        )
        raise AssertionError("Expected missing IDs to be rejected")
    except RerankingError:
        pass

    print("PASS: Missing chunk IDs rejected")

    # --------------------------------------------------
    # 8. Invalid scores rejected.
    # --------------------------------------------------
    invalid_response = RerankingResponse.model_construct(
        results=[
            RerankingItem.model_construct(
                chunk_id=1,
                relevance_score=float("nan"),
            )
        ]
    )

    try:
        _validate_scores(
            chunks=[chunks[0]],
            response=invalid_response,
        )
        raise AssertionError("Expected invalid score to be rejected")
    except RerankingError:
        pass

    print("PASS: Non-finite relevance scores rejected")

    # --------------------------------------------------
    # 9. Malformed Gemini response rejected.
    # --------------------------------------------------
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = (
        SimpleNamespace(
            parsed=None,
            text="This is not valid JSON",
        )
    )

    try:
        with patch(
            "app.services.reranking_service._get_gemini_client",
            return_value=fake_client,
        ):
            rerank_chunks(
                query="Revenue",
                chunks=[chunks[0]],
            )

        raise AssertionError("Expected malformed response to fail")

    except RerankingError:
        pass

    print("PASS: Malformed Gemini response rejected")

    # --------------------------------------------------
    # 10. Gemini API failure handled correctly.
    # --------------------------------------------------
    fake_client = MagicMock()
    fake_client.models.generate_content.side_effect = RuntimeError(
        "Simulated Gemini API failure"
    )

    try:
        with patch(
            "app.services.reranking_service._get_gemini_client",
            return_value=fake_client,
        ):
            rerank_chunks(
                query="Revenue",
                chunks=[chunks[0]],
            )

        raise AssertionError("Expected Gemini API failure")

    except RerankingError:
        pass

    print("PASS: Gemini API failures handled")

    # --------------------------------------------------
    # 11. Empty candidate list handled without API call.
    # --------------------------------------------------
    with patch(
        "app.services.reranking_service._get_gemini_client"
    ) as mock_client:
        results = rerank_chunks(
            query="Revenue",
            chunks=[],
        )

    assert results == []
    mock_client.assert_not_called()

    print("PASS: Empty candidate list handled")

    # --------------------------------------------------
    # 12. Invalid query rejected.
    # --------------------------------------------------
    for invalid_query in ["", "   ", None]:
        try:
            rerank_chunks(
                query=invalid_query,
                chunks=chunks,
            )
            raise AssertionError("Expected invalid query rejection")
        except ValueError:
            pass

    print("PASS: Invalid queries rejected")

    # --------------------------------------------------
    # 13. Invalid top_k rejected.
    # --------------------------------------------------
    for invalid_top_k in [0, 51]:
        try:
            rerank_chunks(
                query="Revenue",
                chunks=chunks,
                top_k=invalid_top_k,
            )
            raise AssertionError("Expected invalid top_k rejection")
        except ValueError:
            pass

    print("PASS: Invalid top-K values rejected")

    # --------------------------------------------------
    # 14. Candidate limit enforced.
    # --------------------------------------------------
    too_many_chunks = [
        make_chunk(i, f"Content {i}")
        for i in range(1, 52)
    ]

    try:
        rerank_chunks(
            query="Revenue",
            chunks=too_many_chunks,
        )
        raise AssertionError("Expected candidate limit rejection")
    except ValueError:
        pass

    print("PASS: Maximum candidate limit enforced")

    # --------------------------------------------------
    # 15. Duplicate input chunk IDs rejected.
    # --------------------------------------------------
    duplicate_chunks = [
        make_chunk(1, "First version"),
        make_chunk(1, "Duplicate version"),
    ]

    try:
        rerank_chunks(
            query="Revenue",
            chunks=duplicate_chunks,
        )
        raise AssertionError("Expected duplicate input rejection")
    except ValueError:
        pass

    print("PASS: Duplicate input chunk IDs rejected")

    print("\nALL RERANKING UNIT TESTS PASSED!")


if __name__ == "__main__":
    run_tests()
