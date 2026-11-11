
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Document, DocumentChunk, User
from app.services.auth_service import register_user

import app.services.retrieval_service as retrieval_service
from app.services.hybrid_retrieval_service import hybrid_search


created_user_ids: list[int] = []


def create_test_user(db: Session, email: str) -> int:
    user = register_user(
        db,
        email,
        "TestPassword123!",
    )
    created_user_ids.append(user.id)
    return user.id


def create_test_document(
    db: Session,
    user_id: int,
    filename: str,
    indexing_status: str = "indexed",
    status: str = "processed",
) -> Document:
    document = Document(
        user_id=user_id,
        original_filename=filename,
        stored_filename=f"{uuid4().hex}.pdf",
        content_type="application/pdf",
        file_size_bytes=1024,
        extracted_text="Hybrid retrieval integration test document",
        status=status,
        indexing_status=indexing_status,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def create_test_chunk(
    db: Session,
    document_id: int,
    chunk_index: int,
    page_number: int,
    content: str,
    embedding: list[float],
) -> DocumentChunk:
    chunk = DocumentChunk(
        document_id=document_id,
        chunk_index=chunk_index,
        page_number=page_number,
        content=content,
        embedding=embedding,
    )

    db.add(chunk)
    db.commit()
    db.refresh(chunk)

    return chunk


def main():
    db = SessionLocal()

    original_generate_query_embedding = (
        retrieval_service.generate_query_embedding
    )

    prefix = f"hybrid-{uuid4().hex[:10]}"

    try:
        # 1. Pre-cleanup in case an earlier test was interrupted.
        db.execute(
            text("DELETE FROM users WHERE email LIKE :pattern"),
            {"pattern": f"{prefix}-%@example.com"},
        )
        db.commit()

        # 2. Create controlled embeddings.
        vec_dim = settings.embedding_dimensions

        vec_revenue = [1.0] + [0.0] * (vec_dim - 1)

        vec_ebitda = (
            [0.8, 0.6] + [0.0] * (vec_dim - 2)
        )

        vec_risk = (
            [0.0, 1.0] + [0.0] * (vec_dim - 2)
        )

        # 3. Create two users.
        user1_id = create_test_user(
            db,
            f"{prefix}-user1@example.com",
        )

        user2_id = create_test_user(
            db,
            f"{prefix}-user2@example.com",
        )

        # 4. Create indexed document for user 1.
        document = create_test_document(
            db,
            user1_id,
            "hybrid_financial_report.pdf",
        )

        chunk_revenue = create_test_chunk(
            db,
            document.id,
            0,
            1,
            (
                "The company reported annual revenue "
                "of INR 500 crore during FY2025."
            ),
            vec_revenue,
        )

        chunk_ebitda = create_test_chunk(
            db,
            document.id,
            1,
            2,
            (
                "The company reported EBITDA of "
                "INR 125 crore during FY2025."
            ),
            vec_ebitda,
        )

        chunk_risk = create_test_chunk(
            db,
            document.id,
            2,
            3,
            (
                "The company faces market risk "
                "and financial volatility."
            ),
            vec_risk,
        )

        # 5. Create an unindexed document for user 1.
        unindexed_document = create_test_document(
            db,
            user1_id,
            "unindexed_financial_report.pdf",
            indexing_status="pending",
        )

        create_test_chunk(
            db,
            unindexed_document.id,
            0,
            1,
            "EBITDA revenue FY2025 unindexed information.",
            vec_revenue,
        )

        # 6. Create an indexed document for user 2.
        other_user_document = create_test_document(
            db,
            user2_id,
            "other_user_report.pdf",
        )

        create_test_chunk(
            db,
            other_user_document.id,
            0,
            1,
            "EBITDA revenue FY2025 belonging to another user.",
            vec_revenue,
        )

        print("PASS: Test users and documents created")

        # 7. Mock only query embedding generation.
        # PostgreSQL semantic and keyword searches remain real.
        def mock_query_embedding(query: str) -> list[float]:
            return vec_revenue

        retrieval_service.generate_query_embedding = (
            mock_query_embedding
        )

        # 8. Execute actual hybrid search.
        results = hybrid_search(
            db=db,
            query="EBITDA OR revenue",
            user_id=user1_id,
            top_k=5,
            candidate_k=20,
            rrf_k=60,
        )

        result_ids = {item.chunk_id for item in results}

        # 9. Both retrieval systems contribute to the results.
        assert chunk_revenue.id in result_ids
        assert chunk_ebitda.id in result_ids

        print("PASS: Semantic and keyword results fused")

        # 10. Verify original ranks are preserved.
        revenue_result = next(
            item for item in results
            if item.chunk_id == chunk_revenue.id
        )

        ebitda_result = next(
            item for item in results
            if item.chunk_id == chunk_ebitda.id
        )

        assert revenue_result.semantic_rank is not None
        assert ebitda_result.keyword_rank is not None

        assert revenue_result.semantic_rank >= 1
        assert ebitda_result.keyword_rank >= 1

        print("PASS: Semantic and keyword ranks preserved")

        # 11. Verify RRF scores.
        for item in results:
            expected_score = 0.0

            if item.semantic_rank is not None:
                expected_score += 1 / (60 + item.semantic_rank)

            if item.keyword_rank is not None:
                expected_score += 1 / (60 + item.keyword_rank)

            assert abs(item.rrf_score - expected_score) < 1e-10

        print("PASS: RRF scores match original retrieval ranks")

        # 12. Verify final results are sorted by RRF score.
        scores = [item.rrf_score for item in results]

        assert scores == sorted(scores, reverse=True)

        print("PASS: Results sorted by RRF score")

        # 13. Verify document and page metadata.
        assert revenue_result.document_id == document.id
        assert revenue_result.document_name == (
            "hybrid_financial_report.pdf"
        )
        assert revenue_result.page_number == 1
        assert revenue_result.chunk_index == 0

        print("PASS: Document and page metadata preserved")

        # 14. Verify user isolation.
        retrieved_document_ids = {
            item.document_id for item in results
        }

        assert other_user_document.id not in retrieved_document_ids

        print("PASS: Other user's documents excluded")

        # 15. Verify unindexed documents are excluded.
        assert unindexed_document.id not in retrieved_document_ids

        print("PASS: Unindexed documents excluded")

        # 16. Verify top-K limit.
        top1_results = hybrid_search(
            db=db,
            query="EBITDA OR revenue",
            user_id=user1_id,
            top_k=1,
            candidate_k=20,
        )

        assert len(top1_results) == 1

        print("PASS: Final top-K limit verified")

        # 17. Verify empty results.
        empty_user_id = create_test_user(
            db,
            f"{prefix}-empty@example.com",
        )

        empty_results = hybrid_search(
            db=db,
            query="EBITDA OR revenue",
            user_id=empty_user_id,
            top_k=5,
            candidate_k=20,
        )

        assert empty_results == []

        print("PASS: Empty hybrid results handled")

        # 18. Verify invalid query.
        try:
            hybrid_search(
                db=db,
                query="   ",
                user_id=user1_id,
            )
            raise AssertionError("Expected ValueError for empty query")
        except ValueError:
            pass

        print("PASS: Empty query rejected")

        # 19. Verify invalid top-K.
        try:
            hybrid_search(
                db=db,
                query="revenue",
                user_id=user1_id,
                top_k=0,
            )
            raise AssertionError("Expected ValueError for top_k=0")
        except ValueError:
            pass

        print("PASS: Invalid top-K rejected")

        print("\nALL HYBRID SEARCH INTEGRATION TESTS PASSED!")

    finally:
        # Restore the real embedding function.
        retrieval_service.generate_query_embedding = (
            original_generate_query_embedding
        )

        # Delete all test users.
        try:
            for user_id in created_user_ids:
                user = db.get(User, user_id)

                if user:
                    db.delete(user)

            db.commit()

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

        print("Test cleanup completed.")


if __name__ == "__main__":
    main()

