from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.schemas.ai_advisor import (
    AIAdvisorGenerationResponse,
    AdvisorRecommendation,
    FinancialClaim,
)
from app.schemas.financial_context import (
    FinancialContext,
    FinancialMetricsContext,
)
from app.services.advisor_output_validation_service import (
    AdvisorOutputValidationError,
    _validate_numerical_claim_coverage,
    validate_and_enforce_advisor_output,
)


def build_response(
    assessment: str,
    claims: list[FinancialClaim] | None = None,
    recommendation_explanation: str = "Understand your current financial position.",
) -> AIAdvisorGenerationResponse:
    return AIAdvisorGenerationResponse(
        overall_assessment=assessment,
        key_findings=["Review your financial position carefully."],
        recommendations=[
            AdvisorRecommendation(
                title="Review your savings",
                explanation=recommendation_explanation,
                suggested_action="Review your monthly budget.",
                priority="medium",
            )
        ],
        limitations=["This analysis has limitations."],
        financial_claims=claims or [],
    )


def test_omitted_claim_in_assessment_raises_error():
    response = build_response(
        assessment="Your monthly surplus is ₹50,000 and should be invested.",
        claims=[],
    )

    with pytest.raises(
        AdvisorOutputValidationError,
        match="Financial number 50000 mentioned in explanation",
    ):
        _validate_numerical_claim_coverage(response)


def test_declared_claim_in_assessment_passes():
    claim = FinancialClaim(
        metric_key="monthly_surplus",
        claimed_value=Decimal("50000"),
    )
    response = build_response(
        assessment="Your monthly surplus is ₹50,000 and should be invested.",
        claims=[claim],
    )

    _validate_numerical_claim_coverage(response)


def test_omitted_claim_in_recommendation_raises_error():
    response = build_response(
        assessment="Your overall finances are stable.",
        claims=[],
        recommendation_explanation="We suggest an investment of ₹10,000 monthly into index funds.",
    )

    with pytest.raises(
        AdvisorOutputValidationError,
        match="Financial number 10000 mentioned in explanation",
    ):
        _validate_numerical_claim_coverage(response)


def test_time_period_not_treated_as_financial_number():
    response = build_response(
        assessment="Given your 10-year horizon, equities provide higher expected returns.",
        claims=[],
    )

    _validate_numerical_claim_coverage(response)


def test_unsafe_guaranteed_returns_raises_error():
    response = build_response(
        assessment="This scheme provides guaranteed returns for all investors.",
        claims=[],
    )
    context = FinancialContext(
        user_id=1,
        metrics=FinancialMetricsContext(),
        goal_analysis=[],
        generated_at=datetime.now(timezone.utc),
    )

    with pytest.raises(
        AdvisorOutputValidationError,
        match="Advisor response contains potentially misleading",
    ):
        validate_and_enforce_advisor_output(response, context)


def test_unsafe_risk_free_raises_error():
    response = build_response(
        assessment="This option offers a completely risk-free investment opportunity.",
        claims=[],
    )
    context = FinancialContext(
        user_id=1,
        metrics=FinancialMetricsContext(),
        goal_analysis=[],
        generated_at=datetime.now(timezone.utc),
    )

    with pytest.raises(
        AdvisorOutputValidationError,
        match="Advisor response contains potentially misleading",
    ):
        validate_and_enforce_advisor_output(response, context)


def test_negated_guarantee_warning_allowed():
    response = build_response(
        assessment="Please note that market returns are not guaranteed and capital may fluctuate.",
        claims=[],
    )
    context = FinancialContext(
        user_id=1,
        metrics=FinancialMetricsContext(),
        goal_analysis=[],
        generated_at=datetime.now(timezone.utc),
    )

    result = validate_and_enforce_advisor_output(response, context)
    assert isinstance(result, AIAdvisorGenerationResponse)


def test_missing_data_disclosures_injected():
    response = build_response(
        assessment="General financial analysis based on available records.",
        claims=[],
    )
    context = FinancialContext(
        user_id=1,
        metrics=FinancialMetricsContext(),
        goal_analysis=[],
        profile=None,
        risk_assessment=None,
        goals=[],
        documents=[],
        generated_at=datetime.now(timezone.utc),
    )

    validated = validate_and_enforce_advisor_output(response, context)

    # Disclosures should be deterministically added to limitations
    assert any("risk assessment was available" in lim for lim in validated.limitations)
    assert any("goals were available" in lim for lim in validated.limitations)
    assert any("documents were available" in lim for lim in validated.limitations)
