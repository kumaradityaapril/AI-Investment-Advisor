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


def test_asset_allocation_percentage_allowed():
    response = build_response(
        assessment="We recommend an asset allocation of 70% in equity and 30% in debt instruments.",
        claims=[],
    )

    _validate_numerical_claim_coverage(response)


def test_savings_rate_percentage_requires_claim():
    response = build_response(
        assessment="Your savings rate is 50% which is sufficient for your goals.",
        claims=[],
    )

    with pytest.raises(
        AdvisorOutputValidationError,
        match="Financial number 50 mentioned in explanation",
    ):
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


def test_market_return_percentage_alongside_savings_rate_passes():
    claim = FinancialClaim(
        metric_key="savings_rate_percent",
        claimed_value=Decimal("45.83"),
    )
    response = build_response(
        assessment="With a savings rate of 45.83%, an equity mutual fund delivering 14% annualized return is recommended.",
        claims=[claim],
    )
    _validate_numerical_claim_coverage(response)


def test_profile_verified_number_in_explanation_passes():
    from app.schemas.financial_context import InvestorProfileContext

    response = build_response(
        assessment="You currently have existing investments of ₹14.25 lakh and a monthly income of ₹1,20,000.",
        claims=[],
    )
    context = FinancialContext(
        user_id=1,
        profile=InvestorProfileContext(
            age=28,
            monthly_income=Decimal("120000.00"),
            monthly_expenses=Decimal("65000.00"),
            savings=Decimal("250000.00"),
            existing_investments=Decimal("1425000.00"),
            monthly_investment_capacity=Decimal("40000.00"),
        ),
        metrics=FinancialMetricsContext(),
        goal_analysis=[],
        generated_at=datetime.now(timezone.utc),
    )

    validated = validate_and_enforce_advisor_output(response, context)
    assert isinstance(validated, AIAdvisorGenerationResponse)


def test_following_negation_allowed():
    response = build_response(
        assessment="Guaranteed returns are not available in equity markets.",
        claims=[],
    )
    context = FinancialContext(
        user_id=1,
        metrics=FinancialMetricsContext(),
        goal_analysis=[],
        generated_at=datetime.now(timezone.utc),
    )
    validated = validate_and_enforce_advisor_output(response, context)
    assert isinstance(validated, AIAdvisorGenerationResponse)


def test_sovereign_ppf_statutory_guarantee_allowed():
    response = build_response(
        assessment="PPF offers sovereign-backed guaranteed returns of 7.1% as established by the Ministry of Finance.",
        claims=[],
    )
    context = FinancialContext(
        user_id=1,
        metrics=FinancialMetricsContext(),
        goal_analysis=[],
        generated_at=datetime.now(timezone.utc),
    )
    validated = validate_and_enforce_advisor_output(response, context)
    assert isinstance(validated, AIAdvisorGenerationResponse)


def test_market_guarantee_alongside_ppf_fails():
    response = build_response(
        assessment="While PPF provides sovereign backing, our equity portfolio delivers guaranteed returns.",
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


def test_no_risk_tolerance_phrase_allowed():
    response = build_response(
        assessment="Having no risk tolerance will hinder long-term compounding against inflation.",
        claims=[],
    )
    context = FinancialContext(
        user_id=1,
        metrics=FinancialMetricsContext(),
        goal_analysis=[],
        generated_at=datetime.now(timezone.utc),
    )
    validated = validate_and_enforce_advisor_output(response, context)
    assert isinstance(validated, AIAdvisorGenerationResponse)


def test_derived_goal_deficit_950000_passes():
    from app.schemas.financial_context import InvestorGoalContext, InvestorProfileContext

    response = build_response(
        assessment="To reach your ₹10,00,000 goal after factoring in your ₹50,000 savings, you need to accumulate ₹9,50,000.",
        claims=[],
    )
    context = FinancialContext(
        user_id=421,
        profile=InvestorProfileContext(
            monthly_income=Decimal("100000"),
            monthly_expenses=Decimal("45000"),
            savings=Decimal("50000"),
            monthly_investment_capacity=Decimal("40000"),
        ),
        metrics=FinancialMetricsContext(monthly_surplus=Decimal("55000")),
        goals=[
            InvestorGoalContext(
                id=1,
                title="Home Down Payment",
                goal_type="house",
                target_amount=Decimal("1000000"),
                time_horizon_months=60,
            )
        ],
        goal_analysis=[],
        generated_at=datetime.now(timezone.utc),
    )
    validated = validate_and_enforce_advisor_output(response, context)
    assert isinstance(validated, AIAdvisorGenerationResponse)


def test_explanatory_milestone_figure_passes_with_context():
    from app.schemas.financial_context import InvestorProfileContext

    response = build_response(
        assessment="Disciplined SIP investments into equity index funds could help build a long-term portfolio corpus of ₹35,00,000 over 15 years.",
        claims=[],
    )
    context = FinancialContext(
        user_id=421,
        profile=InvestorProfileContext(
            monthly_income=Decimal("100000"),
            monthly_expenses=Decimal("45000"),
            monthly_investment_capacity=Decimal("40000"),
        ),
        metrics=FinancialMetricsContext(monthly_surplus=Decimal("55000")),
        goal_analysis=[],
        generated_at=datetime.now(timezone.utc),
    )
    validated = validate_and_enforce_advisor_output(response, context)
    assert isinstance(validated, AIAdvisorGenerationResponse)


def test_hallucinated_personal_surplus_still_rejected():
    from app.schemas.financial_context import InvestorProfileContext

    response = build_response(
        assessment="Your monthly surplus is ₹9,50,000, giving you ample capital to deploy.",
        claims=[],
    )
    context = FinancialContext(
        user_id=421,
        profile=InvestorProfileContext(
            monthly_income=Decimal("100000"),
            monthly_expenses=Decimal("45000"),
        ),
        metrics=FinancialMetricsContext(monthly_surplus=Decimal("55000")),
        goal_analysis=[],
        generated_at=datetime.now(timezone.utc),
    )
    with pytest.raises(
        AdvisorOutputValidationError,
        match="Financial number 950000 mentioned in explanation",
    ):
        validate_and_enforce_advisor_output(response, context)
