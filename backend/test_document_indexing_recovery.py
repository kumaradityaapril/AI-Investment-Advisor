from datetime import datetime, timedelta, timezone
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Document, DocumentChunk, User
from app.services.auth_service import register_user
from app.services.document_indexing_service import (
    recover_stale_document_indexing,
)

created_user_id: int | None = None


def run_tests():
    global created_user_id
    db: Session = SessionLocal()
    try:
        # Pre-cleanup in case of previous interrupted run
        db.execute(text("DELETE FROM users WHERE email LIKE 'stale-recovery-%@example.com'"))
        db.commit()

        email = f"stale-recovery-{uuid4().hex[:12]}@example.com"
        user = register_user(
            db,
            email,
            "TestPassword123!",
        )
        created_user_id = user.id
        now = datetime.now(timezone.utc)

        # 1. Stale indexing document (> 30 minutes old)
        doc_stale = Document(
            user_id=user.id,
            original_filename="stale_doc.pdf",
            stored_filename=f"stale_{uuid4().hex}.pdf",
            content_type="application/pdf",
            file_size_bytes=1000,
            status="processed",
            extracted_text="Sample text",
            indexing_status="indexing",
            indexing_started_at=now - timedelta(minutes=45),
        )
        db.add(doc_stale)
        db.flush()

        # Add an existing chunk to doc_stale to verify chunks are preserved
        mock_embedding = [1.0] + [0.0] * (settings.embedding_dimensions - 1)
        stale_chunk = DocumentChunk(
            document_id=doc_stale.id,
            chunk_index=0,
            page_number=1,
            content="Previous valid chunk",
            embedding=mock_embedding,
        )
        db.add(stale_chunk)

        # 2. Recent indexing document (< 30 minutes old)
        doc_recent = Document(
            user_id=user.id,
            original_filename="recent_doc.pdf",
            stored_filename=f"recent_{uuid4().hex}.pdf",
            content_type="application/pdf",
            file_size_bytes=1000,
            status="processed",
            extracted_text="Sample text",
            indexing_status="indexing",
            indexing_started_at=now - timedelta(minutes=5),
        )
        db.add(doc_recent)

        # 3. Pending document
        doc_pending = Document(
            user_id=user.id,
            original_filename="pending_doc.pdf",
            stored_filename=f"pending_{uuid4().hex}.pdf",
            content_type="application/pdf",
            file_size_bytes=1000,
            status="processed",
            extracted_text="Sample text",
            indexing_status="pending",
            indexing_started_at=None,
        )
        db.add(doc_pending)

        # 4. Successfully indexed document
        doc_indexed = Document(
            user_id=user.id,
            original_filename="indexed_doc.pdf",
            stored_filename=f"indexed_{uuid4().hex}.pdf",
            content_type="application/pdf",
            file_size_bytes=1000,
            status="processed",
            extracted_text="Sample text",
            indexing_status="indexed",
            indexing_started_at=None,
            indexed_at=now,
        )
        db.add(doc_indexed)

        # 5. Indexing document without start timestamp
        doc_no_timestamp = Document(
            user_id=user.id,
            original_filename="no_timestamp_doc.pdf",
            stored_filename=f"no_ts_{uuid4().hex}.pdf",
            content_type="application/pdf",
            file_size_bytes=1000,
            status="processed",
            extracted_text="Sample text",
            indexing_status="indexing",
            indexing_started_at=None,
        )
        db.add(doc_no_timestamp)

        db.commit()
        print("PASS: Recovery test documents created")

        # Run recovery
        recovered_count = recover_stale_document_indexing(db)
        assert recovered_count == 1
        print("PASS: Exactly one stale document recovered")

        # Verify doc_stale was marked failed
        db.refresh(doc_stale)
        assert doc_stale.indexing_status == "failed"
        assert doc_stale.indexing_started_at is None
        print("PASS: Stale document marked failed")

        # Verify doc_recent was left untouched
        db.refresh(doc_recent)
        assert doc_recent.indexing_status == "indexing"
        assert doc_recent.indexing_started_at is not None
        print("PASS: Recent indexing operation left untouched")

        # Verify doc_pending was left untouched
        db.refresh(doc_pending)
        assert doc_pending.indexing_status == "pending"
        print("PASS: Pending document left untouched")

        # Verify doc_indexed was left untouched
        db.refresh(doc_indexed)
        assert doc_indexed.indexing_status == "indexed"
        print("PASS: Successfully indexed document left untouched")

        # Verify doc_no_timestamp was left untouched
        db.refresh(doc_no_timestamp)
        assert doc_no_timestamp.indexing_status == "indexing"
        print("PASS: Document without start timestamp left untouched")

        # Verify existing vector chunks on doc_stale preserved
        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == doc_stale.id)
            .all()
        )
        assert len(chunks) == 1
        assert chunks[0].content == "Previous valid chunk"
        print("PASS: Existing vector chunks preserved")

        # Verify repeated recovery does not modify documents
        repeat_count = recover_stale_document_indexing(db)
        assert repeat_count == 0
        print("PASS: Repeated recovery does not modify documents")

        print("\nALL STALE RECOVERY TESTS PASSED!")

    finally:
        if created_user_id:
            try:
                user_record = db.get(User, created_user_id)
                if user_record:
                    db.delete(user_record)
                db.commit()
            except Exception:
                db.rollback()
        try:
            db.close()
        except Exception:
            pass


if __name__ == "__main__":
    run_tests()

