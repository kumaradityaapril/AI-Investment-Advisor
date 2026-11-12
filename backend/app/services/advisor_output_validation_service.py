from decimal import Decimal, InvalidOperation
import re

from app.schemas.ai_advisor import AIAdvisorGenerationResponse
from app.schemas.financial_context import FinancialContext


class AdvisorOutputValidationError(Exception):
    """Raised when an advisor response contains unsafe claims
    or cannot satisfy output validation requirements.
    """


# Detect affirmative claims that incorrectly imply certainty or
# absence of investment risk.
UNSAFE_FINANCIAL_PATTERNS = [
    re.compile(
        r"\b(?:guaranteed|assured)\s+(?:positive\s+)?"
        r"(?:returns?|profits?|gains?|income)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:guaranteed|assured)\s+to\s+"
        r"(?:earn|make|generate|deliver)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:risk[- ]free|zero[- ]risk)\s+"
        r"(?:investment|returns?|profits?|strategy)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bno\s+risk\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:cannot|can't|will not|won't)\s+"
        r"(?:lose|suffer a loss)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:100\s*%\s*(?:safe|guaranteed)|"
        r"completely\s+safe)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:will definitely|certainly)\s+"
        r"(?:earn|make|generate|profit|gain)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:principal|capital)\s+(?:is|will be)\s+"
        r"(?:guaranteed|protected)\b",
        re.IGNORECASE,
    ),
]

# A negated statement such as "returns are not guaranteed"
# is a risk warning, not an unsafe promise.
NEGATION_PATTERN = re.compile(
    r"\b(?:not|never|cannot|can't|isn't|aren't|"
    r"won't|will not|is not|are not|no)\s+"
    r"(?:necessarily\s+)?$",
    re.IGNORECASE,
)

FINANCIAL_CONTEXT_KEYWORDS = re.compile(
    r"\b(?:income|salary|expense|expenses|surplus|deficit|"
    r"savings|investment|investments|portfolio|capital|"
    r"returns?|profit|profits|loss|losses|sip|emi|"
    r"contribution|allocation|budget|cash flow|"
    r"monthly investment|annual income|savings rate|"
    r"expense ratio|financial goal|target amount)\b",
    re.IGNORECASE,
)

NUMBER_PATTERN = re.compile(
    r"(?<![\w.])"
    r"(?:₹\s*|INR\s*|Rs\.?\s*)?"
    r"(\d[\d,]*(?:\.\d+)?)"
    r"\s*(lakh|lakhs|lac|crore|crores|cr|k)?"
    r"\s*(%)?",
    re.IGNORECASE,
)

DURATION_SUFFIX = re.compile(
    r"^\s*(?:years?|months?|weeks?|days?)\b",
    re.IGNORECASE,
)

NUMBER_MULTIPLIERS = {
    "k": Decimal("1000"),
    "lakh": Decimal("100000"),
    "lakhs": Decimal("100000"),
    "lac": Decimal("100000"),
    "crore": Decimal("10000000"),
    "crores": Decimal("10000000"),
    "cr": Decimal("10000000"),
}


def _extract_financial_numbers(text: str) -> list[Decimal]:
    """Extract currency, percentage and financial-scale numbers."""
    values = []
    for match in NUMBER_PATTERN.finditer(text):
        suffix = match.group(2)
        is_percentage = bool(match.group(3))

        # Avoid interpreting ordinary time periods as financial values.
        if not suffix and not is_percentage:
            following_text = text[match.end():]
            if DURATION_SUFFIX.search(following_text):
                continue

            # Ignore unqualified numbers unless they are clearly
            # presented as currency.
            matched_text = match.group(0)
            if not re.match(
                r"\s*(?:₹|INR|Rs\.?)",
                matched_text,
                re.IGNORECASE,
            ):
                continue

        try:
            value = Decimal(match.group(1).replace(",", ""))
            if suffix:
                value *= NUMBER_MULTIPLIERS[suffix.lower()]
            values.append(value)
        except (InvalidOperation, KeyError):
            continue

    return values


def _is_negated(text: str, match_start: int) -> bool:
    preceding_text = text[max(0, match_start - 40):match_start]
    return bool(NEGATION_PATTERN.search(preceding_text))


def _collect_narrative_text(
    response: AIAdvisorGenerationResponse,
) -> list[str]:
    """Collect all user-facing generated narrative fields."""

    texts = [
        response.overall_assessment,
        *response.key_findings,
        *response.risk_considerations,
        *response.assumptions,
        *response.limitations,
    ]

    for recommendation in response.recommendations:
        texts.extend([
            recommendation.title,
            recommendation.explanation,
            recommendation.suggested_action,
        ])

    return texts


