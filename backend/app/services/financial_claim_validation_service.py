from decimal import Decimal

from app.schemas.ai_advisor import FinancialClaim
from app.schemas.financial_context import FinancialContext


class FinancialClaimValidationError(Exception):
    """Raised when an AI-generated financial claim cannot be verified."""


# These values come exclusively from our deterministic backend calculations.
INVESTOR_METRICS = {
    "monthly_surplus": "monthly_surplus",
    "annual_income": "annual_income",
    "annual_expenses": "annual_expenses",
    "savings_rate_percent": "savings_rate_percent",
    "expense_ratio_percent": "expense_ratio_percent",
}

GOAL_METRICS = {
    "required_monthly_contribution": "required_monthly_contribution",
    "planned_monthly_investment": "planned_monthly_investment",
    "monthly_contribution_shortfall": "monthly_contribution_shortfall",
}

CLAIM_TOLERANCE = Decimal("0.01")


def _get_expected_value(
    claim: FinancialClaim,
    financial_context: FinancialContext,
) -> Decimal:
    """
    Retrieve the trusted backend value corresponding to an AI claim.
    """

    if claim.metric_key in INVESTOR_METRICS:
        metric_attribute = INVESTOR_METRICS[claim.metric_key]
        expected_value = getattr(
            financial_context.metrics,
            metric_attribute,
        )

        if expected_value is None:
            raise FinancialClaimValidationError(
                f"Cannot verify '{claim.metric_key}': "
                "the required financial information is unavailable."
            )

        return expected_value

    if claim.metric_key in GOAL_METRICS:
        goal_analysis = next(
            (
                goal
                for goal in financial_context.goal_analysis
                if goal.goal_id == claim.goal_id
            ),
            None,
        )

        if goal_analysis is None:
            raise FinancialClaimValidationError(
                f"Cannot verify '{claim.metric_key}': "
                f"goal {claim.goal_id} was not found in financial context."
            )

        metric_attribute = GOAL_METRICS[claim.metric_key]
        expected_value = getattr(goal_analysis, metric_attribute)

        if expected_value is None:
            raise FinancialClaimValidationError(
                f"Cannot verify '{claim.metric_key}' "
                f"for goal {claim.goal_id}: value is unavailable."
            )

        return expected_value

    raise FinancialClaimValidationError(
        f"Unsupported financial metric: {claim.metric_key}"
    )


def validate_financial_claims(
    financial_claims: list[FinancialClaim],
    financial_context: FinancialContext,
) -> None:
    """
    Verify all structured financial claims against trusted backend values.

    Raises FinancialClaimValidationError if any claim is unsupported,
    duplicated, unavailable, or numerically inconsistent.
    """

    if len(financial_claims) > 20:
        raise FinancialClaimValidationError(
            "Too many financial claims."
        )

    seen_claims: set[tuple[str, int | None]] = set()

    for claim in financial_claims:
        claim_identity = (claim.metric_key, claim.goal_id)

        if claim_identity in seen_claims:
            raise FinancialClaimValidationError(
                f"Duplicate financial claim: {claim.metric_key}"
            )

        seen_claims.add(claim_identity)

        if not claim.claimed_value.is_finite():
            raise FinancialClaimValidationError(
                f"Non-finite value supplied for '{claim.metric_key}'."
            )

        expected_value = _get_expected_value(
            claim,
            financial_context,
        )

        difference = abs(claim.claimed_value - expected_value)

        if difference > CLAIM_TOLERANCE:
            raise FinancialClaimValidationError(
                f"Financial claim mismatch for '{claim.metric_key}'. "
                f"AI claimed {claim.claimed_value}, "
                f"but backend calculated {expected_value}."
            )

