from app.services.hybrid_retrieval_service import HybridRetrievedChunk
from app.services.reranking_service import rerank_chunks


def main():
    query = "Explain the company's profitability and EBITDA performance in FY2025."

    chunks = [
        HybridRetrievedChunk(
            chunk_id=101,
            document_id=1,
            document_name="annual_report_2025.pdf",
            page_number=12,
            chunk_index=0,
            content=(
                "The company reported EBITDA of INR 125 crore "
                "during FY2025, representing a 15 percent "
                "increase compared with the previous year."
            ),
            rrf_score=0.032,
            semantic_rank=1,
            keyword_rank=2,
        ),
        HybridRetrievedChunk(
            chunk_id=102,
            document_id=1,
            document_name="annual_report_2025.pdf",
            page_number=14,
            chunk_index=1,
            content=(
                "The company's net profit increased to INR 80 crore "
                "during FY2025 due to improved operating efficiency."
            ),
            rrf_score=0.030,
            semantic_rank=2,
            keyword_rank=1,
        ),
        HybridRetrievedChunk(
            chunk_id=103,
            document_id=1,
            document_name="annual_report_2025.pdf",
            page_number=45,
            chunk_index=2,
            content=(
                "The annual employee sports day was held in February 2025, "
                "with participation from over 500 team members across offices."
            ),
            rrf_score=0.015,
            semantic_rank=None,
            keyword_rank=None,
        ),
    ]

    print("Sending candidate chunks to Gemini for reranking...")
    reranked = rerank_chunks(query=query, chunks=chunks)

    # 1. Check count
    assert len(reranked) == 3, f"Expected 3 chunks, got {len(reranked)}"
    print("PASS: All 3 candidate chunks returned")

    # 2. Check all chunk IDs present
    result_ids = {c.chunk_id for c in reranked}
    assert result_ids == {101, 102, 103}, f"Unexpected chunk IDs: {result_ids}"
    print("PASS: All chunk IDs received scores")

    # 3. Check score ranges [0, 100]
    for c in reranked:
        assert 0.0 <= c.relevance_score <= 100.0, (
            f"Invalid score for chunk {c.chunk_id}: {c.relevance_score}"
        )
    print("PASS: Scores are within valid [0, 100] range")

    # 4. Check ranks are 1, 2, 3
    ranks = [c.rerank_rank for c in reranked]
    assert ranks == [1, 2, 3], f"Unexpected ranks: {ranks}"
    print("PASS: Final ranks are numbered 1, 2, 3")

    # 5. Check metadata preserved
    chunk_map = {c.chunk_id: c for c in chunks}
    for c in reranked:
        original = chunk_map[c.chunk_id]
        assert c.content == original.content
        assert c.document_id == original.document_id
        assert c.document_name == original.document_name
        assert c.page_number == original.page_number
        assert c.chunk_index == original.chunk_index
        assert c.rrf_score == original.rrf_score
    print("PASS: Original content and metadata preserved")

    # 6. Check relevance order: chunks 101 & 102 should be ranked higher than irrelevant chunk 103
    score_by_id = {c.chunk_id: c.relevance_score for c in reranked}
    assert score_by_id[101] > score_by_id[103], (
        f"EBITDA chunk (101) score {score_by_id[101]} should exceed sports chunk (103) score {score_by_id[103]}"
    )
    assert score_by_id[102] > score_by_id[103], (
        f"Profit chunk (102) score {score_by_id[102]} should exceed sports chunk (103) score {score_by_id[103]}"
    )
    assert reranked[-1].chunk_id == 103, (
        f"Expected irrelevant chunk 103 to be ranked last, got rank {reranked[-1].rerank_rank} for chunk {reranked[-1].chunk_id}"
    )
    print("PASS: Relevant financial chunks scored significantly higher than irrelevant chunk")

    print("\n--- Reranking Results ---")
    for c in reranked:
        print(
            f"Rank {c.rerank_rank}: Chunk {c.chunk_id} | "
            f"Score: {c.relevance_score:.1f} | "
            f"RRF: {c.rrf_score:.4f} | "
            f"Page: {c.page_number}"
        )
        print(f"Content: {c.content}\n")

    print("ALL GEMINI RERANKING SMOKE TESTS PASSED!")


if __name__ == "__main__":
    main()

