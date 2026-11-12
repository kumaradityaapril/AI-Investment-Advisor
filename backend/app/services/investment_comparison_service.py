from decimal import Decimal
import json
import logging
import re
from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.financial_context import FinancialContext
from app.schemas.investment_comparison import (
    COMPARISON_DISCLAIMER,
    InvestmentComparisonExplanation,
    InvestmentComparisonItem,
    InvestmentComparisonRequest,
    InvestmentComparisonResponse,
    OptionSuitability,
)
from app.services.advisor_output_validation_service import (
    UNSAFE_FINANCIAL_PATTERNS,
    _is_negated,
)
from app.services.financial_calculation_service import (
    calculate_future_value_lumpsum,
    calculate_future_value_sip,
)

logger = logging.getLogger(__name__)


class InvestmentComparisonError(Exception):
    """Raised when investment comparison fails."""


def _get_gemini_client() -> genai.Client:
    """Create a Gemini client using configured settings."""
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options={
            "api_version": "v1beta",
            "timeout": 30000,
        },
    )


def compute_comparison_items(
    request: InvestmentComparisonRequest,
) -> list[InvestmentComparisonItem]:
    """
    Compute side-by-side comparison data including deterministic future values.
    """
    items = []
    has_projection = (
        request.investment_amount is not None
        and request.time_horizon_months is not None
    )

    for opt in request.options:
        fv = None
        total_inv = None
        total_earnings = None

        if has_projection:
            amount = request.investment_amount  # type: ignore
            months = request.time_horizon_months  # type: ignore

            if request.investment_type == "lump_sum":
                fv = calculate_future_value_lumpsum(
                    principal=amount,
                    annual_return_percent=opt.expected_annual_return_percent,
                    time_horizon_months=months,
                )
                total_inv = amount
                total_earnings = fv - total_inv
            else:
                fv = calculate_future_value_sip(
                    monthly_contribution=amount,
                    annual_return_percent=opt.expected_annual_return_percent,
                    time_horizon_months=months,
                )
                total_inv = amount * Decimal(months)
                total_earnings = fv - total_inv

        items.append(
            InvestmentComparisonItem(
                name=opt.name,
                category=opt.category,
                expected_annual_return_percent=opt.expected_annual_return_percent,
                risk_level=opt.risk_level,
                liquidity=opt.liquidity,
                lock_in_period_months=opt.lock_in_period_months,
                recommended_horizon_months=opt.recommended_horizon_months,
                tax_implications=opt.tax_implications,
                capital_protection=opt.capital_protection,
                advantages=opt.advantages,
                disadvantages=opt.disadvantages,
                projected_future_value=fv,
                projected_total_investment=total_inv,
                projected_total_earnings=total_earnings,
            )
        )

    return items


def build_comparison_prompt(
    request: InvestmentComparisonRequest,
    comparison_items: list[InvestmentComparisonItem],
    financial_context: FinancialContext | None = None,
) -> str:
    """Build grounded system instructions and data context for comparison."""

    options_data = [item.model_dump(mode="json") for item in comparison_items]

    investor_summary = {}
    if financial_context is not None:
        if financial_context.risk_assessment:
            investor_summary["risk_category"] = financial_context.risk_assessment.risk_category
            investor_summary["risk_score"] = financial_context.risk_assessment.risk_score
        if financial_context.profile:
            investor_summary["monthly_surplus"] = str(financial_context.metrics.monthly_surplus)
            investor_summary["investment_capacity"] = str(
                financial_context.profile.monthly_investment_capacity
            )
        if financial_context.goals:
            investor_summary["goals"] = [
                {
                    "title": g.title,
                    "target_amount": str(g.target_amount),
                    "horizon_months": g.time_horizon_months,
                }
                for g in financial_context.goals
            ]

    instructions = """You are an objective, professional financial analyst comparing investment options.

CORE RESPONSIBILITIES:
1. Provide an objective, balanced comparison of the specified options.
2. Clearly highlight differences across risk, returns, liquidity, lock-in, and tax implications.
3. For each option, specify who it is suitable for, who it is unsuitable for, and its primary trade-off.
4. If investor context is supplied, tailor the suitability analysis to their risk profile and goals.
5. NEVER declare one option as universally "better", "the winner", or "the best choice". Every investment involves tradeoffs.
6. NEVER claim guaranteed returns, risk-free profits, or absolute certainty.
7. Return your response matching the InvestmentComparisonExplanation schema."""

    prompt_parts = [
        instructions,
        "\n=== OPTIONS TO COMPARE ===",
        json.dumps(options_data, indent=2),
    ]

    if investor_summary:
        prompt_parts.extend([
            "\n=== INVESTOR CONTEXT ===",
            json.dumps(investor_summary, indent=2),
        ])

    if request.investor_question:
        prompt_parts.extend([
            "\n=== INVESTOR QUESTION ===",
            request.investor_question,
        ])

    prompt_parts.append(
        "\n=== OUTPUT INSTRUCTIONS ===\n"
        "Produce a structured comparative analysis in the specified JSON schema without picking winners."
    )

    return "\n".join(prompt_parts)


