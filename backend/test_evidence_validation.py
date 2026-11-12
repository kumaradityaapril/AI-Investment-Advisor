
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.services.evidence_validation_service import (
    EvidenceValidationError,
    validate_and_build_evidence,
)
from app.services.reranking_service import RerankedChunk


def make_retrieved_chunk(
    chunk_id=101,
    document_id=15,
):
    """Create a realistic retrieval result."""

    return RerankedChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        document_name="retrieved_portfolio.pdf",
        page_number=2,
        chunk_index=0,
        content="Retrieved chunk content.",
        relevance_score=0.95,
        rrf_score=0.032,
        semantic_rank=1,
        keyword_rank=1,
        rerank_rank=1,
    )


def make_database_records(
    chunk_id=101,
    document_id=15,
    user_id=10,
    content="Actual verified financial information from the database.",
):
    """Create database-like records for a retrieved chunk."""

    db_chunk = SimpleNamespace(
        id=chunk_id,
        document_id=document_id,
        page_number=4,
        content=content,
    )

    db_document = SimpleNamespace(
        id=document_id,
        user_id=user_id,
        original_filename="actual_portfolio.pdf",
        status="processed",
        indexing_status="indexed",
    )

    return db_chunk, db_document


def make_mock_db(rows=None, side_effect=None):
    db = Mock()

    if side_effect is not None:
        db.execute.side_effect = side_effect
    else:
        db.execute.return_value.all.return_value = rows or []

    return db


def test_builds_verified_evidence_from_database():
    """Evidence metadata must come from PostgreSQL, not retrieval metadata."""

    retrieved = make_retrieved_chunk()

    db_chunk, db_document = make_database_records()

    db = make_mock_db(rows=[(db_chunk, db_document)])

    result = validate_and_build_evidence(
        db=db,
        user_id=10,
        evidence_chunk_ids=[101],
        retrieved_chunks=[retrieved],
    )

    assert len(result) == 1

    evidence = result[0]

    assert evidence.chunk_id == 101
    assert evidence.document_id == 15

    # Database metadata must be used instead of retrieval metadata.
    assert evidence.filename == "actual_portfolio.pdf"
    assert evidence.page_number == 4

    assert (
        evidence.supporting_excerpt
        == "Actual verified financial information from the database."
    )


def test_discards_unknown_chunk_ids():
    """Gemini cannot cite chunks absent from retrieval results."""

    retrieved = make_retrieved_chunk()

    db = make_mock_db()

    result = validate_and_build_evidence(
        db=db,
        user_id=10,
        evidence_chunk_ids=[999],
        retrieved_chunks=[retrieved],
    )

    assert result == []

    # No database lookup should happen for an unknown ID.
    db.execute.assert_not_called()


def test_discards_cross_user_evidence():
    """A chunk belonging to another investor must never be returned."""

    retrieved = make_retrieved_chunk()

    # Simulate the database ownership filter returning no matching records.
    db = make_mock_db(rows=[])

    result = validate_and_build_evidence(
        db=db,
        user_id=10,
        evidence_chunk_ids=[101],
        retrieved_chunks=[retrieved],
    )

    assert result == []

    db.execute.assert_called_once()

    statement = db.execute.call_args.args[0]
    compiled = statement.compile()

    # Verify that the authenticated user's ID is included in the SQL filter.
    assert 10 in compiled.params.values()


def test_keeps_valid_evidence_and_discards_unknown_ids():
    """One invalid citation should not discard valid citations."""

    retrieved = make_retrieved_chunk()

    db_chunk, db_document = make_database_records()

    db = make_mock_db(rows=[(db_chunk, db_document)])

    result = validate_and_build_evidence(
        db=db,
        user_id=10,
        evidence_chunk_ids=[101, 999],
        retrieved_chunks=[retrieved],
    )

    assert len(result) == 1
    assert result[0].chunk_id == 101


def test_rejects_duplicate_requested_ids():
    retrieved = make_retrieved_chunk()

    db = make_mock_db()

    with pytest.raises(ValueError, match="Duplicate"):
        validate_and_build_evidence(
            db=db,
            user_id=10,
            evidence_chunk_ids=[101, 101],
            retrieved_chunks=[retrieved],
        )

    db.execute.assert_not_called()


@pytest.mark.parametrize(
    "invalid_id",
    [0, -1, True, "101", 1.5, None],
)
def test_rejects_invalid_evidence_ids(invalid_id):
    retrieved = make_retrieved_chunk()

    db = make_mock_db()

    with pytest.raises(ValueError, match="positive integers"):
        validate_and_build_evidence(
            db=db,
            user_id=10,
            evidence_chunk_ids=[invalid_id],
            retrieved_chunks=[retrieved],
        )

    db.execute.assert_not_called()


def test_rejects_more_than_five_evidence_ids():
    retrieved = [
        make_retrieved_chunk(chunk_id=i)
        for i in range(1, 7)
    ]

    db = make_mock_db()

    with pytest.raises(ValueError, match="At most five"):
        validate_and_build_evidence(
            db=db,
            user_id=10,
            evidence_chunk_ids=[1, 2, 3, 4, 5, 6],
            retrieved_chunks=retrieved,
        )

    db.execute.assert_not_called()


def test_empty_evidence_returns_empty_list():
    db = make_mock_db()

    result = validate_and_build_evidence(
        db=db,
        user_id=10,
        evidence_chunk_ids=[],
        retrieved_chunks=[],
    )

    assert result == []
    db.execute.assert_not_called()


def test_wraps_database_failure():
    retrieved = make_retrieved_chunk()

    db = make_mock_db(
        side_effect=RuntimeError("Database connection failed")
    )

    with pytest.raises(
        EvidenceValidationError,
        match="Unable to verify financial document evidence",
    ):
        validate_and_build_evidence(
            db=db,
            user_id=10,
            evidence_chunk_ids=[101],
            retrieved_chunks=[retrieved],
        )


def test_rejects_duplicate_ids_in_retrieval_results():
    retrieved = [
        make_retrieved_chunk(chunk_id=101),
        make_retrieved_chunk(chunk_id=101),
    ]

    db = make_mock_db()

    with pytest.raises(
        EvidenceValidationError,
        match="Duplicate chunk IDs",
    ):
        validate_and_build_evidence(
            db=db,
            user_id=10,
            evidence_chunk_ids=[101],
            retrieved_chunks=retrieved,
        )

    db.execute.assert_not_called()


def test_discards_empty_database_content():
    retrieved = make_retrieved_chunk()

    db_chunk, db_document = make_database_records(content="   ")

    db = make_mock_db(rows=[(db_chunk, db_document)])

    result = validate_and_build_evidence(
        db=db,
        user_id=10,
        evidence_chunk_ids=[101],
        retrieved_chunks=[retrieved],
    )

    assert result == []


def test_rejects_invalid_user_id():
    db = make_mock_db()

    with pytest.raises(ValueError, match="Invalid user ID"):
        validate_and_build_evidence(
            db=db,
            user_id=0,
            evidence_chunk_ids=[101],
            retrieved_chunks=[make_retrieved_chunk()],
        )

    db.execute.assert_not_called()
