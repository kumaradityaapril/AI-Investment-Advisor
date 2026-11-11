from types import SimpleNamespace

from app.services.hybrid_retrieval_service import (
    hybrid_search,
    reciprocal_rank_fusion,
)


def make_chunk(chunk_id: int, content: str):
    return SimpleNamespace(
        chunk_id=chunk_id,
        document_id=1,
        document_name="financial-report.pdf",
        page_number=chunk_id,
        chunk_index=chunk_id,
        content=content,
    )


def run_tests():
    # 1. Chunk appearing in both search systems.
    semantic = [
        make_chunk(1, "Revenue was 500 crore."),
        make_chunk(2, "EBITDA was 125 crore."),
    ]
    keyword = [
        make_chunk(2, "EBITDA was 125 crore."),
        make_chunk(3, "Profit was 80 crore."),
    ]
    results = reciprocal_rank_fusion(
        semantic_results=semantic,
        keyword_results=keyword,
    )
    assert len(results) == 3
    assert results[0].chunk_id == 2
    print("PASS: Results from both systems are fused")

    # 2. Rank metadata.
    second_chunk = next(
        item for item in results if item.chunk_id == 2
    )
    assert second_chunk.semantic_rank == 2
    assert second_chunk.keyword_rank == 1
    print("PASS: Original retrieval ranks preserved")

    # 3. RRF score.
    expected_score = (1 / 62) + (1 / 61)
    assert abs(
        second_chunk.rrf_score - expected_score
    ) < 1e-10
    print("PASS: RRF score calculated correctly")

    # 4. Chunk appearing in only one system.
    single_semantic = next(item for item in results if item.chunk_id == 1)
    assert single_semantic.semantic_rank == 1
    assert single_semantic.keyword_rank is None
    assert abs(single_semantic.rrf_score - (1 / 61)) < 1e-10

    single_keyword = next(item for item in results if item.chunk_id == 3)
    assert single_keyword.semantic_rank is None
    assert single_keyword.keyword_rank == 2
    assert abs(single_keyword.rrf_score - (1 / 62)) < 1e-10
    print("PASS: Single-source results supported")

    # 5. Empty retrieval lists handled.
    assert reciprocal_rank_fusion([], []) == []
    assert len(reciprocal_rank_fusion(semantic, [])) == 2
    assert len(reciprocal_rank_fusion([], keyword)) == 2
    print("PASS: Empty retrieval lists handled")

    # 6. Invalid RRF constant rejected.
    try:
        reciprocal_rank_fusion(semantic, keyword, k=0)
        assert False, "Expected ValueError for k=0"
    except ValueError:
        pass

    try:
        reciprocal_rank_fusion(semantic, keyword, k=-5)
        assert False, "Expected ValueError for k=-5"
    except ValueError:
        pass
    print("PASS: Invalid RRF constant rejected")

    # 7. Deterministic tie-breaking verified.
    tie_semantic = [make_chunk(10, "Text 10")]
    tie_keyword = [make_chunk(5, "Text 5")]
    tie_results = reciprocal_rank_fusion(tie_semantic, tie_keyword)
    assert len(tie_results) == 2
    assert tie_results[0].rrf_score == tie_results[1].rrf_score
    assert tie_results[0].chunk_id == 5
    assert tie_results[1].chunk_id == 10
    print("PASS: Deterministic tie-breaking verified")

    # 8. Conflicting chunk metadata rejected.
    conflicting_chunk = SimpleNamespace(
        chunk_id=2,
        document_id=999,
        document_name="other.pdf",
        page_number=99,
        chunk_index=99,
        content="Different content",
    )
    try:
        reciprocal_rank_fusion(semantic, [conflicting_chunk])
        assert False, "Expected ValueError for conflicting chunk metadata"
    except ValueError:
        pass
    print("PASS: Conflicting chunk metadata rejected")

    print("\nALL RRF UNIT TESTS PASSED!")


if __name__ == "__main__":
    run_tests()

