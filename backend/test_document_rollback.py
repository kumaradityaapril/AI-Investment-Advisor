from io import BytesIO
from unittest.mock import MagicMock
from fastapi import UploadFile
from starlette.datastructures import Headers
from app.core.config import settings
from app.services.document_service import create_document, _upload_directory


def test_database_failure_cleanup():
    # A minimal PDF-like payload for testing the upload service.
    pdf_content = b"%PDF-1.4\nTest document content\n%%EOF"
    file = UploadFile(
        filename="rollback-test.pdf",
        file=BytesIO(pdf_content),
        headers=Headers({"content-type": "application/pdf"}),
    )

    # Mock the database session without modifying PostgreSQL.
    db = MagicMock()
    db.commit.side_effect = RuntimeError(
        "Simulated database commit failure"
    )

    upload_dir = _upload_directory()
    before_files = {
        p.name for p in upload_dir.iterdir() if p.is_file()
    }

    commit_failed = False
    try:
        create_document(
            db=db,
            user_id=1,
            file=file,
        )
    except RuntimeError as e:
        if "Simulated database commit failure" in str(e):
            commit_failed = True
            print("PASS: Database commit failure simulated")
        else:
            raise

    assert commit_failed, "Expected RuntimeError was not raised"

    # Check db.rollback() was called
    db.rollback.assert_called_once()
    print("PASS: Database rollback called")

    after_files = {
        p.name for p in upload_dir.iterdir() if p.is_file()
    }

    # Verify no new file remains
    new_files = after_files - before_files
    assert len(new_files) == 0, f"Found lingering files: {new_files}"
    print("PASS: Uploaded file cleaned up")

    # Verify existing files are preserved
    assert before_files.issubset(after_files), "Existing files were deleted"
    print("PASS: Existing uploaded files preserved")


if __name__ == "__main__":
    test_database_failure_cleanup()
