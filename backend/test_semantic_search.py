from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Document, DocumentChunk, User
from app.services.auth_service import register_user
import app.services.retrieval_service as retrieval_service

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
        extracted_text="Sample text content for retrieval test",
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
    original_generate_query_embedding = retrieval_service.generate_query_embedding

    try:
        # Pre-cleanup in case previous run was interrupted
        db.execute(text("DELETE FROM users WHERE email LIKE 'test_semantic_%@example.com'"))
        db.commit()

        # Controlled unit vectors for deterministic cosine distance
        vec_dim = settings.embedding_dimensions
        vec_revenue = [1.0] + [0.0] * (vec_dim - 1)
        vec_esg = [0.0, 1.0] + [0.0] * (vec_dim - 2)
        vec_risks = [0.0, 0.0, 1.0] + [0.0] * (vec_dim - 3)

        # 1. Create test users and documents
        user1_id = create_test_user(db, f"test_semantic_1_{uuid4().hex[:8]}@example.com")
        user2_id = create_test_user(db, f"test_semantic_2_{uuid4().hex[:8]}@example.com")

        # Document 1 for user1 (indexed)
        doc1 = create_test_document(db, user1_id, "annual_report_2026.pdf", indexing_status="indexed")
        chunk0 = create_test_chunk(
            db=db,
            document_id=doc1.id,
            chunk_index=0,
            page_number=1,
            content="The company reported revenue of INR 500000 and net profit of INR 75000.",
            embedding=vec_revenue,
        )
        chunk1 = create_test_chunk(
            db=db,
            document_id=doc1.id,
            chunk_index=1,
            page_number=2,
            content="The company complies with environmental, social, and governance standards.",
            embedding=vec_esg,
        )
        chunk2 = create_test_chunk(
            db=db,
            document_id=doc1.id,
            chunk_index=2,
            page_number=3,
            content="General forward-looking statements involve market risk and volatility.",
            embedding=vec_risks,
        )

        # Unindexed document for user1 (pending)
        doc_unindexed = create_test_document(db, user1_id, "unindexed_doc.pdf", indexing_status="pending")
        create_test_chunk(
            db=db,
            document_id=doc_unindexed.id,
            chunk_index=0,
            page_number=1,
            content="Unindexed document draft revenue information",
            embedding=vec_revenue,
        )

        # Document for user2 (indexed)
        doc_user2 = create_test_document(db, user2_id, "other_user_doc.pdf", indexing_status="indexed")
        create_test_chunk(
            db=db,
            document_id=doc_user2.id,
            chunk_index=0,
            page_number=1,
            content="Other user financial report with revenue of INR 999999.",
            embedding=vec_revenue,
        )

        print("PASS: Test users and documents created")

        # Mock query embedding generation with controlled vector
        def mock_query_embedding(query: str) -> list[float]:
            return vec_revenue

        retrieval_service.generate_query_embedding = mock_query_embedding

        # 2. Test relevant chunk ranked first
        results = retrieval_service.semantic_search(
            db=db,
            query="What was the revenue and profit?",
            user_id=user1_id,
            top_k=5,
        )
        assert len(results) == 3
        assert results[0].chunk_id == chunk0.id
        assert "revenue of INR 500000" in results[0].content
        print("PASS: Relevant chunk ranked first")

        # 3. Document and page metadata preserved
        assert results[0].document_id == doc1.id
        assert results[0].document_name == "annual_report_2026.pdf"
        assert results[0].page_number == 1
        assert results[0].chunk_index == 0
        print("PASS: Document and page metadata preserved")

        # 4. Cosine distance and similarity verified
        assert round(results[0].distance, 4) == 0.0
        assert round(results[0].similarity, 4) == 1.0
        assert round(results[1].distance, 4) == 1.0
        assert round(results[1].similarity, 4) == 0.0
        print("PASS: Cosine distance and similarity verified")

        # 5. Top-K limit verified
        top1_results = retrieval_service.semantic_search(
            db=db,
            query="revenue",
            user_id=user1_id,
            top_k=1,
        )
        assert len(top1_results) == 1
        assert top1_results[0].chunk_id == chunk0.id
        print("PASS: Top-K limit verified")

        # 6. Another user's chunks are excluded
        retrieved_doc_ids = {r.document_id for r in results}
        assert doc_user2.id not in retrieved_doc_ids
        print("PASS: Another user's chunks are excluded")

        # 7. Unindexed document chunks are excluded
        assert doc_unindexed.id not in retrieved_doc_ids
        print("PASS: Unindexed document chunks are excluded")

        # 8. Empty search results handled correctly
        user3_id = create_test_user(db, f"test_semantic_3_{uuid4().hex[:8]}@example.com")
        empty_results = retrieval_service.semantic_search(
            db=db,
            query="revenue",
            user_id=user3_id,
            top_k=5,
        )
        assert empty_results == []
        print("PASS: Empty search results handled correctly")

        # 9. Empty query rejected
        try:
            retrieval_service.semantic_search(db=db, query="", user_id=user1_id)
            raise AssertionError("Expected ValueError for empty query")
        except ValueError:
            pass

        try:
            retrieval_service.semantic_search(db=db, query="   ", user_id=user1_id)
            raise AssertionError("Expected ValueError for whitespace query")
        except ValueError:
            pass

        print("PASS: Empty query rejected")

        # 10. Invalid top_k rejected
        try:
            retrieval_service.semantic_search(db=db, query="revenue", user_id=user1_id, top_k=0)
            raise AssertionError("Expected ValueError for top_k=0")
        except ValueError:
            pass

        try:
            retrieval_service.semantic_search(db=db, query="revenue", user_id=user1_id, top_k=51)
            raise AssertionError("Expected ValueError for top_k=51")
        except ValueError:
            pass

        print("PASS: Invalid top_k rejected")

        print("\nALL SEMANTIC SEARCH TESTS PASSED!")

    finally:
        retrieval_service.generate_query_embedding = original_generate_query_embedding

        # Clean up created test users (cascade will remove documents and chunks)
        if created_user_ids:
            try:
                for uid in created_user_ids:
                    u = db.get(User, uid)
                    if u:
                        db.delete(u)
                db.commit()
            except Exception:
                db.rollback()

        try:
            db.close()
        except Exception:
            pass

        print("Test cleanup completed.")


if __name__ == "__main__":
    main()

