import logging
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.schemas.research_agent import EvidenceItem
from app.services.financial_calculation_service import (
    FinancialCalculationError,
    calculate_annual_expenses,
    calculate_annual_income,
    calculate_expense_ratio,
    calculate_future_value_lumpsum,
    calculate_future_value_sip,
    calculate_goal_shortfall,
    calculate_monthly_surplus,
    calculate_required_monthly_contribution,
    calculate_required_monthly_sip,
    calculate_savings_rate,
)
from app.services.retrieval_pipeline_service import retrieve_and_rerank

logger = logging.getLogger(__name__)

# Curated financial knowledge repository for approved financial facts and tax rules
APPROVED_FINANCIAL_KNOWLEDGE: list[dict[str, Any]] = [
    {
        "keywords": ["ppf", "public provident fund", "provident fund"],
        "title": "Public Provident Fund (PPF) Statutory Guidelines",
        "reference_id": "PPF_SCHEME_2019",
        "snippet": (
            "Public Provident Fund (PPF) is a government-backed 15-year small savings scheme. "
            "It enjoys EEE (Exempt-Exempt-Exempt) tax status: contributions qualify under Section 80C "
            "(up to ₹1.5 Lakh/financial year), interest earned is tax-exempt, and maturity proceeds are tax-free. "
            "Current benchmark interest is set quarterly by the Ministry of Finance (~7.1% p.a., compounded annually). "
            "Partial withdrawals are permitted from the 7th financial year."
        ),
    },
    {
        "keywords": ["fd", "fixed deposit", "term deposit", "bank deposit"],
        "title": "Bank Fixed Deposit (FD) Regulations & Taxation",
        "reference_id": "RBI_DICGC_FD_RULES",
        "snippet": (
            "Bank Fixed Deposits offer contractual, fixed interest returns for a defined tenure (7 days to 10 years). "
            "Under DICGC (Deposit Insurance and Credit Guarantee Corporation), each depositor in an insured bank "
            "is insured up to ₹5,00,000 (₹5 Lakh) for both principal and interest across all branches. "
            "Interest earned is fully taxable at the investor's applicable marginal income tax slab rate. "
            "TDS applies if annual interest exceeds ₹40,000 (₹50,000 for senior citizens)."
        ),
    },
    {
        "keywords": ["equity mutual fund", "mutual funds", "equity", "shares", "stocks", "ltcg", "stcg"],
        "title": "Equity Investments & Mutual Funds Tax Structure (Budget 2024)",
        "reference_id": "INCOME_TAX_EQUITY_2024",
        "snippet": (
            "Equity mutual funds invest at least 65% in domestic equities and offer market-linked returns without capital guarantees. "
            "Under Finance Act 2024 rules: Long-Term Capital Gains (LTCG) on equity held over 12 months are taxed at 12.5% "
            "for gains exceeding ₹1.25 Lakh per financial year. Short-Term Capital Gains (STCG) on equity held up to 12 months "
            "are taxed at 20%. Systematic Investment Plans (SIPs) allow dollar-cost averaging into equity funds."
        ),
    },
    {
        "keywords": ["debt mutual fund", "debt fund", "liquid fund", "bond"],
        "title": "Debt Mutual Funds & Fixed Income Taxation",
        "reference_id": "INCOME_TAX_DEBT_2023",
        "snippet": (
            "For debt mutual funds acquired on or after April 1, 2023 (with less than 35% equity exposure), "
            "capital gains are treated as short-term capital gains and taxed at the investor's applicable income tax slab rate, "
            "without indexation benefits. Liquid and ultra-short duration debt funds offer high liquidity for emergency reserves."
        ),
    },
    {
        "keywords": ["sgb", "sovereign gold bond", "gold"],
        "title": "Sovereign Gold Bonds (SGB) Framework",
        "reference_id": "RBI_SGB_SCHEME",
        "snippet": (
            "Sovereign Gold Bonds (SGBs) issued by the RBI on behalf of the Government of India offer an annual 2.5% fixed interest "
            "paid semi-annually on nominal value, plus redemption value linked to gold prices. Tenure is 8 years with early exit "
            "options after 5 years. Capital gains on redemption at maturity are 100% tax-free for individuals."
        ),
    },
    {
        "keywords": ["nps", "national pension system", "pension", "retirement"],
        "title": "National Pension System (NPS) Architecture",
        "reference_id": "PFRDA_NPS_GUIDELINES",
        "snippet": (
            "National Pension System (NPS) is a voluntary, long-term retirement savings scheme regulated by PFRDA. "
            "Offers an exclusive additional tax deduction of up to ₹50,000 under Section 80CCD(1B) beyond the ₹1.5 Lakh 80C cap. "
            "At superannuation (age 60), up to 60% of the accumulated corpus can be withdrawn tax-free as a lump sum; "
            "the remaining 40% must be used to purchase an annuity providing regular pension."
        ),
    },
    {
        "keywords": ["80c", "section 80c", "tax deduction", "tax saving"],
        "title": "Section 80C Income Tax Deductions",
        "reference_id": "INCOME_TAX_SEC_80C",
        "snippet": (
            "Section 80C of the Income Tax Act allows a maximum cumulative deduction of ₹1,50,000 per financial year from gross total income "
            "under the Old Tax Regime. Eligible avenues include EPF, PPF, ELSS (Equity Linked Savings Scheme, 3-year lock-in), "
            "life insurance premiums, principal repayment of home loan, and NSC."
        ),
    },
    {
        "keywords": ["emergency fund", "liquidity", "contingency", "buffer", "salaried", "freelancer", "freelancers", "fluctuating", "self-employed"],
        "title": "Emergency Fund Calibration: Salaried vs Freelancers",
        "reference_id": "PRUDENTIAL_EMERGENCY_RESERVE",
        "snippet": (
            "Prudent financial planning recommends different emergency buffer sizes depending on income stability. "
            "Salaried individuals with predictable monthly paychecks and employer benefits should hold 3 to 6 months "
            "of mandatory living expenses (rent, groceries, EMIs, insurance). Freelancers, consultants, and self-employed "
            "individuals with fluctuating or irregular income should maintain 9 to 12 months of essential expenses plus a "
            "separate reserve for quarterly advance income tax and business slowdowns. Emergency money should stay in "
            "high-liquidity, low-volatility avenues such as high-yield savings accounts, sweep-in FDs, or liquid debt funds "
            "so long-term equity investments never need to be sold during market downturns."
        ),
    },
    {
        "keywords": ["nifty 50", "nifty", "index fund", "index funds", "passive", "etf", "expense ratio"],
        "title": "Nifty 50 Index Funds & Passive Equity Investing in India",
        "reference_id": "SEBI_PASSIVE_INDEX_FUNDS",
        "snippet": (
            "Nifty 50 Index Funds passively replicate India's 50 largest listed companies on the National Stock Exchange "
            "by market capitalization. Direct-plan Nifty 50 index funds typically carry very low expense ratios (0.05% to 0.25% p.a.), "
            "eliminating fund manager selection bias and style drift. Over long horizons (10 to 15+ years), lower annual fees "
            "compound meaningfully in the investor's favor. They carry no statutory lock-in period (high liquidity), and profits "
            "are subject to standard equity taxation: LTCG at 12.5% above ₹1.25 Lakh/year (held > 12 months) and STCG at 20%."
        ),
    },
    {
        "keywords": ["elss", "equity linked savings scheme", "active fund", "actively managed", "tax saver", "lock-in", "alpha"],
        "title": "Actively Managed ELSS Mutual Funds & Lock-in Framework",
        "reference_id": "SEBI_ELSS_GUIDELINES",
        "snippet": (
            "ELSS (Equity Linked Savings Scheme) mutual funds are actively managed diversified equity funds investing at least 80% "
            "in equities. Under the Old Tax Regime, ELSS investments qualify for Section 80C tax deductions up to ₹1,50,000 per year "
            "with a mandatory 3-year statutory lock-in per installment (the shortest lock-in among Section 80C options). "
            "Actively managed ELSS funds charge higher expense ratios (typically 0.60% to 1.20% in Direct plans and 1.50% to 2.10% "
            "in Regular plans) to pay for active stock selection aiming to beat the benchmark. However, SPIVA India studies show "
            "a substantial share of active large-cap/diversified funds underperform broad indices over 10-to-15-year periods after fees. "
            "Under the New Tax Regime, ELSS provides no Section 80C tax deduction, making its 3-year lock-in and higher fee a key trade-off vs Index Funds."
        ),
    },
    {
        "keywords": ["new tax regime", "old tax regime", "tax regime", "87a", "standard deduction", "income tax", "budget 2024"],
        "title": "India Income Tax Regimes: Old vs New Regime (Finance Act 2024)",
        "reference_id": "INCOME_TAX_REGIME_2024",
        "snippet": (
            "The New Tax Regime is the default personal income tax structure in India, offering lower slab rates and a "
            "₹75,000 standard deduction for salaried taxpayers plus Section 87A tax rebate for eligible lower-taxable-income brackets, "
            "while disallowing most exemptions such as Section 80C, 80D, HRA, and Section 24(b) home loan interest. "
            "The Old Tax Regime retains higher slab rates but permits deductions including Section 80C (₹1.5 Lakh), "
            "Section 80CCD(1B) NPS (₹50,000), Section 80D health insurance, and Section 24(b) home loan interest (₹2 Lakh)."
        ),
    },
    {
        "keywords": ["sip", "systematic investment plan", "lump sum", "compounding", "rupee cost averaging", "horizon", "15-year", "long-term"],
        "title": "SIP vs Lump Sum Investing & Long-Term Compounding Principles",
        "reference_id": "INVESTOR_EDU_SIP_COMPOUNDING",
        "snippet": (
            "Systematic Investment Plans (SIPs) automate fixed monthly investments and apply rupee cost averaging: buying more "
            "fund units during market dips and fewer at peaks, which helps manage timing risk and behavioral stress. "
            "Over long horizons (10 to 15+ years), compounding accelerates wealth creation as returns themselves generate "
            "further returns, while minimizing annual expense ratios and portfolio churn preserves a larger share of the final corpus."
        ),
    },
    {
        "keywords": ["asset allocation", "rebalancing", "diversification", "portfolio", "risk profile", "drawdown", "volatility"],
        "title": "Asset Allocation, Diversification & Portfolio Rebalancing",
        "reference_id": "SEBI_PORTFOLIO_ALLOCATION",
        "snippet": (
            "Asset allocation: splitting money across growth assets (equities), stability assets (debt/fixed income), and "
            "hedges (gold), is the primary driver of long-term portfolio volatility and drawdown behavior. Annual rebalancing "
            "restores target weights by trimming appreciated assets and adding to underweighted ones. Investors nearing "
            "retirement or short-term goals (under 5 years) should gradually shift toward lower-volatility debt instruments "
            "to reduce sequence-of-returns risk."
        ),
    },
    {
        "keywords": ["scss", "senior citizen", "post office", "retirement income", "nsc"],
        "title": "Senior Citizen Savings Scheme (SCSS) & Sovereign Small Savings",
        "reference_id": "MOF_SCSS_GUIDELINES",
        "snippet": (
            "The Senior Citizen Savings Scheme (SCSS) is a sovereign-backed 5-year scheme (extendable by 3 years) for Indian "
            "residents aged 60+ (or 55+ under voluntary retirement rules), with a maximum deposit ceiling of ₹30 Lakh. "
            "It offers government-administered quarterly interest (~8.2% p.a. benchmark). Principal qualifies under Section 80C "
            "(Old Regime), while interest earned is taxable at the investor's slab rate."
        ),
    },
    {
        "keywords": ["health insurance", "term insurance", "80d", "section 80d", "insurance", "life cover"],
        "title": "Personal Risk Protection: Term Life & Health Insurance (Section 80D)",
        "reference_id": "IRDAI_PROTECTION_STANDARDS",
        "snippet": (
            "Financial planning frameworks recommend securing adequate protection before aggressive investing: pure term life "
            "insurance of 10x to 15x annual income for earners with financial dependents, and personal health insurance "
            "independent of employer group coverage. Under Section 80D (Old Regime), health insurance premiums qualify for "
            "deductions up to ₹25,000 for self/family and an additional ₹25,000 (₹50,000 if senior citizen) for parents."
        ),
    },
    {
        "keywords": ["credit card", "personal loan", "debt", "emi", "loan", "high interest", "apr"],
        "title": "High-Cost Debt Repayment Priority vs Market Investing",
        "reference_id": "PRUDENTIAL_DEBT_WATERFALL",
        "snippet": (
            "Revolving credit card balances in India typically carry 30% to 42% APR, and unsecured personal loans charge "
            "11% to 16% p.a. Because paying down high-interest debt provides an immediate, predictable interest savings "
            "far exceeding typical long-term market returns after tax, clearing credit card balances and expensive personal "
            "loans takes priority over starting new equity investments, once a starter emergency buffer is in place."
        ),
    },
]


