from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from uuid import uuid4
import pymupdf
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Document, DocumentChunk, User
from app.services.document_indexing_service import index_document
import app.services.document_indexing_service as indexing_module


def get_upload_directory() -> Path:
    directory = Path(settings.upload_dir)
    if not directory.is_absolute():
        directory = Path(__file__).resolve().parent / directory
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def create_test_pdf(path: Path) -> None:
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text(
            (72, 72),
            "Concurrency Test Financial Report\n"
            "Revenue: INR 600000\n"
            "Net Profit: INR 90000",
        )
        pdf.save(path)


def fake_embeddings(texts: list[str]) -> list[list[float]]:
    return [[1.0] + [0.0] * 767 for _ in texts]


def main():
    setup_db = SessionLocal()
    test_user = None
    other_user = None
    test_document = None
    created_files = []

    allow_embedding_to_finish = Event()
    original_embedding_function = indexing_module.generate_document_embeddings

    try:
        # Pre-cleanup in case previous run was interrupted
        setup_db.execute(
            text(
                "DELETE FROM users WHERE email IN "
                "('test_concurrency_user@example.com', 'other_concurrency_user@example.com')"
            )
        )
        setup_db.commit()

        upload_dir = get_upload_directory()

        # 1. Create two users
        test_user = User(
            email="test_concurrency_user@example.com",
            hashed_password=hash_password("Password123!"),
        )
        other_user = User(
            email="other_concurrency_user@example.com",
            hashed_password=hash_password("Password123!"),
        )
        setup_db.add(test_user)
        setup_db.add(other_user)
        setup_db.commit()
        setup_db.refresh(test_user)
        setup_db.refresh(other_user)

        # 2. Create test document
        stored_filename = f"test_concurrency_{uuid4().hex}.pdf"
        stored_path = upload_dir / stored_filename
        create_test_pdf(stored_path)
        created_files.append(stored_path)

        test_document = Document(
            user_id=test_user.id,
            original_filename="concurrency_report.pdf",
            stored_filename=stored_filename,
            content_type="application/pdf",
            file_size_bytes=stored_path.stat().st_size,
            extracted_text="Concurrency Test Financial Report\nRevenue: INR 600000\nNet Profit: INR 90000",
            status="processed",
            indexing_status="pending",
        )
        setup_db.add(test_document)
        setup_db.commit()
        setup_db.refresh(test_document)
        print(f"Test document created: {test_document.id}")

        # 3. Test ownership isolation
        other_db = SessionLocal()
        try:
            try:
                index_document(other_db, test_document.id, other_user.id)
                raise AssertionError("Expected 404 for unowned document")
            except HTTPException as exc:
                assert exc.status_code == 404
                print("PASS: Another user cannot index this document")
        finally:
            other_db.close()

        # 4. Test concurrent indexing requests
        embedding_started = Event()

        def blocking_embeddings(texts: list[str]) -> list[list[float]]:
            embedding_started.set()
            if not allow_embedding_to_finish.wait(timeout=10):
                raise TimeoutError("allow_embedding_to_finish was not set in time")
            return fake_embeddings(texts)

        indexing_module.generate_document_embeddings = blocking_embeddings

        task1_exception = None

        def run_task1():
            nonlocal task1_exception
            db1 = SessionLocal()
            try:
                index_document(db1, test_document.id, test_user.id)
            except Exception as e:
                task1_exception = e
            finally:
                db1.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(run_task1)

            # Wait until task 1 claims the document and enters embedding generation
            if not embedding_started.wait(timeout=5):
                raise TimeoutError("Task 1 did not reach embedding generation in time")

            # Simultaneous indexing attempt by the same user with a separate session
            db2 = SessionLocal()
            try:
                index_document(db2, test_document.id, test_user.id)
                raise AssertionError("Expected 409 for concurrent indexing attempt")
            except HTTPException as exc:
                assert exc.status_code == 409
                print("PASS: Concurrent indexing request rejected with HTTP 409")
            finally:
                db2.close()

            # Allow task 1 to finish
            allow_embedding_to_finish.set()
            future1.result(timeout=5)

        if task1_exception is not None:
            raise task1_exception

        # 5. Verify chunk persistence
        chunks = (
            setup_db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == test_document.id)
            .all()
        )
        assert len(chunks) == 1
        print("PASS: Only one indexing operation persisted chunks")

        print("\nALL CONCURRENCY AND OWNERSHIP TESTS PASSED!")

    finally:
        allow_embedding_to_finish.set()
        indexing_module.generate_document_embeddings = (
            original_embedding_function
        )

        # Clean up database records
        if test_document and test_document.id:
            try:
                setup_db.delete(test_document)
            except Exception:
                pass
        if test_user and test_user.id:
            try:
                setup_db.delete(test_user)
            except Exception:
                pass
        if other_user and other_user.id:
            try:
                setup_db.delete(other_user)
            except Exception:
                pass
        try:
            setup_db.commit()
        except Exception:
            setup_db.rollback()
        finally:
            setup_db.close()

        # Clean up files
        for f in created_files:
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass

        print("Test cleanup completed.")


if __name__ == "__main__":
    main()

