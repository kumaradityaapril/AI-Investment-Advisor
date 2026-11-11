import math
from pathlib import Path
from uuid import uuid4
import pymupdf
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Document, DocumentChunk, User
from app.core.security import hash_password
from app.services.document_indexing_service import index_document


def get_upload_directory() -> Path:
    directory = Path(settings.upload_dir)
    if not directory.is_absolute():
        directory = Path(__file__).resolve().parent / directory
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def create_test_pdf(path: Path) -> None:
    """Create a two-page financial PDF with known content."""
    with pymupdf.open() as pdf:
        page1 = pdf.new_page()
        page1.insert_text(
            (72, 72),
            "Annual Financial Report 2026\n"
            "Company: Test Financial Corporation\n"
            "Revenue: INR 500000\n"
            "Net Profit: INR 75000",
        )
        page2 = pdf.new_page()
        page2.insert_text(
            (72, 72),
            "Balance Sheet Highlights\n"
            "Total Assets: INR 1200000\n"
            "Total Liabilities: INR 450000\n"
            "Cash and Equivalents: INR 350000",
        )
        pdf.save(path)


def main():
    db = SessionLocal()
    test_user = None
    test_document = None
    created_files = []

    try:
        # Pre-cleanup in case previous run was interrupted
        db.execute(
            text(
                "DELETE FROM users WHERE email = 'test_indexing_user@example.com'"
            )
        )
        db.commit()

        upload_dir = get_upload_directory()

        # 1. Create a test user
        test_user = User(
            email="test_indexing_user@example.com",
            hashed_password=hash_password("Password123!"),
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        # 2. Create a 2-page test PDF
        stored_filename = f"test_index_{uuid4().hex}.pdf"
        stored_path = upload_dir / stored_filename
        create_test_pdf(stored_path)
        created_files.append(stored_path)

        # 3. Create a processed test document
        test_document = Document(
            user_id=test_user.id,
            original_filename="annual_report_2026.pdf",
            stored_filename=stored_filename,
            content_type="application/pdf",
            file_size_bytes=stored_path.stat().st_size,
            extracted_text=(
                "Annual Financial Report 2026\n"
                "Company: Test Financial Corporation\n"
                "Revenue: INR 500000\n"
                "Net Profit: INR 75000\n"
                "Balance Sheet Highlights\n"
                "Total Assets: INR 1200000\n"
                "Total Liabilities: INR 450000\n"
                "Cash and Equivalents: INR 350000"
            ),
            status="processed",
            indexing_status="pending",
        )
        db.add(test_document)
        db.commit()
        db.refresh(test_document)
        print(f"Test document created: {test_document.id}")

        # 4. Perform real document indexing
        indexed_doc = index_document(
            db=db,
            document_id=test_document.id,
            user_id=test_user.id,
        )
        assert indexed_doc.indexing_status == "indexed"
        assert indexed_doc.indexed_at is not None
        print("PASS: Document indexing completed successfully")

        # 5. Query and verify persisted chunks
        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == test_document.id)
            .order_by(DocumentChunk.chunk_index)
            .all()
        )
        assert len(chunks) == 2
        print("PASS: 2 chunks persisted")

        # Verify chunk indexes and page numbers
        assert chunks[0].chunk_index == 0 and chunks[0].page_number == 1
        assert chunks[1].chunk_index == 1 and chunks[1].page_number == 2
        print("PASS: Chunk indexes and page numbers preserved")

        # Verify content
        assert "Revenue: INR 500000" in chunks[0].content
        assert "Balance Sheet Highlights" in chunks[1].content
        print("PASS: Financial text persisted correctly")

        # Verify embedding dimensions
        for chunk in chunks:
            assert len(chunk.embedding) == settings.embedding_dimensions
        print("PASS: Embedding dimensions verified")

        # Verify embedding normalization
        for chunk in chunks:
            norm = math.sqrt(sum(v * v for v in chunk.embedding))
            assert math.isclose(norm, 1.0, rel_tol=1e-5)
        print("PASS: Embedding normalization verified")

        # Verify document processing and indexing statuses
        db.refresh(test_document)
        assert test_document.status == "processed"
        assert test_document.indexing_status == "indexed"
        print("PASS: Document processing and indexing statuses verified")

        print("\nREAL DOCUMENT INDEXING TEST PASSED!")

    finally:
        # Cleanup test records
        if test_document and test_document.id:
            try:
                db.delete(test_document)
            except Exception:
                pass
        if test_user and test_user.id:
            try:
                db.delete(test_user)
            except Exception:
                pass
        try:
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

        # Cleanup created test files
        for f in created_files:
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass

        print("Test cleanup completed.")


if __name__ == "__main__":
    main()