def search_financial_documents(
    query: str,
    user_id: int,
    db: Session,
    limit: int = 3,
) -> list[EvidenceItem]:
    """
    Search investor's indexed documents using the hybrid RAG pipeline.
    Enforces user boundary isolation.
    """
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        logger.warning("search_financial_documents called with invalid user_id: %s", user_id)
        return []

    if not query or not query.strip():
        return []

    try:
        chunks = retrieve_and_rerank(
            db=db,
            query=query.strip(),
            user_id=user_id,
            top_k=min(max(1, limit), 5),
            candidate_k=min(max(1, limit * 2), 20),
        )
    except Exception as exc:
        logger.warning("RAG search failed for query '%s' and user %s: %s", query, user_id, exc)
        return []

    items: list[EvidenceItem] = []
    for chunk in chunks:
        confidence = (
            round(float(chunk.relevance_score) / 100.0, 3)
            if chunk.relevance_score is not None
            else None
        )
        items.append(
            EvidenceItem(
                source_type="financial_document",
                source_title=chunk.document_name,
                reference_id=f"chunk_{chunk.chunk_id}",
                content_snippet=chunk.content.strip(),
                confidence_score=confidence,
            )
        )
    return items


def calculate_financial_metrics(
    calculation_type: str,
    parameters: dict[str, Any],
) -> EvidenceItem:
    """
    Execute deterministic financial calculations.
    Rejects LLM arithmetic and enforces exact Decimal precision.
    """
    calc_lower = calculation_type.strip().lower()

    try:
        if calc_lower in ("future_value_lumpsum", "future_value_lump_sum", "lump_sum"):
            principal = parameters.get("principal")
            annual_rate = parameters.get("annual_rate_percent") or parameters.get("annual_return_percent")
            months = int(parameters.get("time_horizon_months") or (int(parameters.get("tenure_years", 1)) * 12))
            fv = calculate_future_value_lumpsum(principal, annual_rate, months)
            snippet = f"Future value of lump-sum ₹{principal} at {annual_rate}% over {months} months is ₹{fv}."

        elif calc_lower in ("future_value_sip", "sip"):
            monthly = parameters.get("monthly_contribution") or parameters.get("monthly_investment")
            annual_rate = parameters.get("annual_rate_percent") or parameters.get("annual_return_percent")
            months = int(parameters.get("time_horizon_months") or (int(parameters.get("tenure_years", 1)) * 12))
            fv = calculate_future_value_sip(monthly, annual_rate, months)
            snippet = f"Future value of monthly SIP ₹{monthly} at {annual_rate}% over {months} months is ₹{fv}."

        elif calc_lower in ("monthly_surplus", "surplus"):
            income = parameters.get("monthly_income")
            expenses = parameters.get("monthly_expenses")
            surplus = calculate_monthly_surplus(income, expenses)
            snippet = f"Monthly surplus for income ₹{income} and expenses ₹{expenses} is ₹{surplus}."

        elif calc_lower in ("savings_rate",):
            income = parameters.get("monthly_income")
            expenses = parameters.get("monthly_expenses")
            rate = calculate_savings_rate(income, expenses)
            snippet = f"Savings rate for income ₹{income} and expenses ₹{expenses} is {rate}%."

        elif calc_lower in ("expense_ratio",):
            income = parameters.get("monthly_income")
            expenses = parameters.get("monthly_expenses")
            ratio = calculate_expense_ratio(income, expenses)
            snippet = f"Expense ratio for income ₹{income} and expenses ₹{expenses} is {ratio}%."

        elif calc_lower in ("required_monthly_sip",):
            target = parameters.get("target_amount")
            current = parameters.get("current_amount", 0)
            annual_rate = parameters.get("annual_rate_percent") or parameters.get("annual_return_percent", 0)
            months = int(parameters.get("time_horizon_months") or (int(parameters.get("tenure_years", 1)) * 12))
            sip = calculate_required_monthly_sip(target, current, annual_rate, months)
            snippet = (
                f"Required monthly SIP to accumulate target ₹{target} from starting ₹{current} "
                f"at {annual_rate}% over {months} months is ₹{sip}."
            )

        elif calc_lower in ("goal_shortfall", "shortfall"):
            target = parameters.get("target_amount")
            current = parameters.get("current_amount", 0)
            shortfall = calculate_goal_shortfall(target, current)
            snippet = f"Goal shortfall between target ₹{target} and current ₹{current} is ₹{shortfall}."

        else:
            raise FinancialCalculationError(f"Unsupported calculation type '{calculation_type}'.")

        return EvidenceItem(
            source_type="financial_calculation",
            source_title=f"Deterministic Calculation: {calculation_type}",
            reference_id=calculation_type,
            content_snippet=snippet,
            confidence_score=1.0,
        )

    except Exception as exc:
        logger.warning("Calculation failed for %s with params %s: %s", calculation_type, parameters, exc)
        return EvidenceItem(
            source_type="financial_calculation",
            source_title=f"Deterministic Calculation: {calculation_type}",
            reference_id=calculation_type,
            content_snippet=f"Calculation error: {exc}",
            confidence_score=0.0,
        )


