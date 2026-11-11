
from uuid import uuid4
import math

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Document, DocumentChunk, User
from app.services.auth_service import register_user
from app.services.embedding_service import generate_document_embeddings
from app.services.retrieval_pipeline_service import retrieve_and_rerank


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
) -> Document:
    document = Document(
        user_id=user_id,
        original_filename=filename,
        stored_filename=f"{uuid4().hex}.pdf",
        content_type="application/pdf",
        file_size_bytes=2048,
        extracted_text="End-to-end financial retrieval integration test.",
        status="processed",
        indexing_status=indexing_status,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def main():
    db: Session = SessionLocal()
    prefix = f"pipeline-{uuid4().hex[:10]}"

    try:
        # 1. Pre-cleanup from an interrupted run.
        db.execute(
            text("DELETE FROM users WHERE email LIKE :pattern"),
            {"pattern": f"{prefix}-%@example.com"},
        )
        db.commit()

        # 2. Create two users.
        user1_id = create_test_user(
            db,
            f"{prefix}-user1@example.com",
        )

        user2_id = create_test_user(
            db,
            f"{prefix}-user2@example.com",
        )

        # 3. Create an indexed document for user 1.
        document = create_test_document(
            db,
            user1_id,
            "annual_financial_report_2025.pdf",
        )

        # Financial chunks and one unrelated distractor.
        contents = [
            (
                "The company reported EBITDA of INR 125 crore "
                "during FY2025, representing a 15 percent increase "
                "compared with the previous financial year."
            ),
            (
                "The company's net profit increased to INR 80 crore "
                "during FY2025 due to improved operating efficiency."
            ),
            (
                "The company reported annual revenue of INR 500 crore "
                "during FY2025, compared with INR 420 crore in FY2024."
            ),
            (
                "The company faces market risk due to changing "
                "interest rates, inflation, and economic uncertainty."
            ),
            (
                "The annual employee sports day was held in February "
                "2025, with participation from over 500 team members."
            ),
        ]

        # 4. Generate REAL Gemini document embeddings.
        embeddings = generate_document_embeddings(contents)

        assert len(embeddings) == len(contents)

        for embedding in embeddings:
            assert len(embedding) == settings.embedding_dimensions
            assert all(math.isfinite(value) for value in embedding)

        print("PASS: Real Gemini document embeddings generated")

        # 5. Store chunks in PostgreSQL.
        test_chunks = []

        for index, (content, embedding) in enumerate(
            zip(contents, embeddings)
        ):
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                page_number=index + 1,
                content=content,
                embedding=embedding,
            )

            db.add(chunk)
            test_chunks.append(chunk)

        db.commit()

        for chunk in test_chunks:
            db.refresh(chunk)

        print("PASS: Financial chunks persisted in PostgreSQL")

        # 6. Create another user's indexed document.
        other_document = create_test_document(
            db,
            user2_id,
            "another_users_financial_report.pdf",
        )

        other_content = (
            "The company reported EBITDA of INR 999 crore "
            "during FY2025."
        )

        other_embedding = generate_document_embeddings(
            [other_content]
        )[0]

        other_chunk = DocumentChunk(
            document_id=other_document.id,
            chunk_index=0,
            page_number=1,
            content=other_content,
            embedding=other_embedding,
        )

        db.add(other_chunk)
        db.commit()

        print("PASS: Separate user's financial document created")

        # 7. Create an unindexed document for user 1.
        unindexed_document = create_test_document(
            db,
            user1_id,
            "unindexed_report.pdf",
            indexing_status="pending",
        )

        unindexed_content = (
            "EBITDA net profit revenue FY2025 unindexed information."
        )

        unindexed_embedding = generate_document_embeddings(
            [unindexed_content]
        )[0]

        unindexed_chunk = DocumentChunk(
            document_id=unindexed_document.id,
            chunk_index=0,
            page_number=1,
            content=unindexed_content,
            embedding=unindexed_embedding,
        )

        db.add(unindexed_chunk)
        db.commit()

        print("PASS: Unindexed document created")

        # 8. Run the COMPLETE real retrieval pipeline.
        query = (
            "Explain the company's profitability, "
            "EBITDA and net profit performance in FY2025."
        )

        print("\nRunning hybrid retrieval and Gemini reranking...")

        results = retrieve_and_rerank(
            db=db,
            query=query,
            user_id=user1_id,
            top_k=3,
            candidate_k=5,
            rrf_k=60,
        )

        # 9. Verify final results exist.
        assert len(results) > 0
        assert len(results) <= 3

        print("PASS: End-to-end retrieval pipeline returned results")

        # 10. Verify reranking scores and final ranks.
        assert [item.rerank_rank for item in results] == list(
            range(1, len(results) + 1)
        )

        for item in results:
            assert math.isfinite(item.relevance_score)
            assert 0 <= item.relevance_score <= 100
            assert math.isfinite(item.rrf_score)

        print("PASS: Gemini relevance scores and ranks validated")

        # 11. Verify final results are sorted correctly.
        sort_keys = [
            (
                -item.relevance_score,
                -item.rrf_score,
                item.chunk_id,
            )
            for item in results
        ]

        assert sort_keys == sorted(sort_keys)

        print("PASS: Final reranking order verified")

        # 12. Verify metadata and original evidence.
        expected_content = {chunk.id: chunk.content for chunk in test_chunks}

        for item in results:
            assert item.document_id == document.id
            assert item.document_name == (
                "annual_financial_report_2025.pdf"
            )
            assert item.content == expected_content[item.chunk_id]
            assert item.page_number in range(1, 6)

        print("PASS: Original document content and metadata preserved")

        # 13. Verify ownership isolation.
        retrieved_document_ids = {
            item.document_id for item in results
        }

        assert other_document.id not in retrieved_document_ids

        print("PASS: Other user's documents excluded")

        # 14. Verify unindexed documents are excluded.
        assert unindexed_document.id not in retrieved_document_ids

        print("PASS: Unindexed documents excluded")

        # 15. Verify empty user retrieval.
        empty_user_id = create_test_user(
            db,
            f"{prefix}-empty@example.com",
        )

        empty_results = retrieve_and_rerank(
            db=db,
            query=query,
            user_id=empty_user_id,
            top_k=3,
            candidate_k=5,
        )

        assert empty_results == []

        print("PASS: Empty retrieval handled without reranking")

        # 16. Print final results for manual inspection.
        print("\n--- END-TO-END RETRIEVAL RESULTS ---")

        for item in results:
            print(
                f"\nRank: {item.rerank_rank}"
                f"\nChunk ID: {item.chunk_id}"
                f"\nRelevance: {item.relevance_score}/100"
                f"\nRRF score: {item.rrf_score:.6f}"
                f"\nDocument: {item.document_name}"
                f"\nPage: {item.page_number}"
                f"\nContent: {item.content}"
            )

        print("\nALL END-TO-END RETRIEVAL TESTS PASSED!")

    finally:
        # Remove only the test users created in this run.
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
