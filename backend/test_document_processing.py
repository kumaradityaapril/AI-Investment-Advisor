from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
import pymupdf
from fastapi import HTTPException
from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Document, User
from app.services.document_processing_service import process_document


def create_test_pdf(path: Path) -> None:
    """Create a small PDF containing known financial text."""
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text(
            (72, 72),
            "Financial Report 2026\n"
            "Revenue: INR 500000\n"
            "Net Profit: INR 75000",
        )
        pdf.save(path)


def main():
    db = SessionLocal()
    test_user = None
    other_user = None
    test_document = None
    missing_file_document = None
    failed_document = None
    created_files = []

    try:
        # Pre-cleanup in case previous run was interrupted
        db.execute(
            text(
                "DELETE FROM users WHERE email IN "
                "('test_doc_proc_user@example.com', 'other_doc_proc_user@example.com')"
            )
        )
        db.commit()

        upload_dir = Path("uploads")
        if not upload_dir.is_absolute():
            upload_dir = Path(__file__).resolve().parent / upload_dir
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Create two isolated test users.
        test_user = User(
            email="test_doc_proc_user@example.com",
            hashed_password=hash_password("Password123!"),
        )
        other_user = User(
            email="other_doc_proc_user@example.com",
            hashed_password=hash_password("Password123!"),
        )
        db.add(test_user)
        db.add(other_user)
        db.commit()
        db.refresh(test_user)
        db.refresh(other_user)

        # 1. Test successful extraction and database persistence
        stored_file_1 = f"test_proc_{uuid4().hex}.pdf"
        stored_path_1 = upload_dir / stored_file_1
        create_test_pdf(stored_path_1)
        created_files.append(stored_path_1)

        test_document = Document(
            user_id=test_user.id,
            original_filename="financial_report.pdf",
            stored_filename=stored_file_1,
            content_type="application/pdf",
            file_size_bytes=stored_path_1.stat().st_size,
            status="uploaded",
        )
        db.add(test_document)
        db.commit()
        db.refresh(test_document)

        processed_doc = process_document(db, test_document.id, test_user.id)
        assert processed_doc.status == "processed"
        assert processed_doc.extracted_text is not None
        assert "Financial Report 2026" in processed_doc.extracted_text
        assert "Revenue: INR 500000" in processed_doc.extracted_text
        print("PASS: PDF extracted and saved in database")

        # 2. Test ownership isolation
        try:
            process_document(db, test_document.id, other_user.id)
            raise AssertionError("Expected 404 for unowned document")
        except HTTPException as exc:
            assert exc.status_code == 404
            print("PASS: Ownership isolation enforced")

        # 3. Test duplicate processing prevented
        try:
            process_document(db, test_document.id, test_user.id)
            raise AssertionError("Expected 409 for already processed document")
        except HTTPException as exc:
            assert exc.status_code == 409
            print("PASS: Duplicate processing prevented")

        # 4. Test missing document handled correctly
        try:
            process_document(db, 999999999, test_user.id)
            raise AssertionError("Expected 404 for non-existent document")
        except HTTPException as exc:
            assert exc.status_code == 404
            print("PASS: Missing document handled correctly")

        # 5. Test missing PDF marks document as failed
        missing_filename = f"missing_{uuid4().hex}.pdf"
        missing_file_document = Document(
            user_id=test_user.id,
            original_filename="missing.pdf",
            stored_filename=missing_filename,
            content_type="application/pdf",
            file_size_bytes=100,
            status="uploaded",
        )
        db.add(missing_file_document)
        db.commit()
        db.refresh(missing_file_document)

        try:
            process_document(db, missing_file_document.id, test_user.id)
            raise AssertionError("Expected extraction error for missing PDF")
        except Exception:
            pass

        db.refresh(missing_file_document)
        assert missing_file_document.status == "failed"
        print("PASS: Missing PDF marks document as failed")

        # 6. Test invalid PDF marks document as failed
        invalid_filename = f"invalid_{uuid4().hex}.pdf"
        invalid_path = upload_dir / invalid_filename
        invalid_path.write_text("This is not a PDF file.", encoding="utf-8")
        created_files.append(invalid_path)

        failed_document = Document(
            user_id=test_user.id,
            original_filename="invalid.pdf",
            stored_filename=invalid_filename,
            content_type="application/pdf",
            file_size_bytes=invalid_path.stat().st_size,
            status="uploaded",
        )
        db.add(failed_document)
        db.commit()
        db.refresh(failed_document)

        try:
            process_document(db, failed_document.id, test_user.id)
            raise AssertionError("Expected extraction error for invalid PDF")
        except Exception:
            pass

        db.refresh(failed_document)
        assert failed_document.status == "failed"
        print("PASS: Invalid PDF marks document as failed")

    finally:
        # Clean up database records (CASCADE will handle documents, but we clean up explicitly)
        if test_document and test_document.id:
            try:
                db.delete(test_document)
            except Exception:
                pass
        if missing_file_document and missing_file_document.id:
            try:
                db.delete(missing_file_document)
            except Exception:
                pass
        if failed_document and failed_document.id:
            try:
                db.delete(failed_document)
            except Exception:
                pass
        if test_user and test_user.id:
            try:
                db.delete(test_user)
            except Exception:
                pass
        if other_user and other_user.id:
            try:
                db.delete(other_user)
            except Exception:
                pass
        try:
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

        # Clean up any created files
        for f in created_files:
            f.unlink(missing_ok=True)

        print("Test cleanup completed.")


if __name__ == "__main__":
    main()