def search_financial_information(topic: str) -> list[EvidenceItem]:
    """
    Search approved financial information repository for verified rules,
    tax provisions, statutory rates, and investment vehicle details.
    """
    if not topic or not topic.strip():
        return []

    tokens = [t.lower() for t in topic.strip().split() if len(t) > 2]
    matched: list[tuple[int, dict[str, Any]]] = []

    for entry in APPROVED_FINANCIAL_KNOWLEDGE:
        score = 0
        for kw in entry["keywords"]:
            if kw in topic.lower():
                score += 5
            for t in tokens:
                if t in kw:
                    score += 1
        if score > 0:
            matched.append((score, entry))

    matched.sort(key=lambda x: x[0], reverse=True)

    results: list[EvidenceItem] = []
    for _, item in matched[:4]:
        results.append(
            EvidenceItem(
                source_type="financial_information",
                source_title=item["title"],
                reference_id=item["reference_id"],
                content_snippet=item["snippet"],
                confidence_score=0.95,
            )
        )

    if not results:
        results.append(
            EvidenceItem(
                source_type="financial_information",
                source_title="General Regulatory Financial Guidelines",
                reference_id="GEN_FIN_GUIDELINES",
                content_snippet=(
                    "Under Indian financial regulations (SEBI & RBI), all non-deposit investment products "
                    "carry market risks. Tax implications depend on asset category, holding period, and applicable "
                    "income tax regime. Investors should diversify across asset classes based on risk capacity."
                ),
                confidence_score=0.8,
            )
        )

    return results

