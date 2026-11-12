
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.schemas.ai_advisor import AdvisorEvidence

logger = logging.getLogger(__name__)


class EvidenceValidationError(Exception):
    """Raised when evidence validation cannot be completed."""


def validate_and_build_evidence(
    db: Session,
    user_id: int,
    evidence_chunk_ids: list[int],
    retrieved_chunks: list,
) -> list[AdvisorEvidence]:
    """
    Validate Gemini-selected evidence IDs and construct trusted citations.

    An evidence chunk must:
    1. Be present in the actual retrieval results.
    2. Exist in the database.
    3. Belong to the authenticated investor.

    All final evidence metadata is retrieved from PostgreSQL.
    """

    # ---------------------------------------------------------
    # 1. Validate user ID
    # ---------------------------------------------------------

    if (
        not isinstance(user_id, int)
        or isinstance(user_id, bool)
        or user_id <= 0
    ):
        raise ValueError("Invalid user ID.")

    # ---------------------------------------------------------
    # 2. Validate requested evidence IDs
    # ---------------------------------------------------------

    if not isinstance(evidence_chunk_ids, list):
        raise ValueError("Evidence chunk IDs must be a list.")

    if len(evidence_chunk_ids) > 5:
        raise ValueError("At most five evidence chunks are allowed.")

    if any(
        not isinstance(chunk_id, int)
        or isinstance(chunk_id, bool)
        or chunk_id <= 0
        for chunk_id in evidence_chunk_ids
    ):
        raise ValueError("Evidence chunk IDs must be positive integers.")

    if len(evidence_chunk_ids) != len(set(evidence_chunk_ids)):
        raise ValueError("Duplicate evidence chunk IDs are not allowed.")

    if not evidence_chunk_ids:
        return []

    # ---------------------------------------------------------
    # 3. Build a map of actual retrieval results
    # ---------------------------------------------------------

    if not isinstance(retrieved_chunks, list):
        raise ValueError("Retrieved chunks must be a list.")

    retrieved_by_id = {}

    for chunk in retrieved_chunks:
        chunk_id = getattr(chunk, "chunk_id", None)

        if not isinstance(chunk_id, int) or isinstance(chunk_id, bool):
            continue

        if chunk_id in retrieved_by_id:
            raise EvidenceValidationError(
                "Duplicate chunk IDs found in retrieval results."
            )

        retrieved_by_id[chunk_id] = chunk

    # Only IDs returned by the retrieval pipeline are eligible.
    eligible_ids = [
        chunk_id
        for chunk_id in evidence_chunk_ids
        if chunk_id in retrieved_by_id
    ]

    if not eligible_ids:
        logger.warning(
            "AI Advisor returned no verifiable evidence IDs for user %s.",
            user_id,
        )
        return []

    # ---------------------------------------------------------
    # 4. Verify database ownership and retrieve trusted metadata
    # ---------------------------------------------------------

    statement = (
        select(DocumentChunk, Document)
        .join(
            Document,
            DocumentChunk.document_id == Document.id,
        )
        .where(
            DocumentChunk.id.in_(eligible_ids),
            Document.user_id == user_id,
            Document.status == "processed",
            Document.indexing_status == "indexed",
        )
    )

    try:
        rows = db.execute(statement).all()

    except Exception as exc:
        logger.exception(
            "Database evidence verification failed for user %s.",
            user_id,
        )

        raise EvidenceValidationError(
            "Unable to verify financial document evidence."
        ) from exc

    database_records = {
        chunk.id: (chunk, document)
        for chunk, document in rows
    }

    # ---------------------------------------------------------
    # 5. Construct evidence using trusted database records
    # ---------------------------------------------------------

    verified_evidence = []

    for chunk_id in evidence_chunk_ids:

        # Reject IDs not found in retrieval results.
        if chunk_id not in retrieved_by_id:
            logger.warning(
                "Discarding evidence ID %s not present in retrieval results.",
                chunk_id,
            )
            continue

        # Reject IDs not verified against the investor's database records.
        if chunk_id not in database_records:
            logger.warning(
                "Discarding unverified evidence ID %s for user %s.",
                chunk_id,
                user_id,
            )
            continue

        chunk, document = database_records[chunk_id]

        excerpt = chunk.content.strip()[:1000]

        if not excerpt:
            logger.warning(
                "Discarding empty evidence chunk %s.",
                chunk_id,
            )
            continue

        verified_evidence.append(
            AdvisorEvidence(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                filename=document.original_filename,
                page_number=chunk.page_number,
                supporting_excerpt=excerpt,
            )
        )

    return verified_evidence
