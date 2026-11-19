from decimal import Decimal, InvalidOperation
import logging
import re

from app.schemas.ai_advisor import AIAdvisorGenerationResponse
from app.schemas.financial_context import FinancialContext
from app.services.plain_language_service import annotate_advisor_generation_response

logger = logging.getLogger(__name__)


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
        r"\bno\s+risk\b(?!\s+(?:tolerance|appetite|capacity|preference|profile|cushion|buffer))",
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

# A negated statement such as "returns are not guaranteed" or exclusion in suitability
# is a risk warning, not an unsafe promise.
NEGATION_PATTERN = re.compile(
    r"\b(?:not|never|cannot|can't|isn't|aren't|won't|will not|is not|are not|no|without|neither|nor|unsuitable|not\s+suitable|avoid|seeking|requiring|preferring|desiring|demanding|does\s+not|do\s+not|did\s+not|doesn't|don't|unlike|free\s+from|free\s+of|lack\s+of)\b(?:\s+[\w,-]+){0,6}\s*$",
    re.IGNORECASE,
)

FOLLOWING_NEGATION_PATTERN = re.compile(
    r"^\s*(?:are|is|will|can|could|do|does|may|might|should)?\s*(?:not|never|cannot|can't|neither|barely|unlikely|impossible|absent|non[- ]existent|unavailable)\b",
    re.IGNORECASE,
)

SOVEREIGN_STATUTORY_PATTERN = re.compile(
    r"\b(?:ppf|public\s+provident\s+fund|epf|vpf|g-sec|gsec|sovereign|government|govt|statutory|dicgc|deposit\s+insurance|rbi|post\s+office|postal|nsc|scss|sukanya)\b",
    re.IGNORECASE,
)

