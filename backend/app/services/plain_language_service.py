"""Plain-language prompt guidelines and post-processing glossary annotator.

Ensures every AI-generated financial report across the platform (AI Advisor,
Investment Comparison, Scenario Simulator, Autonomous Research Agent, and
Analysis History Diff) is written in clear, beginner-friendly language and
automatically explains unfamiliar financial/tax terms in brackets right after
their first appearance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

PLAIN_LANGUAGE_COMMUNICATION_RULES = """PLAIN-LANGUAGE & CLARITY RULES (MANDATORY):
1. Write in simple, clear, everyday English so that even a beginner investor can immediately understand what the analysis means for their money and what steps to take next.
2. Avoid dense banking or Wall Street jargon. Explain the practical meaning of numbers and recommendations in plain words.
3. Whenever you introduce a financial, investment, or tax term for the first time (such as SIP, PPF, ELSS, LTCG, STCG, Expense Ratio, Asset Allocation, Rebalancing, CAGR, Liquidity, Volatility, Inflation, Compounding, Corpus, Drawdown, DICGC, Index Fund, Debt Fund, Section 80C, Section 24(b), Lock-in, Sovereign-backed, NAV, Exit Load, Diversification), immediately write its simple meaning in brackets right after it: for example: "SIP (Systematic Investment Plan: investing a fixed amount regularly every month)" or "Expense Ratio (the small yearly fee a fund charges to manage your money)".
4. Define each term only once (on its first mention) so the report stays clean, friendly, and easy to read."""


@dataclass(frozen=True)
class _GlossaryTerm:
    pattern: str
    concept_id: str
    definition: str
    case_sensitive: bool = False


# Ordered from most specific / longest multi-word phrases to shorter terms.
# Definitions are concise, beginner-friendly, and free of prohibited certainty language.
_GLOSSARY_TERMS: tuple[_GlossaryTerm, ...] = (
    # Multi-word Indian & personal finance concepts
    _GlossaryTerm(
        r"Systematic\s+Investment\s+Plan",
        "sip",
        "investing a fixed amount regularly, usually every month",
    ),
    _GlossaryTerm(
        r"Public\s+Provident\s+Fund",
        "ppf",
        "a long-term government-backed tax-saving account",
    ),
    _GlossaryTerm(
        r"National\s+Pension\s+System",
        "nps",
        "a government-regulated retirement savings scheme",
    ),
    _GlossaryTerm(
        r"Equity\s+Linked\s+Savings\s+Scheme",
        "elss",
        "a tax-saving stock mutual fund with a 3-year lock-in",
    ),
    _GlossaryTerm(
        r"Sovereign\s+Gold\s+Bonds?",
        "sgb",
        "government-issued bonds linked to gold prices",
    ),
    _GlossaryTerm(
        r"Long[- ]Term\s+Capital\s+Gains?",
        "ltcg",
        "profit from selling an investment held for the long term",
    ),
    _GlossaryTerm(
        r"Short[- ]Term\s+Capital\s+Gains?",
        "stcg",
        "profit from selling an investment held for a short period",
    ),
    _GlossaryTerm(
        r"Section\s+80CCD\(1B\)",
        "sec_80ccd1b",
        "an income tax rule offering an extra deduction for NPS retirement contributions",
    ),
    _GlossaryTerm(
        r"Section\s+80C",
        "sec_80c",
        "an income tax rule that lowers taxable income for eligible savings like PPF and ELSS",
    ),
    _GlossaryTerm(
        r"Section\s+80D",
        "sec_80d",
        "an income tax rule offering deductions for health insurance premiums",
    ),
    _GlossaryTerm(
        r"Section\s+24\(b\)",
        "sec_24b",
        "an income tax rule allowing deductions on home loan interest",
    ),
    _GlossaryTerm(
        r"Section\s+87A",
        "sec_87a",
        "an income tax rebate that reduces tax payable for eligible income slabs",
    ),
    _GlossaryTerm(
        r"Rupee\s+Cost\s+Averaging",
        "rupee_cost_averaging",
        "buying more units when prices dip and fewer when prices rise through regular investing",
    ),
    _GlossaryTerm(
        r"Tax[- ]Loss\s+Harvesting",
        "tax_loss_harvesting",
        "selling losing investments to offset taxes on your other gains",
    ),
    _GlossaryTerm(
        r"Expense\s+Ratio",
        "expense_ratio",
        "the small yearly fee a mutual fund charges to manage your money",
    ),
    _GlossaryTerm(
        r"Asset\s+Allocation",
        "asset_allocation",
        "how your money is divided across growth assets like stocks and steadier assets like bonds",
    ),
    _GlossaryTerm(
        r"Index\s+Funds?",
        "index_fund",
        "a low-cost fund that tracks a broad stock market index like Nifty 50",
    ),
    _GlossaryTerm(
        r"Debt\s+Funds?",
        "debt_fund",
        "a mutual fund that invests mainly in steadier bonds and fixed-income securities",
    ),
    _GlossaryTerm(
        r"Liquid\s+Funds?",
        "liquid_fund",
        "a short-term, low-volatility fund built for quick access to cash",
    ),
    _GlossaryTerm(
        r"Hybrid\s+Funds?",
        "hybrid_fund",
        "a fund that mixes stocks for growth and bonds for stability",
    ),
    _GlossaryTerm(
        r"Equity\s+Funds?",
        "equity_fund",
        "a mutual fund that mainly invests in company shares for long-term growth",
    ),
    _GlossaryTerm(
        r"Exit\s+Load",
        "exit_load",
        "a small fee charged if you withdraw from a mutual fund too early",
    ),
    _GlossaryTerm(
        r"Lock[- ]in\s+Period",
        "lock_in",
        "a fixed waiting period during which you cannot withdraw your money",
    ),
    _GlossaryTerm(
        r"Lock[- ]in",
        "lock_in",
        "a fixed waiting period before you can withdraw your money",
    ),
    _GlossaryTerm(
        r"Capital\s+Gains?",
        "capital_gains",
        "profit made when you sell an investment for more than you paid",
    ),
    _GlossaryTerm(
        r"Real\s+Returns?",
        "real_return",
        "your investment return after subtracting the effect of inflation",
    ),
    _GlossaryTerm(
        r"Sovereign[- ]backed",
        "sovereign",
        "backed directly by the central government",
    ),
    _GlossaryTerm(
        r"Nifty\s+50",
        "nifty_50",
        "an index tracking India's 50 largest listed companies",
    ),
    _GlossaryTerm(
        r"Sensex",
        "sensex",
        "an index tracking 30 major companies on the Bombay Stock Exchange",
    ),
    # Acronyms (strictly case-sensitive so ordinary lowercase words are never matched)
    _GlossaryTerm(
        r"SIP",
        "sip",
        "Systematic Investment Plan: investing a fixed amount regularly every month",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"PPF",
        "ppf",
        "Public Provident Fund: a long-term government-backed tax-saving account",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"EPF",
        "epf",
        "Employees' Provident Fund: a retirement savings account for salaried employees",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"VPF",
        "vpf",
        "Voluntary Provident Fund: extra voluntary savings added to your EPF account",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"NPS",
        "nps",
        "National Pension System: a government-regulated retirement savings scheme",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"ELSS",
        "elss",
        "Equity Linked Savings Scheme: a tax-saving stock mutual fund with a 3-year lock-in",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"LTCG",
        "ltcg",
        "Long-Term Capital Gains: tax on profits from investments held for the long term",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"STCG",
        "stcg",
        "Short-Term Capital Gains: tax on profits from investments sold quickly",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"CAGR",
        "cagr",
        "Compound Annual Growth Rate: the average yearly growth rate of an investment",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"XIRR",
        "xirr",
        "Extended Internal Rate of Return: your true yearly return across multiple investment dates",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"DICGC",
        "dicgc",
        "Deposit Insurance and Credit Guarantee Corporation: the RBI body that insures bank deposits",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"SGB",
        "sgb",
        "Sovereign Gold Bond: a government-issued bond linked to gold prices",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"ETF",
        "etf",
        "Exchange-Traded Fund: a basket of stocks or bonds traded live on the stock market",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"FD",
        "fd",
        "Fixed Deposit: a bank deposit earning a fixed interest rate for a chosen period",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"RD",
        "rd",
        "Recurring Deposit: a bank deposit where you save a fixed amount every month",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"NAV",
        "nav",
        "Net Asset Value: the current price of one unit of a mutual fund",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"AUM",
        "aum",
        "Assets Under Management: the total investor money managed by a fund",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"EMI",
        "emi",
        "Equated Monthly Installment: the fixed monthly payment toward a loan",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"G-Sec",
        "gsec",
        "Government Security: a bond issued directly by the government",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"SWP",
        "swp",
        "Systematic Withdrawal Plan: withdrawing a fixed amount regularly from your investments",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"STP",
        "stp",
        "Systematic Transfer Plan: automatically shifting money regularly from one fund to another",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"TER",
        "expense_ratio",
        "Total Expense Ratio: the yearly fee a mutual fund charges to manage your money",
        case_sensitive=True,
    ),
    _GlossaryTerm(
        r"IDCW",
        "idcw",
        "Income Distribution cum Capital Withdrawal: periodic payouts distributed by a mutual fund",
        case_sensitive=True,
    ),
    # Single-word technical financial terms
    _GlossaryTerm(
        r"Compounding",
        "compounding",
        "earning returns not just on your original money, but also on past returns over time",
    ),
    _GlossaryTerm(
        r"Diversification",
        "diversification",
        "spreading your money across different investments so one drop does not hurt everything",
    ),
    _GlossaryTerm(
        r"Rebalancing",
        "rebalancing",
        "periodically adjusting your investments back to your planned mix of stocks and safer assets",
    ),
    _GlossaryTerm(
        r"Liquidity",
        "liquidity",
        "how quickly and easily you can turn an investment back into cash",
    ),
    _GlossaryTerm(
        r"Volatility",
        "volatility",
        "how sharply an investment's price moves up and down over time",
    ),
    _GlossaryTerm(
        r"Inflation",
        "inflation",
        "the gradual rise in everyday prices that reduces what your money can buy over time",
    ),
    _GlossaryTerm(
        r"Drawdown",
        "drawdown",
        "a temporary peak-to-bottom dip in an investment's value during market declines",
    ),
    _GlossaryTerm(
        r"Corpus",
        "corpus",
        "the total pool of money you build up for a goal",
    ),
    _GlossaryTerm(
        r"Equities",
        "equity",
        "company shares that offer higher long-term growth potential along with market ups and downs",
    ),
    _GlossaryTerm(
        r"Equity",
        "equity",
        "ownership shares in companies, offering higher growth potential with market ups and downs",
    ),
    _GlossaryTerm(
        r"Arbitrage",
        "arbitrage",
        "a low-volatility strategy that profits from small price differences across markets",
    ),
)

# Build one combined regex with named groups so a single left-to-right pass
# matches longest phrases first and never re-scans inserted definitions.
_GROUP_TO_TERM: dict[str, _GlossaryTerm] = {}
_REGEX_BRANCHES: list[str] = []

for _idx, _term in enumerate(_GLOSSARY_TERMS):
    _group_name = f"t{_idx}"
    _GROUP_TO_TERM[_group_name] = _term
    if _term.case_sensitive:
        _REGEX_BRANCHES.append(f"(?P<{_group_name}>\\b{_term.pattern}\\b)")
    else:
        _REGEX_BRANCHES.append(f"(?P<{_group_name}>(?i:\\b{_term.pattern}\\b))")

_COMBINED_GLOSSARY_PATTERN = re.compile("|".join(_REGEX_BRANCHES))
_FOLLOWING_PAREN_PATTERN = re.compile(r"^\s*\(")


def _paren_depths(text: str) -> list[int]:
    """Compute parenthesis nesting depth at each character position."""
    depths: list[int] = []
    depth = 0
    for ch in text:
        depths.append(depth)
        if ch == "(":
            depth += 1
        elif ch == ")" and depth > 0:
            depth -= 1
    return depths


def annotate_financial_terms(
    text: str,
    seen_concepts: set[str] | None = None,
    max_length: int | None = None,
) -> str:
    """Append beginner-friendly bracketed definitions on the first occurrence of financial terms.

    - Skips any term already followed by a parenthetical explanation `(...)`.
    - Skips any match inside existing parentheses so nested brackets never occur.
    - Tracks `seen_concepts` across calls so each concept is explained only once per report.
    - Respects `max_length` so Pydantic string length limits are never exceeded.
    """
    if not text or not isinstance(text, str):
        return text

    if seen_concepts is None:
        seen_concepts = set()

    depths = _paren_depths(text)
    pieces: list[str] = []
    last_idx = 0
    current_len = len(text)

    for match in _COMBINED_GLOSSARY_PATTERN.finditer(text):
        start, end = match.span()
        group_name = match.lastgroup
        if not group_name:
            continue

        term = _GROUP_TO_TERM[group_name]

        # Skip terms inside existing parentheses (e.g. "(PPF)" or "(Systematic Investment Plan)")
        if depths[start] > 0:
            seen_concepts.add(term.concept_id)
            continue

        # If already explained by the AI with a bracket immediately after, mark seen and skip
        if _FOLLOWING_PAREN_PATTERN.match(text[end:]):
            seen_concepts.add(term.concept_id)
            continue

        # Only explain each concept once per report
        if term.concept_id in seen_concepts:
            continue

        addition = f" ({term.definition})"
        if max_length is not None and (current_len + len(addition)) > max_length:
            continue

        pieces.append(text[last_idx:end])
        pieces.append(addition)
        last_idx = end
        current_len += len(addition)
        seen_concepts.add(term.concept_id)

    if not pieces:
        return text

    pieces.append(text[last_idx:])
    return "".join(pieces)


def annotate_string_list(
    items: list[str],
    seen_concepts: set[str],
    max_length: int | None = None,
) -> list[str]:
    """Annotate a list of narrative strings sharing the same seen_concepts tracker."""
    return [
        annotate_financial_terms(item, seen_concepts=seen_concepts, max_length=max_length)
        for item in items
    ]


def annotate_advisor_generation_response(response: Any) -> Any:
    """Annotate financial terms across an AIAdvisorGenerationResponse."""
    seen: set[str] = set()
    data = response.model_dump(mode="python")

    data["overall_assessment"] = annotate_financial_terms(
        data["overall_assessment"], seen_concepts=seen, max_length=2000
    )
    data["key_findings"] = annotate_string_list(data["key_findings"], seen_concepts=seen)

    for rec in data.get("recommendations", []):
        rec["explanation"] = annotate_financial_terms(
            rec["explanation"], seen_concepts=seen, max_length=1500
        )
        rec["suggested_action"] = annotate_financial_terms(
            rec["suggested_action"], seen_concepts=seen, max_length=1000
        )

    data["risk_considerations"] = annotate_string_list(
        data.get("risk_considerations", []), seen_concepts=seen
    )
    data["assumptions"] = annotate_string_list(
        data.get("assumptions", []), seen_concepts=seen
    )
    data["limitations"] = annotate_string_list(
        data.get("limitations", []), seen_concepts=seen
    )

    return response.__class__.model_validate(data)


def annotate_comparison_explanation(explanation: Any) -> Any:
    """Annotate financial terms across an InvestmentComparisonExplanation."""
    seen: set[str] = set()
    data = explanation.model_dump(mode="python")

    data["summary"] = annotate_financial_terms(
        data["summary"], seen_concepts=seen, max_length=1500
    )
    data["key_differences"] = annotate_string_list(
        data.get("key_differences", []), seen_concepts=seen
    )

    for suit in data.get("suitability_analysis", []):
        suit["suitable_for"] = annotate_financial_terms(
            suit["suitable_for"], seen_concepts=seen, max_length=500
        )
        suit["unsuitable_for"] = annotate_financial_terms(
            suit["unsuitable_for"], seen_concepts=seen, max_length=500
        )
        suit["key_tradeoff"] = annotate_financial_terms(
            suit["key_tradeoff"], seen_concepts=seen, max_length=500
        )

    data["risk_tradeoffs"] = annotate_string_list(
        data.get("risk_tradeoffs", []), seen_concepts=seen
    )
    data["assumptions_and_missing_info"] = annotate_string_list(
        data.get("assumptions_and_missing_info", []), seen_concepts=seen
    )

    return explanation.__class__.model_validate(data)


def annotate_scenario_explanation(explanation: Any) -> Any:
    """Annotate financial terms across a ScenarioAIExplanation."""
    seen: set[str] = set()
    data = explanation.model_dump(mode="python")

    data["summary_narrative"] = annotate_financial_terms(
        data["summary_narrative"], seen_concepts=seen, max_length=1500
    )
    data["key_advantages"] = annotate_string_list(
        data.get("key_advantages", []), seen_concepts=seen
    )
    data["trade_offs_and_risks"] = annotate_string_list(
        data.get("trade_offs_and_risks", []), seen_concepts=seen
    )
    if data.get("goal_impact_analysis"):
        data["goal_impact_analysis"] = annotate_financial_terms(
            data["goal_impact_analysis"], seen_concepts=seen, max_length=1000
        )
    data["practical_next_steps"] = annotate_string_list(
        data.get("practical_next_steps", []), seen_concepts=seen
    )

    return explanation.__class__.model_validate(data)


def annotate_research_report(report: Any) -> Any:
    """Annotate financial terms across a ResearchReport."""
    seen: set[str] = set()
    data = report.model_dump(mode="python")

    data["summary"] = annotate_financial_terms(
        data["summary"], seen_concepts=seen, max_length=3500
    )
    data["key_findings"] = annotate_string_list(
        data.get("key_findings", []), seen_concepts=seen
    )
    data["risks_and_limitations"] = annotate_string_list(
        data.get("risks_and_limitations", []), seen_concepts=seen
    )
    # Sync frontend compatibility aliases with annotated fields
    data["executive_summary"] = data["summary"]
    data["synthesis"] = data["summary"]
    data["risk_factors"] = list(data["risks_and_limitations"])

    return report.__class__.model_validate(data)


def annotate_analysis_diff_explanation(explanation: Any) -> Any:
    """Annotate financial terms across an AnalysisDiffExplanation."""
    seen: set[str] = set()
    data = explanation.model_dump(mode="python")

    data["summary_narrative"] = annotate_financial_terms(
        data["summary_narrative"], seen_concepts=seen, max_length=1500
    )
    data["key_improvements"] = annotate_string_list(
        data.get("key_improvements", []), seen_concepts=seen
    )
    data["key_concerns"] = annotate_string_list(
        data.get("key_concerns", []), seen_concepts=seen
    )
    data["stale_recommendations"] = annotate_string_list(
        data.get("stale_recommendations", []), seen_concepts=seen
    )
    data["updated_strategic_focus"] = annotate_string_list(
        data.get("updated_strategic_focus", []), seen_concepts=seen
    )

    return explanation.__class__.model_validate(data)
