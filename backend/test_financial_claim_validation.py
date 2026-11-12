from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.schemas.ai_advisor import FinancialClaim
from app.schemas.financial_context import (
    FinancialContext,
    FinancialGoalAnalysis,
    FinancialMetricsContext,
)
from app.services.financial_claim_validation_service import (
    FinancialClaimValidationError,
    validate_financial_claims,
)


def build_context():
    return FinancialContext(
        user_id=1,
        metrics=FinancialMetricsContext(
            monthly_surplus=Decimal("50000"),
            annual_income=Decimal("1200000"),
            annual_expenses=Decimal("600000"),
            savings_rate_percent=Decimal("50"),
            expense_ratio_percent=Decimal("50"),
        ),
        goal_analysis=[
            FinancialGoalAnalysis(
                goal_id=10,
                goal_title="Emergency Fund",
                required_monthly_contribution=Decimal("10000"),
                planned_monthly_investment=Decimal("8000"),
                monthly_contribution_shortfall=Decimal("2000"),
            )
        ],
        generated_at=datetime.now(timezone.utc),
    )


def test_valid_investor_claims_pass():
    context = build_context()
    claims = [
        FinancialClaim(
            metric_key="monthly_surplus",
            claimed_value=Decimal("50000"),
        ),
        FinancialClaim(
            metric_key="annual_income",
            claimed_value=Decimal("1200000"),
        ),
    ]

    validate_financial_claims(claims, context)


def test_valid_goal_claims_pass():
    context = build_context()
    claims = [
        FinancialClaim(
            metric_key="required_monthly_contribution",
            claimed_value=Decimal("10000"),
            goal_id=10,
        ),
        FinancialClaim(
            metric_key="monthly_contribution_shortfall",
            claimed_value=Decimal("2000"),
            goal_id=10,
        ),
    ]

    validate_financial_claims(claims, context)


def test_claim_value_mismatch_raises_error():
    context = build_context()
    claims = [
        FinancialClaim(
            metric_key="monthly_surplus",
            claimed_value=Decimal("55000"),
        )
    ]

    with pytest.raises(
        FinancialClaimValidationError,
        match="Financial claim mismatch",
    ):
        validate_financial_claims(claims, context)


def test_unavailable_metric_raises_error():
    context = FinancialContext(
        user_id=1,
        metrics=FinancialMetricsContext(monthly_surplus=None),
        goal_analysis=[],
        generated_at=datetime.now(timezone.utc),
    )
    claims = [
        FinancialClaim(
            metric_key="monthly_surplus",
            claimed_value=Decimal("50000"),
        )
    ]

    with pytest.raises(
        FinancialClaimValidationError,
        match="the required financial information is unavailable",
    ):
        validate_financial_claims(claims, context)


def test_nonexistent_goal_raises_error():
    context = build_context()
    claims = [
        FinancialClaim(
            metric_key="required_monthly_contribution",
            claimed_value=Decimal("10000"),
            goal_id=999,
        )
    ]

    with pytest.raises(
        FinancialClaimValidationError,
        match="goal 999 was not found",
    ):
        validate_financial_claims(claims, context)


def test_duplicate_claims_raise_error():
    context = build_context()
    claim1 = FinancialClaim(
        metric_key="monthly_surplus",
        claimed_value=Decimal("50000"),
    )
    claim2 = FinancialClaim(
        metric_key="monthly_surplus",
        claimed_value=Decimal("50000"),
    )

    with pytest.raises(
        FinancialClaimValidationError,
        match="Duplicate financial claim",
    ):
        validate_financial_claims([claim1, claim2], context)


def test_too_many_claims_raises_error():
    context = build_context()
    claims = [
        FinancialClaim(
            metric_key="monthly_surplus",
            claimed_value=Decimal("50000"),
        )
    ] * 21

    with pytest.raises(
        FinancialClaimValidationError,
        match="Too many financial claims",
    ):
        validate_financial_claims(claims, context)


def test_empty_claims_pass():
    context = build_context()
    validate_financial_claims([], context)