def _validate_comparison_explanation_safety(
    explanation: InvestmentComparisonExplanation,
) -> None:
    """Enforce risk language safety on AI comparison outputs."""
    texts = [
        explanation.summary,
        *explanation.key_differences,
        *explanation.risk_tradeoffs,
        *explanation.assumptions_and_missing_info,
    ]
    for suitability in explanation.suitability_analysis:
        texts.extend([
            suitability.suitable_for,
            suitability.unsuitable_for,
            suitability.key_tradeoff,
        ])

    for text in texts:
        for pattern in UNSAFE_FINANCIAL_PATTERNS:
            for match in pattern.finditer(text):
                if _is_negated(text, match.start()):
                    continue
                raise InvestmentComparisonError(
                    "AI comparison contains disallowed certainty or risk-free language."
                )


def _parse_comparison_response(response: Any) -> InvestmentComparisonExplanation:
    """Parse and validate Gemini's structured response."""
    if response is None:
        raise InvestmentComparisonError("Gemini returned an empty response.")

    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, InvestmentComparisonExplanation):
        return parsed

    text = getattr(response, "text", None)
    if not text or not str(text).strip():
        raise InvestmentComparisonError("Gemini returned an empty response.")

    try:
        return InvestmentComparisonExplanation.model_validate_json(text)
    except ValidationError as exc:
        raise InvestmentComparisonError(
            f"Failed to validate comparison explanation: {exc}"
        ) from exc


def generate_comparison_explanation(
    prompt: str,
    client: genai.Client | None = None,
) -> InvestmentComparisonExplanation:
    """Generate structured comparison explanation from Gemini."""
    if client is None:
        try:
            client = _get_gemini_client()
        except Exception as exc:
            raise InvestmentComparisonError(
                f"Failed to initialize Gemini client: {exc}"
            ) from exc

    try:
        response = client.models.generate_content(
            model=settings.advisor_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=3000,
                response_mime_type="application/json",
                response_schema=InvestmentComparisonExplanation,
            ),
        )
    except Exception as exc:
        logger.exception("Gemini comparison generation failed.")
        raise InvestmentComparisonError(
            f"Failed to generate comparison explanation: {exc}"
        ) from exc

    explanation = _parse_comparison_response(response)
    _validate_comparison_explanation_safety(explanation)
    return explanation


def compare_investments(
    request: InvestmentComparisonRequest,
    financial_context: FinancialContext | None = None,
    client: genai.Client | None = None,
) -> InvestmentComparisonResponse:
    """
    Main orchestration for comparing investment options.
    1. Computes deterministic comparison table and projections.
    2. Builds grounded prompt with investor context if available.
    3. Generates structured AI comparison explanation.
    4. Validates safety and returns unified response with disclaimer.
    """
    if not isinstance(request, InvestmentComparisonRequest):
        raise ValueError("Invalid investment comparison request.")

    # 1. Deterministic comparison items
    comparison_table = compute_comparison_items(request)

    # 2. Build prompt
    prompt = build_comparison_prompt(
        request=request,
        comparison_items=comparison_table,
        financial_context=financial_context,
    )

    # 3. Generate structured explanation
    explanation = generate_comparison_explanation(prompt=prompt, client=client)

    # 4. Assemble response
    return InvestmentComparisonResponse(
        comparison_table=comparison_table,
        ai_explanation=explanation,
        disclaimer=COMPARISON_DISCLAIMER,
    )