def _validate_risk_language(
    response: AIAdvisorGenerationResponse,
) -> None:
    """Reject misleading investment certainty or safety claims."""

    for text in _collect_narrative_text(response):
        for pattern in UNSAFE_FINANCIAL_PATTERNS:
            for match in pattern.finditer(text):
                if _is_negated(text, match.start()):
                    continue

                raise AdvisorOutputValidationError(
                    "Advisor response contains potentially misleading "
                    "investment certainty or risk-free language."
                )


def _validate_numerical_claim_coverage(
    response: AIAdvisorGenerationResponse,
) -> None:
    """Ensure financial numbers mentioned in the narrative are declared in financial_claims."""
    declared_values = {
        claim.claimed_value
        for claim in response.financial_claims
    }

    for text in _collect_narrative_text(response):
        for match in re.finditer(r"[^.!?\n]+[.!?\n]?", text):
            sentence = match.group(0)
            if not FINANCIAL_CONTEXT_KEYWORDS.search(sentence):
                continue

            extracted_numbers = _extract_financial_numbers(sentence)
            for num in extracted_numbers:
                if not any(
                    abs(num - declared) <= Decimal("0.01")
                    for declared in declared_values
                ):
                    raise AdvisorOutputValidationError(
                        f"Financial number {num} mentioned in explanation "
                        "is not declared in financial claims."
                    )


def _build_missing_data_disclosures(
    financial_context: FinancialContext,
) -> list[str]:
    """Build deterministic disclosures from unavailable context."""

    disclosures: list[str] = []

    profile = getattr(financial_context, "profile", None)
    if profile is None:
        disclosures.append(
            "Investor profile information was unavailable. "
            "Personalized analysis may therefore be limited."
        )
    else:
        profile_fields = {
            "age": "age",
            "monthly_income": "monthly income",
            "monthly_expenses": "monthly expenses",
            "savings": "savings",
            "existing_investments": "existing investments",
            "monthly_investment_capacity": "monthly investment capacity",
        }

        missing_profile_fields = [
            description
            for attribute, description in profile_fields.items()
            if getattr(profile, attribute, None) is None
        ]

        if missing_profile_fields:
            disclosures.append(
                "The following investor profile details were unavailable: "
                + ", ".join(missing_profile_fields)
                + "."
            )

    if getattr(financial_context, "risk_assessment", None) is None:
        disclosures.append(
            "No risk assessment was available. "
            "The investor's risk tolerance has not been established."
        )

    if not getattr(financial_context, "goals", None):
        disclosures.append(
            "No financial goals were available. "
            "Goal-specific planning could not be performed."
        )

    metric_fields = {
        "monthly_surplus": "monthly surplus",
        "annual_income": "annual income",
        "annual_expenses": "annual expenses",
        "savings_rate_percent": "savings rate",
        "expense_ratio_percent": "expense ratio",
    }

    metrics = getattr(financial_context, "metrics", None)
    if metrics is not None:
        missing_metrics = [
            description
            for attribute, description in metric_fields.items()
            if getattr(metrics, attribute, None) is None
        ]

        if missing_metrics:
            disclosures.append(
                "The following financial metrics could not be calculated "
                "from the available information: "
                + ", ".join(missing_metrics)
                + "."
            )

    if not getattr(financial_context, "documents", None):
        disclosures.append(
            "No indexed financial documents were available. "
            "Document-based analysis could not be performed."
        )

    return disclosures


def validate_and_enforce_advisor_output(
    response: AIAdvisorGenerationResponse,
    financial_context: FinancialContext,
) -> AIAdvisorGenerationResponse:
    """
    Validate generated advisor output and add deterministic
    disclosures for missing financial information.

    Returns a validated generation response.
    Raises AdvisorOutputValidationError for unsafe output.
    """

    _validate_risk_language(response)
    _validate_numerical_claim_coverage(response)

    disclosures = _build_missing_data_disclosures(
        financial_context
    )

    limitations = list(response.limitations)

    existing = {
        limitation.strip().casefold()
        for limitation in limitations
    }

    for disclosure in disclosures:
        if disclosure.casefold() not in existing:
            limitations.append(disclosure)
            existing.add(disclosure.casefold())

    if len(limitations) > 10:
        raise AdvisorOutputValidationError(
            "Too many limitations and missing-data disclosures "
            "to construct a valid advisor response."
        )

    risk_considerations = list(response.risk_considerations)

    if not risk_considerations:
        risk_considerations.append(
            "Investment values and returns are uncertain. "
            "Actual outcomes may differ from expectations, "
            "and investors may lose some or all of their capital."
        )

    updated_data = response.model_dump(mode="python")
    updated_data["limitations"] = limitations
    updated_data["risk_considerations"] = risk_considerations

    return AIAdvisorGenerationResponse.model_validate(updated_data)