MARKET_INSTRUMENT_PATTERN = re.compile(
    r"\b(?:equity|equities|stock|stocks|mutual\s+fund|mutual\s+funds|portfolio|crypto|index\s+fund|index\s+funds|etf|etfs|market)\b",
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

PERCENTAGE_METRIC_PRECEDING = re.compile(
    r"\b(?:savings?\s*rate|expense\s*ratio)\b(?:\s+(?:of|is|at|was|around|approximately|approx\.?|standing\s+at|:|=))?\s*$",
    re.IGNORECASE,
)
PERCENTAGE_METRIC_FOLLOWING = re.compile(
    r"^\s*(?:savings?\s*rate|expense\s*ratio)\b",
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


def _extract_financial_number_spans(
    text: str,
) -> list[tuple[Decimal, int, int, bool]]:
    """Extract (value, start, end, is_percentage) for currency, percentage, and financial-scale numbers."""
    results: list[tuple[Decimal, int, int, bool]] = []
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

        # Ignore percentages unless directly expressing tracked financial metrics (savings rate, expense ratio).
        if is_percentage:
            preceding_context = text[max(0, match.start() - 35):match.start()]
            following_context = text[match.end():min(len(text), match.end() + 25)]
            if not PERCENTAGE_METRIC_PRECEDING.search(preceding_context) and not PERCENTAGE_METRIC_FOLLOWING.search(following_context):
                continue

        try:
            value = Decimal(match.group(1).replace(",", ""))
            if suffix:
                value *= NUMBER_MULTIPLIERS[suffix.lower()]
            results.append((value, match.start(), match.end(), is_percentage))
        except (InvalidOperation, KeyError):
            continue

    return results


def _extract_financial_numbers(text: str) -> list[Decimal]:
    """Extract currency, percentage and financial-scale numbers."""
    return [val for val, _, _, _ in _extract_financial_number_spans(text)]


def _is_negated(text: str, match_start: int, match_end: int | None = None) -> bool:
    """Check if the matched phrase is qualified or negated preceding or following it."""
    # 1. Preceding negation: e.g. "returns are not guaranteed", "unsuitable for investors requiring guaranteed income"
    preceding_text = text[max(0, match_start - 80):match_start]
    if NEGATION_PATTERN.search(preceding_text):
        return True

    # 2. Following negation: e.g. "Guaranteed returns are not available", "Risk-free investing does not exist"
    if match_end is not None:
        following_text = text[match_end:min(len(text), match_end + 50)]
        if FOLLOWING_NEGATION_PATTERN.search(following_text):
            return True

    return False


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
                if _is_negated(text, match.start(), match.end()):
                    continue

                # Check if this sentence is strictly describing a statutory sovereign scheme
                # (e.g. PPF, Government of India backed, DICGC bank deposit insurance)
                # without asserting market certainty.
                sentence_start = max(0, text.rfind(".", 0, match.start()) + 1)
                sentence_end = text.find(".", match.end())
                if sentence_end == -1:
                    sentence_end = len(text)
                sentence = text[sentence_start:sentence_end]

                if SOVEREIGN_STATUTORY_PATTERN.search(sentence) and not MARKET_INSTRUMENT_PATTERN.search(sentence):
                    # Statutory guarantee or capital protection for sovereign instruments is accurate
                    continue

                logger.warning(
                    "Advisor risk language violation: pattern '%s' matched '%s' in context '%s'",
                    pattern.pattern,
                    match.group(0),
                    text[max(0, match.start() - 50):min(len(text), match.end() + 50)],
                )
                raise AdvisorOutputValidationError(
                    "Advisor response contains potentially misleading "
                    "investment certainty or risk-free language."
                )


SENTENCE_PATTERN = re.compile(
    r"(?:[^\n.!?]|(?<=\d)\.(?=\d)|(?<=\bRs)\.|(?<=\bINR)\.)+[.!?\n]?",
    re.IGNORECASE,
)

STATUTORY_BENCHMARK_KEYWORDS = re.compile(
    r"\b(?:ppf|80c|80ccd|80d|24|24b|24\(b\)|ltcg|stcg|tax|exemption|deduction|rebate|dicgc|insurance|deposit\s+insurance|minimum\s+sip|micro\s+sip|ceiling|limit|slab|corpus|buffer|reserve|emergency|contingency|benchmark|threshold|lump\s*sum|target)\b",
    re.IGNORECASE,
)

STATUTORY_FINANCIAL_BENCHMARKS = {
    Decimal("150000"),  # Section 80C / PPF annual ceiling
    Decimal("200000"),  # Section 24(b) home loan interest deduction ceiling / ₹2 Lakh emergency corpus
    Decimal("50000"),   # Section 80CCD(1B) NPS additional ceiling / standard deduction
    Decimal("125000"),  # Equity LTCG annual exemption threshold
    Decimal("100000"),  # Previous LTCG threshold / 80D max family
    Decimal("250000"),  # Basic tax exemption limit (old regime)
    Decimal("300000"),  # New regime basic exemption limit
    Decimal("500000"),  # DICGC deposit insurance limit (₹5 Lakh)
    Decimal("700000"),  # Section 87A rebate ceiling in new tax regime (₹7 Lakh)
    Decimal("25000"),   # 80D individual
    Decimal("75000"),   # Standard deduction / 80D senior citizen
    Decimal("12500"),   # Monthly PPF maximum (150000 / 12)
    Decimal("500"),     # Standard minimum SIP
    Decimal("100"),     # Micro-SIP minimum
    Decimal("1000"),    # Common minimum investment
}

PERSONAL_METRIC_ASSERTION = re.compile(
    r"\b(?:"
    r"monthly\s+surplus|surplus\s+is|surplus\s+of|"
    r"annual\s+income|yearly\s+income|monthly\s+income|income\s+is|income\s+of|"
    r"annual\s+expenses|yearly\s+expenses|monthly\s+expenses|expenses\s+are|expenses\s+of|"
    r"current\s+savings|savings\s+of|savings\s+are|existing\s+investments|"
    r"investment\s+capacity|capacity\s+of|capacity\s+is|"
    r"savings\s+rate|expense\s+ratio"
    r")\b",
    re.IGNORECASE,
)

SURPLUS_OR_INCOME_ASSERTION = PERSONAL_METRIC_ASSERTION


DIRECT_METRIC_PRECEDING = re.compile(
    r"\b(?:"
    r"monthly\s+surplus|surplus|"
    r"annual\s+income|yearly\s+income|monthly\s+income|"
    r"annual\s+expenses|yearly\s+expenses|monthly\s+expenses|"
    r"current\s+savings|existing\s+investments|"
    r"monthly\s+investment\s+capacity|investment\s+capacity|"
    r"savings\s+rate|expense\s+ratio"
    r")\b(?:\s+(?:is|are|was|were|of|at|stands?\s+at|equals?|around|approx\.?|approximately|:|=))?\s*$",
    re.IGNORECASE,
)


def _matches_financial_value(
    num: Decimal,
    target: Decimal,
    is_percentage: bool = False,
) -> bool:
    """Compare extracted financial numbers with realistic rounding tolerance."""
    if is_percentage:
        return abs(num - target) <= Decimal("0.5")
    if abs(target) >= Decimal("100"):
        return abs(num - target) <= Decimal("1.00")
    return abs(num - target) <= Decimal("0.01")


def _validate_numerical_claim_coverage(
    response: AIAdvisorGenerationResponse,
    financial_context: FinancialContext | None = None,
    user_query: str | None = None,
) -> None:
    """Ensure financial numbers mentioned in the narrative are declared in financial_claims or verified context."""
    valid_values = {
        claim.claimed_value
        for claim in response.financial_claims
    }

    if user_query:
        for num in _extract_financial_numbers(user_query):
            valid_values.add(num)

    max_monthly_available = Decimal("0")

    if financial_context is not None:
        surplus = getattr(financial_context.metrics, "monthly_surplus", None)
        capacity = getattr(financial_context.profile, "monthly_investment_capacity", None) if financial_context.profile else None

        if surplus is not None:
            max_monthly_available = max(max_monthly_available, surplus)
        if capacity is not None:
            max_monthly_available = max(max_monthly_available, capacity)

        savings_val = getattr(financial_context.profile, "savings", None) if financial_context.profile else None
        investments_val = getattr(financial_context.profile, "existing_investments", None) if financial_context.profile else None

        if financial_context.profile is not None:
            for attr in (
                "monthly_income",
                "monthly_expenses",
                "savings",
                "existing_investments",
                "monthly_investment_capacity",
            ):
                val = getattr(financial_context.profile, attr, None)
                if val is not None:
                    valid_values.add(val)

            # Emergency fund multiples (1 to 12 months of expenses)
            if financial_context.profile.monthly_expenses is not None:
                for k in range(1, 13):
                    valid_values.add(financial_context.profile.monthly_expenses * Decimal(k))

            # Annual income multiples for life cover (1 to 15 times)
            if financial_context.profile.monthly_income is not None:
                ann_inc = financial_context.profile.monthly_income * Decimal("12")
                valid_values.add(ann_inc)
                for k in range(1, 16):
                    valid_values.add(ann_inc * Decimal(k))

        if financial_context.metrics is not None:
            for attr in (
                "monthly_surplus",
                "annual_income",
                "annual_expenses",
                "savings_rate_percent",
                "expense_ratio_percent",
            ):
                val = getattr(financial_context.metrics, attr, None)
                if val is not None:
                    valid_values.add(val)

        for goal in financial_context.goals:
            if goal.target_amount is not None:
                valid_values.add(goal.target_amount)
                # Goal net target remaining after current assets
                if savings_val is not None:
                    valid_values.add(goal.target_amount - savings_val)
                    valid_values.add(max(Decimal("0"), goal.target_amount - savings_val))
                if investments_val is not None:
                    valid_values.add(goal.target_amount - investments_val)
                    valid_values.add(max(Decimal("0"), goal.target_amount - investments_val))
                if savings_val is not None and investments_val is not None:
                    valid_values.add(goal.target_amount - (savings_val + investments_val))
                    valid_values.add(max(Decimal("0"), goal.target_amount - (savings_val + investments_val)))
            if goal.planned_monthly_investment is not None:
                valid_values.add(goal.planned_monthly_investment)
                if goal.time_horizon_months:
                    valid_values.add(goal.planned_monthly_investment * Decimal(goal.time_horizon_months))

        total_goal_required = Decimal("0")
        for goal_analysis in financial_context.goal_analysis:
            if goal_analysis.required_monthly_contribution is not None:
                valid_values.add(goal_analysis.required_monthly_contribution)
                total_goal_required += goal_analysis.required_monthly_contribution
            if goal_analysis.planned_monthly_investment is not None:
                valid_values.add(goal_analysis.planned_monthly_investment)
            if goal_analysis.monthly_contribution_shortfall is not None:
                valid_values.add(goal_analysis.monthly_contribution_shortfall)

        # Derived surplus and capacity figures
        if surplus is not None:
            valid_values.add(surplus * Decimal("12"))  # Annualized surplus
            valid_values.add(surplus - total_goal_required)
            valid_values.add(max(Decimal("0"), surplus - total_goal_required))
        if capacity is not None:
            valid_values.add(capacity * Decimal("12"))  # Annualized capacity
            valid_values.add(capacity - total_goal_required)
            valid_values.add(max(Decimal("0"), capacity - total_goal_required))

        # Include numbers mentioned in indexed financial documents
        for doc in getattr(financial_context, "documents", []):
            excerpt = getattr(doc, "summary", "") or getattr(doc, "content", "")
            if excerpt:
                for doc_num in _extract_financial_numbers(excerpt):
                    valid_values.add(doc_num)

    for text in _collect_narrative_text(response):
        for match in SENTENCE_PATTERN.finditer(text):
            sentence = match.group(0)
            if not FINANCIAL_CONTEXT_KEYWORDS.search(sentence):
                continue

            extracted_spans = _extract_financial_number_spans(sentence)
            for num, start, end, is_percentage in extracted_spans:
                # 1. Matches declared claims, verified context figures, or derived totals (with rounding tolerance)
                if any(
                    _matches_financial_value(num, declared, is_percentage=is_percentage)
                    for declared in valid_values
                ):
                    continue

                # Check ONLY the immediate local phrase around THIS specific number so
                # mentioning e.g. "monthly surplus" earlier in a sentence does not taint
                # other numbers like allocations or goal targets later in the same sentence.
                local_before = sentence[max(0, start - 45):start]
                local_after = sentence[end:min(len(sentence), end + 30)]
                is_direct_metric_claim = bool(
                    DIRECT_METRIC_PRECEDING.search(local_before)
                    or (
                        is_percentage
                        and (
                            PERCENTAGE_METRIC_PRECEDING.search(local_before)
                            or PERCENTAGE_METRIC_FOLLOWING.search(local_after)
                        )
                    )
                )

                # 2. Statutory / regulatory benchmarks mentioned in context
                if (
                    STATUTORY_BENCHMARK_KEYWORDS.search(sentence)
                    and not is_direct_metric_claim
                    and any(
                        _matches_financial_value(num, benchmark, is_percentage=False)
                        for benchmark in STATUTORY_FINANCIAL_BENCHMARKS
                    )
                ):
                    continue

                # 3. Actionable monthly investment allocation bounded by user surplus/capacity
                if (
                    financial_context is not None
                    and max_monthly_available > 0
                    and Decimal("0") < num <= max_monthly_available
                    and not is_direct_metric_claim
                ):
                    continue

                # 4. If verified financial context is present and THIS specific number is NOT
                # directly asserting a personal balance-sheet metric, permit explanatory figures safely.
                if (
                    financial_context is not None
                    and not is_direct_metric_claim
                ):
                    logger.debug(
                        "Permitting non-personal metric financial figure %s in explanation: %s",
                        num,
                        sentence,
                    )
                    continue

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
    _validate_numerical_claim_coverage(
        response=response,
        financial_context=financial_context,
    )

    # Annotate financial jargon with plain-English bracketed definitions after AI generation
    response = annotate_advisor_generation_response(response)

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
