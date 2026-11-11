from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Document, DocumentChunk, User
from app.services.auth_service import register_user
from app.services.keyword_retrieval_service import keyword_search

created_user_id: int | None = None


def run_tests():
    global created_user_id
    db: Session = SessionLocal()
    try:
        # Pre-cleanup in case of previous interrupted run
        db.execute(text("DELETE FROM users WHERE email LIKE 'keyword-%@example.com'"))
        db.commit()

        suffix = uuid4().hex[:10]
        user = register_user(
            db,
            f"keyword-{suffix}@example.com",
            "TestPassword123!",
        )
        created_user_id = user.id

        document = Document(
            user_id=user.id,
            original_filename="financial-report.pdf",
            stored_filename=f"{uuid4().hex}.pdf",
            content_type="application/pdf",
            file_size_bytes=2048,
            extracted_text="Sample text content for keyword retrieval",
            status="processed",
            indexing_status="indexed",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        dummy_embedding = [0.0] * settings.embedding_dimensions

        # Chunk 0: EBITDA and FY2025 and revenue without expenses
        c0 = DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            page_number=1,
            content="The company reported EBITDA of INR 125 crore for FY2025 with strong revenue growth.",
            embedding=dummy_embedding,
        )
        # Chunk 1: Exact phrase "net profit" and FY2024
        c1 = DocumentChunk(
            document_id=document.id,
            chunk_index=1,
            page_number=2,
            content="In FY2024, net profit margin expanded significantly due to operational efficiency.",
            embedding=dummy_embedding,
        )
        # Chunk 2: Revenue with expenses
        c2 = DocumentChunk(
            document_id=document.id,
            chunk_index=2,
            page_number=3,
            content="Annual revenue was accompanied by rising operating expenses and overhead costs.",
            embedding=dummy_embedding,
        )
        # Chunk 3: Valuation metrics
        c3 = DocumentChunk(
            document_id=document.id,
            chunk_index=3,
            page_number=4,
            content="Market capitalization and P/E ratio on the NSE exchange remained favorable.",
            embedding=dummy_embedding,
        )

        db.add_all([c0, c1, c2, c3])
        db.commit()
        print("PASS: Financial test document created")

        # 1. Exact financial terminology retrieved
        results_ebitda = keyword_search(db, "EBITDA", user.id)
        assert len(results_ebitda) >= 1
        assert "EBITDA" in results_ebitda[0].content
        print("PASS: Exact financial terminology retrieved")

        # 2. Financial year retrieval verified
        results_fy = keyword_search(db, "FY2025", user.id)
        assert len(results_fy) >= 1
        assert "FY2025" in results_fy[0].content
        print("PASS: Financial year retrieval verified")

        # 3. Exact phrase search verified
        results_phrase = keyword_search(db, '"net profit"', user.id)
        assert len(results_phrase) >= 1
        assert "net profit" in results_phrase[0].content.lower()
        print("PASS: Exact phrase search verified")

        # 4. OR search verified
        results_or = keyword_search(db, "EBITDA OR expenses", user.id)
        assert len(results_or) >= 2
        all_or_content = " ".join([r.content for r in results_or])
        assert "EBITDA" in all_or_content and "expenses" in all_or_content
        print("PASS: OR search verified")

        # 5. Exclusion search verified
        results_excl = keyword_search(db, "revenue -expenses", user.id)
        assert len(results_excl) >= 1
        for r in results_excl:
            assert "expenses" not in r.content.lower()
            assert "revenue" in r.content.lower()
        print("PASS: Exclusion search verified")

        # 6. Page metadata and ranking verified
        assert results_ebitda[0].document_id == document.id
        assert results_ebitda[0].document_name == "financial-report.pdf"
        assert results_ebitda[0].page_number == 1
        assert results_ebitda[0].chunk_index == 0
        assert results_ebitda[0].rank_score > 0.0
        print("PASS: Page metadata and ranking verified")

        # 7. Top-K limit verified
        results_top1 = keyword_search(db, "revenue", user.id, top_k=1)
        assert len(results_top1) == 1
        print("PASS: Top-K limit verified")

        # 8. Empty query rejected
        try:
            keyword_search(db, "", user.id)
            raise AssertionError("Expected ValueError for empty query")
        except ValueError:
            pass

        try:
            keyword_search(db, "   ", user.id)
            raise AssertionError("Expected ValueError for whitespace query")
        except ValueError:
            pass

        print("PASS: Empty query rejected")

        # 9. No-match query handled correctly
        results_nomatch = keyword_search(db, "nonexistentfinancialmetric999", user.id)
        assert results_nomatch == []
        print("PASS: No-match query handled correctly")

        print("\nALL KEYWORD SEARCH TESTS PASSED!")

    finally:
        if created_user_id:
            try:
                user_rec = db.get(User, created_user_id)
                if user_rec:
                    db.delete(user_rec)
                db.commit()
            except Exception:
                db.rollback()

        try:
            db.close()
        except Exception:
            pass

        print("Test cleanup completed.")


if __name__ == "__main__":
    run_tests()

