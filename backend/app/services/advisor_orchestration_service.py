import logging

from sqlalchemy.orm import Session

from app.schemas.ai_advisor import (
    AIAdvisorGenerationResponse,
    AIAdvisorRequest,
    AIAdvisorResponse,
)
from app.services.advisor_output_validation_service import (
    AdvisorOutputValidationError,
    validate_and_enforce_advisor_output,
)
from app.services.advisor_prompt_service import build_advisor_prompt
from app.services.ai_advisor_service import generate_advisor_response
from app.services.evidence_validation_service import (
    EvidenceValidationError,
    validate_and_build_evidence,
)
from app.services.financial_claim_validation_service import (
    FinancialClaimValidationError,
    validate_financial_claims,
)
from app.services.financial_context_service import build_financial_context
from app.services.retrieval_pipeline_service import retrieve_and_rerank

logger = logging.getLogger(__name__)


class AdvisorOrchestrationError(Exception):
    """Raised when the AI Advisor pipeline cannot be completed."""


def get_ai_advisor_response(
    db: Session,
    user_id: int,
    request: AIAdvisorRequest,
) -> AIAdvisorResponse:
    """
    Orchestrate financial context, RAG retrieval, prompt construction,
    structured Gemini generation, and trusted evidence validation.
    """
    if not isinstance(request, AIAdvisorRequest):
        raise ValueError("Invalid AI Advisor request.")

    if (
        not isinstance(user_id, int)
        or isinstance(user_id, bool)
        or user_id <= 0
    ):
        raise ValueError("Invalid user ID.")

    # 1. Build financial context for the authenticated investor.
    try:
        financial_context = build_financial_context(
            db=db,
            user_id=user_id,
        )
    except Exception as exc:
        logger.exception("Failed to build financial context for user %s.", user_id)
        raise AdvisorOrchestrationError(
            "Failed to build financial context."
        ) from exc

    # 2. Retrieve relevant document chunks only if investor has indexed documents
    retrieved_chunks = []
    if financial_context.documents:
        try:
            retrieved_chunks = retrieve_and_rerank(
                db=db,
                query=request.question,
                user_id=user_id,
                top_k=5,
                candidate_k=20,
            )
        except Exception as exc:
            logger.exception(
                "Failed to retrieve document evidence for user %s.", user_id
            )
            raise AdvisorOrchestrationError(
                "Failed to retrieve document evidence."
            ) from exc

    # 3. Construct advisor prompt
    try:
        prompt = build_advisor_prompt(
            request=request,
            financial_context=financial_context,
            retrieved_chunks=retrieved_chunks,
        )
    except Exception as exc:
        logger.exception("Failed to build advisor prompt for user %s.", user_id)
        raise AdvisorOrchestrationError(
            "Failed to build advisor prompt."
        ) from exc

    # 4. Generate structured advisor response using Gemini
    try:
        generated_response: AIAdvisorGenerationResponse = generate_advisor_response(
            prompt=prompt
        )
    except Exception as exc:
        logger.exception(
            "Failed to generate advisor response for user %s.", user_id
        )
        raise AdvisorOrchestrationError(
            "Failed to generate advisor response."
        ) from exc

    # 5. Validate financial claims against trusted financial context
    try:
        validate_financial_claims(
            financial_claims=generated_response.financial_claims,
            financial_context=financial_context,
        )
    except FinancialClaimValidationError as exc:
        logger.warning(
            "Financial claim validation failed for user_id=%s: %s",
            user_id,
            exc,
        )
        raise AdvisorOrchestrationError(
            "The generated advisor response contained "
            "unsupported financial claims."
        ) from exc

    # 6. Validate risk language and enforce missing-data disclosures
    try:
        generated_response = validate_and_enforce_advisor_output(
            response=generated_response,
            financial_context=financial_context,
        )
    except AdvisorOutputValidationError as exc:
        logger.warning(
            "Advisor output validation failed for user_id=%s: %s",
            user_id,
            exc,
        )
        raise AdvisorOrchestrationError(
            "The generated advisor response did not pass "
            "output safety validation."
        ) from exc

    # 7. Validate evidence IDs and build trusted citations from PostgreSQL
    try:
        verified_evidence = validate_and_build_evidence(
            db=db,
            user_id=user_id,
            evidence_chunk_ids=generated_response.evidence_chunk_ids,
            retrieved_chunks=retrieved_chunks,
        )
    except Exception as exc:
        logger.exception(
            "Failed to validate document evidence for user %s.", user_id
        )
        raise AdvisorOrchestrationError(
            "Failed to validate document evidence."
        ) from exc

    # 8. Assemble final response with verified evidence and fixed disclaimer
    return AIAdvisorResponse(
        overall_assessment=generated_response.overall_assessment,
        key_findings=generated_response.key_findings,
        recommendations=generated_response.recommendations,
        risk_considerations=generated_response.risk_considerations,
        assumptions=generated_response.assumptions,
        limitations=generated_response.limitations,
        evidence=verified_evidence,
    )
