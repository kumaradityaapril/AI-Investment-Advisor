from datetime import datetime, timezone
from decimal import Decimal

from app.schemas.ai_advisor import (
    AIAdvisorGenerationResponse,
    AdvisorRecommendation,
)
from app.schemas.analysis_diff import AnalysisDiffExplanation
from app.schemas.financial_context import FinancialContext, FinancialMetricsContext
from app.schemas.investment_comparison import (
    InvestmentComparisonExplanation,
    OptionSuitability,
)
from app.schemas.research_agent import ResearchReport
from app.schemas.scenario_simulation import ScenarioAIExplanation
from app.services.advisor_output_validation_service import (
    validate_and_enforce_advisor_output,
)
from app.services.plain_language_service import (
    annotate_analysis_diff_explanation,
    annotate_comparison_explanation,
    annotate_financial_terms,
    annotate_research_report,
    annotate_scenario_explanation,
)


def test_annotates_first_occurrence_only():
    seen: set[str] = set()
    first = annotate_financial_terms(
        "Start a monthly SIP in an Index Fund to benefit from compounding.",
        seen_concepts=seen,
    )
    second = annotate_financial_terms(
        "Your SIP and Index Fund investments also reduce expense ratio drag.",
        seen_concepts=seen,
    )

    assert "SIP (Systematic Investment Plan" in first
    assert "Index Fund (a low-cost fund" in first
    assert "compounding (earning returns" in first

    # Already defined terms are NOT re-annotated in subsequent fields
    assert "SIP (" not in second
    assert "Index Fund (" not in second
    # New term IS annotated
    assert "expense ratio (the small yearly fee" in second


def test_skips_already_explained_terms_and_nested_parentheses():
    text = "Invest via SIP (monthly automated deposits) and Public Provident Fund (PPF) for Section 80C tax benefits."
    result = annotate_financial_terms(text)

    # SIP already had a bracket immediately after it -> no double bracket
    assert result.count("SIP (") == 1
    assert "SIP (monthly automated deposits)" in result
    # Public Provident Fund already had (PPF) right after it -> no nested bracket inside (PPF)
    assert "Public Provident Fund (PPF)" in result
    assert "(PPF (" not in result
    # Unexplained Section 80C gets annotated
    assert "Section 80C (an income tax rule" in result


def test_respects_max_length():
    text = "Use SIP and PPF for long-term wealth."
    result = annotate_financial_terms(text, max_length=len(text) + 10)
    assert len(result) <= len(text) + 10


def test_acronyms_are_case_sensitive():
    text = "Take a sip of water before reviewing your SIP."
    result = annotate_financial_terms(text)
    assert "Take a sip of water" in result
    assert "your SIP (Systematic Investment Plan" in result


def test_all_five_report_models_annotated_cleanly():
    # 1. Grounded AI Advisor response (through full validation pipeline)
    advisor_resp = AIAdvisorGenerationResponse(
        overall_assessment="Starting a monthly SIP into an Index Fund helps beat inflation.",
        key_findings=["Your SIP builds a long-term corpus while keeping expense ratio low."],
        recommendations=[
            AdvisorRecommendation(
                title="Use PPF for stability",
                explanation="PPF gives sovereign-backed tax savings under Section 80C.",
                suggested_action="Open a PPF account and automate your monthly SIP.",
                priority="high",
            )
        ],
        risk_considerations=["Equity volatility can cause short-term drawdown."],
        assumptions=["Inflation remains steady."],
        limitations=["Tax laws may change."],
    )
    ctx = FinancialContext(
        user_id=1,
        metrics=FinancialMetricsContext(),
        goal_analysis=[],
        generated_at=datetime.now(timezone.utc),
    )
    validated_advisor = validate_and_enforce_advisor_output(advisor_resp, ctx)
    assert "SIP (Systematic Investment Plan" in validated_advisor.overall_assessment
    assert "Index Fund (a low-cost fund" in validated_advisor.overall_assessment
    assert "PPF (Public Provident Fund" in validated_advisor.recommendations[0].explanation
    assert "volatility (how sharply" in validated_advisor.risk_considerations[0]
    # SIP should not be annotated a second time in key_findings
    assert "SIP (" not in validated_advisor.key_findings[0]

    # 2. Investment Comparison
    comp = InvestmentComparisonExplanation(
        summary="Comparing ELSS against PPF shows clear liquidity and lock-in differences.",
        key_differences=["ELSS carries equity volatility while PPF is sovereign-backed."],
        suitability_analysis=[
            OptionSuitability(
                option_name="ELSS",
                suitable_for="Long-term investors seeking LTCG tax efficiency.",
                unsuitable_for="Investors needing immediate liquidity.",
                key_tradeoff="Higher volatility in exchange for growth potential.",
            ),
            OptionSuitability(
                option_name="PPF",
                suitable_for="Conservative savers using Section 80C.",
                unsuitable_for="Short-term cash needs due to long lock-in.",
                key_tradeoff="Lower growth potential versus stability.",
            ),
        ],
        risk_tradeoffs=["Inflation can reduce real return on fixed-income options."],
        assumptions_and_missing_info=["Assumes current tax rules."],
    )
    comp_out = annotate_comparison_explanation(comp)
    assert "ELSS (Equity Linked Savings Scheme" in comp_out.summary
    assert "PPF (Public Provident Fund" in comp_out.summary
    assert "LTCG (Long-Term Capital Gains" in comp_out.suitability_analysis[0].suitable_for

    # 3. Scenario Simulator
    scen = ScenarioAIExplanation(
        summary_narrative="Increasing your SIP boosts compounding and grows your final corpus.",
        key_advantages=["Higher CAGR impact over long horizons."],
        trade_offs_and_risks=["Lower short-term liquidity."],
        goal_impact_analysis="Helps close your retirement corpus gap faster.",
        practical_next_steps=["Automate monthly SIP transfers."],
    )
    scen_out = annotate_scenario_explanation(scen)
    assert "SIP (Systematic Investment Plan" in scen_out.summary_narrative
    assert "compounding (earning returns" in scen_out.summary_narrative
    assert "CAGR (Compound Annual Growth Rate" in scen_out.key_advantages[0]

    # 4. Autonomous Research Agent
    research = ResearchReport(
        research_question="How does LTCG tax work on mutual funds?",
        summary="LTCG applies to equity mutual fund profits held beyond one year.",
        key_findings=["STCG applies when units are sold within one year."],
        sources=["Income Tax Act"],
        risks_and_limitations=["Inflation and market volatility affect actual outcomes."],
    )
    research_out = annotate_research_report(research)
    assert "LTCG (Long-Term Capital Gains" in research_out.summary
    assert "STCG (Short-Term Capital Gains" in research_out.key_findings[0]

    # 5. Analysis History Diff
    diff = AnalysisDiffExplanation(
        summary_narrative="Your asset allocation improved as your SIP contribution grew.",
        key_improvements=["Better diversification across debt funds and equities."],
        key_concerns=["Watch your fund expense ratio over time."],
        stale_recommendations=["Old FD renewal advice is now outdated."],
        updated_strategic_focus=["Schedule yearly rebalancing."],
    )
    diff_out = annotate_analysis_diff_explanation(diff)
    assert "asset allocation (how your money" in diff_out.summary_narrative
    assert "rebalancing (periodically adjusting" in diff_out.updated_strategic_focus[0]
