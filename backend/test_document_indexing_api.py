from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
import pymupdf as fitz
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.main import app
from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Document, DocumentChunk, User
from app.services import document_indexing_service
from app.services.embedding_service import EmbeddingGenerationError

client = TestClient(app)
created_user_ids: list[int] = []
created_file_paths: list[Path] = []


def register_and_login(email: str) -> tuple[int, str]:
    """Create a real user and return their ID and JWT token."""
    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )
    assert register_response.status_code == 201, (
        f"Registration failed: {register_response.text}"
    )
    user_id = register_response.json()["id"]
    created_user_ids.append(user_id)

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )
    assert login_response.status_code == 200, (
        f"Login failed: {login_response.text}"
    )
    token = login_response.json()["access_token"]
    return user_id, token


def get_upload_directory() -> Path:
    directory = Path(settings.upload_dir)
    if not directory.is_absolute():
        directory = Path(__file__).resolve().parent / directory
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def create_test_pdf(path: Path, content: str = "Financial Report 2026\nRevenue: INR 500000") -> None:
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), content)
        pdf.save(path)


def fake_embeddings(texts: list[str]) -> list[list[float]]:
    return [[1.0] + [0.0] * 767 for _ in texts]


def main():
    db = SessionLocal()
    upload_dir = get_upload_directory()

    try:
        # Pre-cleanup if interrupted previously
        db.execute(text("DELETE FROM users WHERE email LIKE 'test_indexing_api_%@example.com'"))
        db.commit()

        print("Creating authenticated test users...")
        email1 = f"test_indexing_api_1_{uuid4().hex[:8]}@example.com"
        email2 = f"test_indexing_api_2_{uuid4().hex[:8]}@example.com"
        user1_id, token1 = register_and_login(email1)
        user2_id, token2 = register_and_login(email2)
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        print("PASS: Test users registered and authenticated")

        # 1. Valid processed document
        file_valid = upload_dir / f"test_api_valid_{uuid4().hex}.pdf"
        create_test_pdf(file_valid, "Valid Report\nRevenue: INR 500000")
        created_file_paths.append(file_valid)

        doc_valid = Document(
            user_id=user1_id,
            original_filename="valid_report.pdf",
            stored_filename=file_valid.name,
            content_type="application/pdf",
            file_size_bytes=file_valid.stat().st_size,
            extracted_text="Valid Report\nRevenue: INR 500000",
            status="processed",
            indexing_status="pending",
        )
        db.add(doc_valid)

        # 2. Unprocessed document
        file_unproc = upload_dir / f"test_api_unproc_{uuid4().hex}.pdf"
        create_test_pdf(file_unproc, "Unprocessed Report")
        created_file_paths.append(file_unproc)

        doc_unprocessed = Document(
            user_id=user1_id,
            original_filename="unprocessed_report.pdf",
            stored_filename=file_unproc.name,
            content_type="application/pdf",
            file_size_bytes=file_unproc.stat().st_size,
            status="uploaded",
            indexing_status="pending",
        )
        db.add(doc_unprocessed)

        # 3. Already-indexing document
        file_indexing = upload_dir / f"test_api_indexing_{uuid4().hex}.pdf"
        create_test_pdf(file_indexing, "Already Indexing Report")
        created_file_paths.append(file_indexing)

        doc_already_indexing = Document(
            user_id=user1_id,
            original_filename="indexing_report.pdf",
            stored_filename=file_indexing.name,
            content_type="application/pdf",
            file_size_bytes=file_indexing.stat().st_size,
            extracted_text="Already Indexing Report",
            status="processed",
            indexing_status="indexing",
        )
        db.add(doc_already_indexing)

        # 4. Document for Gemini failure & retry
        file_fail = upload_dir / f"test_api_fail_{uuid4().hex}.pdf"
        create_test_pdf(file_fail, "Fail and Retry Report\nRevenue: INR 800000")
        created_file_paths.append(file_fail)

        doc_fail = Document(
            user_id=user1_id,
            original_filename="fail_retry_report.pdf",
            stored_filename=file_fail.name,
            content_type="application/pdf",
            file_size_bytes=file_fail.stat().st_size,
            extracted_text="Fail and Retry Report\nRevenue: INR 800000",
            status="processed",
            indexing_status="pending",
        )
        db.add(doc_fail)

        db.commit()
        db.refresh(doc_valid)
        db.refresh(doc_unprocessed)
        db.refresh(doc_already_indexing)
        db.refresh(doc_fail)
        print("PASS: Test documents created")

        # Scenario 1: Authenticated indexing returns HTTP 200
        with patch.object(
            document_indexing_service,
            "generate_document_embeddings",
            side_effect=fake_embeddings,
        ):
            resp1 = client.post(f"/documents/{doc_valid.id}/index", headers=headers1)

        assert resp1.status_code == 200, f"Expected 200, got {resp1.status_code}: {resp1.text}"
        print("PASS: Authenticated indexing returns HTTP 200")

        # Scenario 2: Successful indexing response schema verified
        data1 = resp1.json()
        assert data1["id"] == doc_valid.id
        assert data1["indexing_status"] == "indexed"
        assert data1["indexed_at"] is not None
        assert data1["chunk_count"] > 0
        print("PASS: Successful indexing response schema verified")

        # Scenario 3: Unauthenticated request rejected with HTTP 401
        resp_unauth = client.post(f"/documents/{doc_valid.id}/index")
        assert resp_unauth.status_code == 401
        print("PASS: Unauthenticated request rejected with HTTP 401")

        # Scenario 4: Cross-user indexing rejected with HTTP 404
        resp_cross = client.post(f"/documents/{doc_valid.id}/index", headers=headers2)
        assert resp_cross.status_code == 404
        print("PASS: Cross-user indexing rejected with HTTP 404")

        # Scenario 5: Missing document rejected with HTTP 404
        resp_missing = client.post("/documents/999999999/index", headers=headers1)
        assert resp_missing.status_code == 404
        print("PASS: Missing document rejected with HTTP 404")

        # Scenario 6: Unprocessed document rejected with HTTP 409
        resp_unproc = client.post(f"/documents/{doc_unprocessed.id}/index", headers=headers1)
        assert resp_unproc.status_code == 409
        print("PASS: Unprocessed document rejected with HTTP 409")

        # Scenario 7: Already-indexing document rejected with HTTP 409
        resp_indexing = client.post(f"/documents/{doc_already_indexing.id}/index", headers=headers1)
        assert resp_indexing.status_code == 409
        print("PASS: Already-indexing document rejected with HTTP 409")

        # Scenario 8: Embedding failure returns HTTP 502
        with patch.object(
            document_indexing_service,
            "generate_document_embeddings",
            side_effect=EmbeddingGenerationError("Gemini quota exceeded"),
        ):
            resp_fail = client.post(f"/documents/{doc_fail.id}/index", headers=headers1)

        assert resp_fail.status_code == 502
        print("PASS: Embedding failure returns HTTP 502")

        # Scenario 9: Failed indexing can be retried successfully
        db.refresh(doc_fail)
        assert doc_fail.indexing_status == "failed"
        print("PASS: Failed indexing can be retried successfully")

        # Scenario 10: Retry returns HTTP 200 with valid response
        with patch.object(
            document_indexing_service,
            "generate_document_embeddings",
            side_effect=fake_embeddings,
        ):
            resp_retry = client.post(f"/documents/{doc_fail.id}/index", headers=headers1)

        assert resp_retry.status_code == 200
        data_retry = resp_retry.json()
        assert data_retry["id"] == doc_fail.id
        assert data_retry["indexing_status"] == "indexed"
        assert data_retry["chunk_count"] > 0
        print("PASS: Retry returns HTTP 200 with valid response")

        print("\nALL DOCUMENT INDEXING API TESTS PASSED!")

    finally:
        # Clean up database records
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

        # Clean up files
        for f in created_file_paths:
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass

        print("Test cleanup completed.")


if __name__ == "__main__":
    main()
