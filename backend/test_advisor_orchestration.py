from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.schemas.ai_advisor import (
    AIAdvisorGenerationResponse,
    AIAdvisorRequest,
    AIAdvisorResponse,
    AdvisorEvidence,
    AdvisorRecommendation,
)
from app.services import advisor_orchestration_service as orchestration
from app.services.advisor_output_validation_service import AdvisorOutputValidationError
from app.services.evidence_validation_service import EvidenceValidationError
from app.services.financial_claim_validation_service import FinancialClaimValidationError


@pytest.fixture
def advisor_request():
    return AIAdvisorRequest(
        question="Should I increase my monthly investments?"
    )


@pytest.fixture
def financial_context_with_documents():
    return SimpleNamespace(
        documents=[
            SimpleNamespace(
                document_id=1,
                filename="portfolio.pdf",
            )
        ]
    )


@pytest.fixture
def financial_context_without_documents():
    return SimpleNamespace(documents=[])


@pytest.fixture
def mock_advisor_response():
    return AIAdvisorGenerationResponse(
        overall_assessment="Overall financial assessment is solid.",
        key_findings=["Strong savings rate of 40%."],
        recommendations=[
            AdvisorRecommendation(
                title="Increase Equity Allocation",
                explanation="Given your 10-year horizon, equities provide higher expected returns.",
                suggested_action="Allocate 20% more to index funds.",
                priority="high",
            )
        ],
        risk_considerations=[
            "Market volatility could impact short-term returns."
        ],
        assumptions=["Assumes stable monthly income of 150000."],
        limitations=["Analysis does not account for tax optimization."],
        evidence_chunk_ids=[10],
    )


def test_successful_orchestration(
    monkeypatch,
    advisor_request,
    financial_context_with_documents,
    mock_advisor_response,
):
    mock_db = Mock()
    user_id = 1
    mock_chunks = [
        SimpleNamespace(chunk_id=10, content="Quarterly revenue")
    ]
    verified_evidence = [
        AdvisorEvidence(
            chunk_id=10,
            document_id=15,
            filename="actual_portfolio.pdf",
            page_number=4,
            supporting_excerpt="Verified portfolio information.",
        )
    ]
    mock_build_context = Mock(return_value=financial_context_with_documents)
    mock_retrieve = Mock(return_value=mock_chunks)
    mock_prompt = Mock(return_value="Constructed prompt string")
    mock_generate = Mock(return_value=mock_advisor_response)
    mock_validate_claims = Mock()
    mock_validate_output = Mock(return_value=mock_advisor_response)
    mock_validate_evidence = Mock(return_value=verified_evidence)

    monkeypatch.setattr(
        orchestration,
        "build_financial_context",
        mock_build_context,
    )
    monkeypatch.setattr(
        orchestration,
        "retrieve_and_rerank",
        mock_retrieve,
    )
    monkeypatch.setattr(
        orchestration,
        "build_advisor_prompt",
        mock_prompt,
    )
    monkeypatch.setattr(
        orchestration,
        "generate_advisor_response",
        mock_generate,
    )
    monkeypatch.setattr(
        orchestration,
        "validate_financial_claims",
        mock_validate_claims,
    )
    monkeypatch.setattr(
        orchestration,
        "validate_and_enforce_advisor_output",
        mock_validate_output,
    )
    monkeypatch.setattr(
        orchestration,
        "validate_and_build_evidence",
        mock_validate_evidence,
    )

    result = orchestration.get_ai_advisor_response(
        db=mock_db,
        user_id=user_id,
        request=advisor_request,
    )

    assert isinstance(result, AIAdvisorResponse)
    assert result.overall_assessment == mock_advisor_response.overall_assessment
    assert result.key_findings == mock_advisor_response.key_findings
    assert result.recommendations == mock_advisor_response.recommendations
    assert result.risk_considerations == mock_advisor_response.risk_considerations
    assert result.assumptions == mock_advisor_response.assumptions
    assert result.limitations == mock_advisor_response.limitations
    assert result.evidence == verified_evidence

    mock_build_context.assert_called_once_with(db=mock_db, user_id=user_id)
    mock_retrieve.assert_called_once_with(
        db=mock_db,
        query=advisor_request.question,
        user_id=user_id,
        top_k=5,
        candidate_k=20,
    )
    mock_prompt.assert_called_once_with(
        request=advisor_request,
        financial_context=financial_context_with_documents,
        retrieved_chunks=mock_chunks,
    )
    mock_generate.assert_called_once_with(prompt="Constructed prompt string")
    mock_validate_claims.assert_called_once_with(
        financial_claims=mock_advisor_response.financial_claims,
        financial_context=financial_context_with_documents,
    )
    mock_validate_output.assert_called_once_with(
        response=mock_advisor_response,
        financial_context=financial_context_with_documents,
    )
    mock_validate_evidence.assert_called_once_with(
        db=mock_db,
        user_id=user_id,
        evidence_chunk_ids=mock_advisor_response.evidence_chunk_ids,
        retrieved_chunks=mock_chunks,
    )


