from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
import pymupdf
from fastapi import HTTPException
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Document, DocumentChunk, User
from app.services.document_indexing_service import index_document
from app.services.embedding_service import EmbeddingGenerationError
from app.services.document_persistence_service import (
    replace_document_chunks as real_replace_document_chunks,
)


def get_upload_directory() -> Path:
    directory = Path(settings.upload_dir)
    if not directory.is_absolute():
        directory = Path(__file__).resolve().parent / directory
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def create_test_pdf(path: Path, revenue: int) -> None:
    """Create a financial PDF with identifiable content."""
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text(
            (72, 72),
            f"Financial Report 2026\nRevenue: INR {revenue}\n",
        )
        pdf.save(path)


def mock_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate deterministic normalized mock embeddings."""
    vec = [0.0] * settings.embedding_dimensions
    vec[0] = 1.0
    return [vec for _ in texts]


def main():
    db = SessionLocal()
    test_user = None
    test_document = None
    created_files = []

    try:
        # Pre-cleanup in case previous run was interrupted
        db.execute(
            text(
                "DELETE FROM users WHERE email = 'test_indexing_safety@example.com'"
            )
        )
        db.commit()

        upload_dir = get_upload_directory()

        # 1. Create a test user
        test_user = User(
            email="test_indexing_safety@example.com",
            hashed_password=hash_password("Password123!"),
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        # 2. Create initial test PDF with revenue = 500000
        stored_filename = f"test_safety_{uuid4().hex}.pdf"
        stored_path = upload_dir / stored_filename
        create_test_pdf(stored_path, 500000)
        created_files.append(stored_path)

        test_document = Document(
            user_id=test_user.id,
            original_filename="safety_report.pdf",
            stored_filename=stored_filename,
            content_type="application/pdf",
            file_size_bytes=stored_path.stat().st_size,
            extracted_text="Financial Report 2026\nRevenue: INR 500000\n",
            status="processed",
            indexing_status="pending",
        )
        db.add(test_document)
        db.commit()
        db.refresh(test_document)

        # Scenario 1: Initial successful indexing
        with patch(
            "app.services.document_indexing_service.generate_document_embeddings",
            side_effect=mock_embeddings,
        ):
            index_document(db, test_document.id, test_user.id)

        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == test_document.id)
            .all()
        )
        assert len(chunks) == 1
        assert "Revenue: INR 500000" in chunks[0].content
        print("PASS: Initial indexed chunk created")

        # Scenario 2: Gemini failure on re-indexing
        # Update PDF content on disk to revenue = 600000
        create_test_pdf(stored_path, 600000)

        try:
            with patch(
                "app.services.document_indexing_service.generate_document_embeddings",
                side_effect=EmbeddingGenerationError("Gemini quota exceeded"),
            ):
                index_document(db, test_document.id, test_user.id)
            raise AssertionError("Expected Gemini failure to raise HTTPException")
        except HTTPException as exc:
            assert exc.status_code == 502

        # Verify previous chunks remain intact
        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == test_document.id)
            .all()
        )
        assert len(chunks) == 1
        assert "Revenue: INR 500000" in chunks[0].content
        print("PASS: Gemini failure preserves previous chunks")

        db.refresh(test_document)
        assert test_document.indexing_status == "failed"
        print("PASS: Failed indexing status recorded")

        # Scenario 3: Database failure rolls back chunk replacement
        def failing_replace(*args, **kwargs):
            raise RuntimeError("Simulated database failure during chunk persistence")

        try:
            with patch(
                "app.services.document_indexing_service.generate_document_embeddings",
                side_effect=mock_embeddings,
            ), patch(
                "app.services.document_indexing_service.replace_document_chunks",
                side_effect=failing_replace,
            ):
                index_document(db, test_document.id, test_user.id)
            raise AssertionError("Expected DB failure to raise HTTPException")
        except HTTPException as exc:
            assert exc.status_code == 500

        print("PASS: Database failure rolls back chunk replacement")

        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == test_document.id)
            .all()
        )
        assert len(chunks) == 1
        assert "Revenue: INR 500000" in chunks[0].content
        print("PASS: Previous chunks remain intact after rollback")

        # Scenario 4: Failed document can be retried successfully
        with patch(
            "app.services.document_indexing_service.generate_document_embeddings",
            side_effect=mock_embeddings,
        ):
            retried_doc = index_document(db, test_document.id, test_user.id)

        assert retried_doc.indexing_status == "indexed"
        print("PASS: Failed document can be retried successfully")

        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == test_document.id)
            .all()
        )
        assert len(chunks) == 1
        assert "Revenue: INR 600000" in chunks[0].content
        print("PASS: Previous chunks replaced after successful retry")

        # Scenario 5: Re-indexing replaces old content without duplicates
        create_test_pdf(stored_path, 700000)

        with patch(
            "app.services.document_indexing_service.generate_document_embeddings",
            side_effect=mock_embeddings,
        ):
            reindexed_doc = index_document(db, test_document.id, test_user.id)

        assert reindexed_doc.indexing_status == "indexed"
        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == test_document.id)
            .all()
        )
        assert len(chunks) == 1
        assert "Revenue: INR 700000" in chunks[0].content
        print("PASS: Re-indexing replaces old content without duplicates")

        print("\nALL INDEXING SAFETY TESTS PASSED!")

    finally:
        # Clean up database records
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

        # Clean up files
        for f in created_files:
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass

        print("Test cleanup completed.")


if __name__ == "__main__":
    main()