def test_orchestration_skips_retrieval_when_no_documents(
    monkeypatch,
    advisor_request,
    financial_context_without_documents,
    mock_advisor_response,
):
    mock_db = Mock()
    user_id = 1

    mock_build_context = Mock(
        return_value=financial_context_without_documents
    )
    mock_retrieve = Mock()
    mock_prompt = Mock(return_value="Prompt without documents")
    mock_generate = Mock(return_value=mock_advisor_response)
    mock_validate_claims = Mock()
    mock_validate_output = Mock(return_value=mock_advisor_response)
    mock_validate_evidence = Mock(return_value=[])

    monkeypatch.setattr(
        orchestration,
        "build_financial_context",
        mock_build_context,
    )
    monkeypatch.setattr(
        orchestration,
        "retrieve_and_rerank",
        mock_retrieve,
    )
    monkeypatch.setattr(
        orchestration,
        "build_advisor_prompt",
        mock_prompt,
    )
    monkeypatch.setattr(
        orchestration,
        "generate_advisor_response",
        mock_generate,
    )
    monkeypatch.setattr(
        orchestration,
        "validate_financial_claims",
        mock_validate_claims,
    )
    monkeypatch.setattr(
        orchestration,
        "validate_and_enforce_advisor_output",
        mock_validate_output,
    )
    monkeypatch.setattr(
        orchestration,
        "validate_and_build_evidence",
        mock_validate_evidence,
    )

    result = orchestration.get_ai_advisor_response(
        db=mock_db,
        user_id=user_id,
        request=advisor_request,
    )

    assert isinstance(result, AIAdvisorResponse)
    assert result.evidence == []
    mock_retrieve.assert_not_called()
    mock_prompt.assert_called_once_with(
        request=advisor_request,
        financial_context=financial_context_without_documents,
        retrieved_chunks=[],
    )
    mock_validate_claims.assert_called_once_with(
        financial_claims=mock_advisor_response.financial_claims,
        financial_context=financial_context_without_documents,
    )
    mock_validate_output.assert_called_once_with(
        response=mock_advisor_response,
        financial_context=financial_context_without_documents,
    )
    mock_validate_evidence.assert_called_once_with(
        db=mock_db,
        user_id=user_id,
        evidence_chunk_ids=mock_advisor_response.evidence_chunk_ids,
        retrieved_chunks=[],
    )


def test_orchestration_wraps_financial_context_failure(
    monkeypatch,
    advisor_request,
):
    mock_db = Mock()
    monkeypatch.setattr(
        orchestration,
        "build_financial_context",
        Mock(side_effect=RuntimeError("Database failure")),
    )

    with pytest.raises(
        orchestration.AdvisorOrchestrationError,
        match="Failed to build financial context",
    ):
        orchestration.get_ai_advisor_response(
            db=mock_db,
            user_id=1,
            request=advisor_request,
        )


def test_orchestration_wraps_retrieval_failure(
    monkeypatch,
    advisor_request,
    financial_context_with_documents,
):
    mock_db = Mock()
    monkeypatch.setattr(
        orchestration,
        "build_financial_context",
        Mock(return_value=financial_context_with_documents),
    )
    monkeypatch.setattr(
        orchestration,
        "retrieve_and_rerank",
        Mock(side_effect=RuntimeError("Vector search failure")),
    )

    with pytest.raises(
        orchestration.AdvisorOrchestrationError,
        match="Failed to retrieve document evidence",
    ):
        orchestration.get_ai_advisor_response(
            db=mock_db,
            user_id=1,
            request=advisor_request,
        )


def test_orchestration_wraps_prompt_failure(
    monkeypatch,
    advisor_request,
    financial_context_with_documents,
):
    mock_db = Mock()
    monkeypatch.setattr(
        orchestration,
        "build_financial_context",
        Mock(return_value=financial_context_with_documents),
    )
    monkeypatch.setattr(
        orchestration,
        "retrieve_and_rerank",
        Mock(return_value=[]),
    )
    monkeypatch.setattr(
        orchestration,
        "build_advisor_prompt",
        Mock(side_effect=ValueError("Prompt construction error")),
    )

    with pytest.raises(
        orchestration.AdvisorOrchestrationError,
        match="Failed to build advisor prompt",
    ):
        orchestration.get_ai_advisor_response(
            db=mock_db,
            user_id=1,
            request=advisor_request,
        )


def test_orchestration_wraps_generation_failure(
    monkeypatch,
    advisor_request,
    financial_context_with_documents,
):
    mock_db = Mock()
    monkeypatch.setattr(
        orchestration,
        "build_financial_context",
        Mock(return_value=financial_context_with_documents),
    )
    monkeypatch.setattr(
        orchestration,
        "retrieve_and_rerank",
        Mock(return_value=[]),
    )
    monkeypatch.setattr(
        orchestration,
        "build_advisor_prompt",
        Mock(return_value="Prompt"),
    )
    monkeypatch.setattr(
        orchestration,
        "generate_advisor_response",
        Mock(side_effect=RuntimeError("Gemini quota exceeded")),
    )

    with pytest.raises(
        orchestration.AdvisorOrchestrationError,
        match="Failed to generate advisor response",
    ):
        orchestration.get_ai_advisor_response(
            db=mock_db,
            user_id=1,
            request=advisor_request,
        )


def test_orchestration_wraps_financial_claim_validation_failure(
    monkeypatch,
    advisor_request,
    financial_context_with_documents,
    mock_advisor_response,
):
    mock_db = Mock()
    monkeypatch.setattr(
        orchestration,
        "build_financial_context",
        Mock(return_value=financial_context_with_documents),
    )
    monkeypatch.setattr(
        orchestration,
        "retrieve_and_rerank",
        Mock(return_value=[]),
    )
    monkeypatch.setattr(
        orchestration,
        "build_advisor_prompt",
        Mock(return_value="Prompt"),
    )
    monkeypatch.setattr(
        orchestration,
        "generate_advisor_response",
        Mock(return_value=mock_advisor_response),
    )
    monkeypatch.setattr(
        orchestration,
        "validate_financial_claims",
        Mock(side_effect=FinancialClaimValidationError("Claim mismatch")),
    )

    with pytest.raises(
        orchestration.AdvisorOrchestrationError,
        match="The generated advisor response contained unsupported financial claims.",
    ):
        orchestration.get_ai_advisor_response(
            db=mock_db,
            user_id=1,
            request=advisor_request,
        )


def test_orchestration_wraps_output_validation_failure(
    monkeypatch,
    advisor_request,
    financial_context_with_documents,
    mock_advisor_response,
):
    mock_db = Mock()
    monkeypatch.setattr(
        orchestration,
        "build_financial_context",
        Mock(return_value=financial_context_with_documents),
    )
    monkeypatch.setattr(
        orchestration,
        "retrieve_and_rerank",
        Mock(return_value=[]),
    )
    monkeypatch.setattr(
        orchestration,
        "build_advisor_prompt",
        Mock(return_value="Prompt"),
    )
    monkeypatch.setattr(
        orchestration,
        "generate_advisor_response",
        Mock(return_value=mock_advisor_response),
    )
    monkeypatch.setattr(
        orchestration,
        "validate_financial_claims",
        Mock(),
    )
    monkeypatch.setattr(
        orchestration,
        "validate_and_enforce_advisor_output",
        Mock(side_effect=AdvisorOutputValidationError("Unsafe language")),
    )

    with pytest.raises(
        orchestration.AdvisorOrchestrationError,
        match="The generated advisor response did not pass output safety validation.",
    ):
        orchestration.get_ai_advisor_response(
            db=mock_db,
            user_id=1,
            request=advisor_request,
        )


def test_orchestration_wraps_evidence_validation_failure(
    monkeypatch,
    advisor_request,
    financial_context_with_documents,
    mock_advisor_response,
):
    mock_db = Mock()
    monkeypatch.setattr(
        orchestration,
        "build_financial_context",
        Mock(return_value=financial_context_with_documents),
    )
    monkeypatch.setattr(
        orchestration,
        "retrieve_and_rerank",
        Mock(return_value=[
            SimpleNamespace(chunk_id=10, content="Portfolio data")
        ]),
    )
    monkeypatch.setattr(
        orchestration,
        "build_advisor_prompt",
        Mock(return_value="Prompt"),
    )
    monkeypatch.setattr(
        orchestration,
        "generate_advisor_response",
        Mock(return_value=mock_advisor_response),
    )
    monkeypatch.setattr(
        orchestration,
        "validate_financial_claims",
        Mock(),
    )
    monkeypatch.setattr(
        orchestration,
        "validate_and_enforce_advisor_output",
        Mock(return_value=mock_advisor_response),
    )
    monkeypatch.setattr(
        orchestration,
        "validate_and_build_evidence",
        Mock(side_effect=EvidenceValidationError("Evidence validation failed")),
    )

    with pytest.raises(
        orchestration.AdvisorOrchestrationError,
        match="Failed to validate document evidence",
    ):
        orchestration.get_ai_advisor_response(
            db=mock_db,
            user_id=1,
            request=advisor_request,
        )


def test_orchestration_rejects_invalid_request():
    mock_db = Mock()

    with pytest.raises(ValueError, match="Invalid AI Advisor request."):
        orchestration.get_ai_advisor_response(
            db=mock_db,
            user_id=1,
            request="not a request",  # type: ignore
        )

    with pytest.raises(ValueError, match="Invalid AI Advisor request."):
        orchestration.get_ai_advisor_response(
            db=mock_db,
            user_id=1,
            request=None,  # type: ignore
        )


@pytest.mark.parametrize(
    "invalid_user_id",
    [0, -1, -100, 1.5, "invalid", True, False],
)
def test_orchestration_rejects_invalid_user_id(invalid_user_id, advisor_request):
    mock_db = Mock()

    with pytest.raises(ValueError, match="Invalid user ID."):
        orchestration.get_ai_advisor_response(
            db=mock_db,
            user_id=invalid_user_id,  # type: ignore
            request=advisor_request,
        )
