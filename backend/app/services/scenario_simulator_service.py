from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import json
import logging
from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.goal import Goal
from app.models.profile import Profile
from app.schemas.scenario_simulation import (
    SCENARIO_DISCLAIMER,
    ScenarioAIExplanation,
    ScenarioMetricsComparison,
    ScenarioParameterChanges,
    ScenarioSimulationRequest,
    ScenarioSimulationResponse,
    ScenarioTemplateItem,
    TrajectoryPoint,
)
from app.services.advisor_output_validation_service import (
    UNSAFE_FINANCIAL_PATTERNS,
    _is_negated,
)
from app.services.financial_calculation_service import (
    calculate_future_value_lumpsum,
    calculate_future_value_sip,
    calculate_monthly_surplus,
)

logger = logging.getLogger(__name__)

CENT = Decimal("0.01")


class ScenarioSimulationError(Exception):
    """Raised when scenario simulation or AI explanation generation fails."""


PREDEFINED_SCENARIO_TEMPLATES: list[ScenarioTemplateItem] = [
    ScenarioTemplateItem(
        template_id="sip_step_up_5k",
        title="Step Up Monthly SIP by ₹5,000",
        description="Simulate the long-term compounding impact of increasing your monthly investment by ₹5,000.",
        parameters=ScenarioParameterChanges(
            delta_monthly_investment=Decimal("5000"),
            assumed_annual_return_percent=Decimal("12.0"),
            time_horizon_years=10,
        ),
    ),
    ScenarioTemplateItem(
        template_id="one_time_bonus_100k",
        title="Invest One-Time ₹1,00,000 Bonus",
        description="Model the growth of deploying a lump-sum windfall or bonus alongside your ongoing monthly investments.",
        parameters=ScenarioParameterChanges(
            one_time_lump_sum=Decimal("100000"),
            assumed_annual_return_percent=Decimal("11.0"),
            time_horizon_years=10,
        ),
    ),
    ScenarioTemplateItem(
        template_id="frugal_budget_trim",
        title="Reduce Expenses by ₹4,000 & Channel to SIP",
        description="Optimize discretionary spending by ₹4,000/month and redirect the full cash flow to wealth compounding.",
        parameters=ScenarioParameterChanges(
            delta_monthly_expenses=Decimal("-4000"),
            delta_monthly_investment=Decimal("4000"),
            assumed_annual_return_percent=Decimal("12.0"),
            time_horizon_years=10,
        ),
    ),
    ScenarioTemplateItem(
        template_id="conservative_stress_test",
        title="Conservative Market Stress Test (7%)",
        description="Simulate portfolio trajectory under subdued market returns or high fixed-income allocation.",
        parameters=ScenarioParameterChanges(
            assumed_annual_return_percent=Decimal("7.0"),
            time_horizon_years=10,
        ),
    ),
    ScenarioTemplateItem(
        template_id="extended_horizon_15y",
        title="Extended 15-Year Horizon",
        description="Examine the exponential hockey-stick compounding curve over an extended 15-year horizon.",
        parameters=ScenarioParameterChanges(
            assumed_annual_return_percent=Decimal("12.0"),
            time_horizon_years=15,
        ),
    ),
]


def _get_gemini_client() -> genai.Client:
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options={"api_version": "v1beta", "timeout": 30000},
    )


def _to_decimal(val: Any, default: Decimal = Decimal("0")) -> Decimal:
    if val is None:
        return default
    try:
        dec = Decimal(str(val))
        return dec if dec.is_finite() else default
    except Exception:
        return default


def _money(val: Decimal) -> Decimal:
    return val.quantize(CENT, rounding=ROUND_HALF_UP)


def calculate_scenario_trajectory(
    baseline_income: Decimal,
    baseline_expenses: Decimal,
    baseline_sip: Decimal,
    existing_corpus: Decimal,
    params: ScenarioParameterChanges,
    target_goal: Goal | None = None,
) -> tuple[ScenarioMetricsComparison, list[TrajectoryPoint]]:
    """
    Deterministically project baseline vs hypothetical financial trajectory year by year.
    Uses exact Decimal arithmetic.
    """
    # 1. Compute scenario inputs
    scenario_income = (
        params.new_monthly_income
        if params.new_monthly_income is not None
        else max(Decimal("0"), baseline_income + (params.delta_monthly_income or Decimal("0")))
    )

    scenario_expenses = (
        params.new_monthly_expenses
        if params.new_monthly_expenses is not None
        else max(Decimal("0"), baseline_expenses + (params.delta_monthly_expenses or Decimal("0")))
    )

    baseline_surplus = calculate_monthly_surplus(baseline_income, baseline_expenses)
    scenario_surplus = calculate_monthly_surplus(scenario_income, scenario_expenses)

    if params.new_monthly_investment is not None:
        scenario_sip = params.new_monthly_investment
    elif params.delta_monthly_investment is not None:
        scenario_sip = max(Decimal("0"), baseline_sip + params.delta_monthly_investment)
    else:
        scenario_sip = baseline_sip

    lump_sum = params.one_time_lump_sum or Decimal("0")
    rate = params.assumed_annual_return_percent
    years = params.time_horizon_years

    # 2. Build year-by-year trajectory
    trajectory: list[TrajectoryPoint] = []

    for y in range(1, years + 1):
        months = y * 12

        # Baseline: initial corpus + monthly baseline SIP
        b_init_growth = calculate_future_value_lumpsum(existing_corpus, rate, months)
        b_sip_growth = calculate_future_value_sip(baseline_sip, rate, months)
        b_corpus = _money(b_init_growth + b_sip_growth)
        b_invested = _money(existing_corpus + (baseline_sip * Decimal(months)))

        # Scenario: (initial corpus + lump_sum) + monthly scenario SIP
        s_init_growth = calculate_future_value_lumpsum(existing_corpus + lump_sum, rate, months)
        s_sip_growth = calculate_future_value_sip(scenario_sip, rate, months)
        s_corpus = _money(s_init_growth + s_sip_growth)
        s_invested = _money((existing_corpus + lump_sum) + (scenario_sip * Decimal(months)))

        delta_corpus = _money(s_corpus - b_corpus)

        trajectory.append(
            TrajectoryPoint(
                year=y,
                baseline_projected_corpus=b_corpus,
                scenario_projected_corpus=s_corpus,
                delta_corpus=delta_corpus,
                baseline_total_invested=b_invested,
                scenario_total_invested=s_invested,
            )
        )

    # 3. Final metrics comparison
    final_point = trajectory[-1]
    baseline_final_val = final_point.baseline_projected_corpus
    scenario_final_val = final_point.scenario_projected_corpus
    absolute_growth = _money(scenario_final_val - baseline_final_val)

    pct_increase = None
    if baseline_final_val > Decimal("0"):
        pct_increase = _money((absolute_growth / baseline_final_val) * Decimal("100"))

    extra_invested = _money(final_point.scenario_total_invested - final_point.baseline_total_invested)
    net_wealth_gain = _money(absolute_growth - extra_invested)

    wealth_mult = None
    if extra_invested > Decimal("0"):
        wealth_mult = Decimal(round(float(absolute_growth) / float(extra_invested), 2))

    # Goal progress delta
    goal_id = None
    goal_title = None
    b_shortfall = None
    s_shortfall = None
    shortfall_reduction = None

    if target_goal is not None:
        goal_id = target_goal.id
        goal_title = target_goal.title
        target_amt = _to_decimal(target_goal.target_amount)
        b_shortfall = _money(max(Decimal("0"), target_amt - baseline_final_val))
        s_shortfall = _money(max(Decimal("0"), target_amt - scenario_final_val))
        shortfall_reduction = _money(b_shortfall - s_shortfall)

    comparison = ScenarioMetricsComparison(
        baseline_monthly_investment=baseline_sip,
        scenario_monthly_investment=scenario_sip,
        baseline_monthly_surplus=baseline_surplus,
        scenario_monthly_surplus=scenario_surplus,
        baseline_projected_value=baseline_final_val,
        scenario_projected_value=scenario_final_val,
        absolute_growth_delta=absolute_growth,
        percentage_corpus_increase=pct_increase,
        additional_out_of_pocket_invested=extra_invested,
        net_wealth_gain_from_change=net_wealth_gain,
        wealth_multiplier_on_new_capital=wealth_mult,
        goal_id=goal_id,
        goal_title=goal_title,
        baseline_goal_shortfall=b_shortfall,
        scenario_goal_shortfall=s_shortfall,
        goal_shortfall_reduction=shortfall_reduction,
    )

    return comparison, trajectory


def _validate_scenario_safety(explanation: ScenarioAIExplanation) -> None:
    texts = [
        explanation.summary_narrative,
        *explanation.key_advantages,
        *explanation.trade_offs_and_risks,
        *explanation.practical_next_steps,
    ]
    if explanation.goal_impact_analysis:
        texts.append(explanation.goal_impact_analysis)

    for text in texts:
        for pattern in UNSAFE_FINANCIAL_PATTERNS:
            for match in pattern.finditer(text):
                if _is_negated(text, match.start()):
                    continue
                raise ScenarioSimulationError(
                    "Scenario explanation contains disallowed certainty or guaranteed returns language."
                )


def generate_scenario_explanation(
    scenario_name: str,
    comparison: ScenarioMetricsComparison,
    trajectory: list[TrajectoryPoint],
    params: ScenarioParameterChanges,
    client: genai.Client | None = None,
) -> ScenarioAIExplanation:
    """Generate structured AI narrative analyzing the financial simulation."""
    if client is None:
        try:
            client = _get_gemini_client()
        except Exception as exc:
            raise ScenarioSimulationError(
                f"Failed to initialize Gemini client: {exc}"
            ) from exc

    milestone_years = [1, min(5, len(trajectory)), len(trajectory)]
    milestones = [
        t.model_dump(mode="json")
        for t in trajectory
        if t.year in set(milestone_years)
    ]

    context = {
        "scenario_name": scenario_name,
        "time_horizon_years": params.time_horizon_years,
        "assumed_annual_return_percent": str(params.assumed_annual_return_percent),
        "comparison_summary": comparison.model_dump(mode="json"),
        "trajectory_milestones": milestones,
    }

    prompt = f"""You are an expert AI Financial Advisor explaining a hypothetical scenario simulation for an investor.

SIMULATION DATA:
{json.dumps(context, indent=2)}

INSTRUCTIONS:
1. Explain the financial trajectory shift caused by the hypothetical change.
2. Highlight key advantages, including the compounding multiplier on extra savings.
3. Detail trade-offs and risks (e.g. reduced monthly liquid cash buffer, inflation eroding real purchasing power, market volatility).
4. If goal information is present, explain how the scenario closes or impacts the target shortfall.
5. Provide actionable, practical next steps for the investor.
6. MANDATORY RULE: Never state or imply guaranteed returns or zero risk. All figures are hypothetical mathematical projections.
7. Return your response matching the ScenarioAIExplanation schema."""

    try:
        response = client.models.generate_content(
            model=settings.advisor_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=3000,
                response_mime_type="application/json",
                response_schema=ScenarioAIExplanation,
            ),
        )
    except Exception as exc:
        logger.exception("Failed to generate scenario explanation.")
        raise ScenarioSimulationError(
            f"Failed to generate scenario explanation: {exc}"
        ) from exc

    if response is None:
        raise ScenarioSimulationError("Gemini returned an empty response.")

    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, ScenarioAIExplanation):
        explanation = parsed
    else:
        text = getattr(response, "text", "")
        if not text:
            raise ScenarioSimulationError("Gemini returned an empty text.")
        try:
            explanation = ScenarioAIExplanation.model_validate_json(text)
        except ValidationError as exc:
            raise ScenarioSimulationError(f"Validation failed on scenario explanation: {exc}") from exc

    _validate_scenario_safety(explanation)
    return explanation


def run_scenario_simulation(
    db: Session,
    user_id: int,
    request: ScenarioSimulationRequest,
    client: genai.Client | None = None,
) -> ScenarioSimulationResponse:
    """
    Run complete financial scenario simulation for authenticated investor.
    """
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("Invalid user ID.")

    # 1. Resolve baseline parameters
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    goals = db.query(Goal).filter(Goal.user_id == user_id).all()

    existing_corpus = Decimal("0")
    if profile is not None:
        existing_corpus = _to_decimal(profile.savings) + _to_decimal(profile.existing_investments)

    if request.base_overrides:
        baseline_income = request.base_overrides.monthly_income
        baseline_expenses = request.base_overrides.monthly_expenses
        baseline_sip = request.base_overrides.current_monthly_investment
        if request.base_overrides.existing_accumulated_corpus > Decimal("0"):
            existing_corpus = request.base_overrides.existing_accumulated_corpus
    elif profile is not None:
        baseline_income = _to_decimal(profile.monthly_income, Decimal("80000.00"))
        baseline_expenses = _to_decimal(profile.monthly_expenses, Decimal("50000.00"))
        surplus = max(Decimal("0"), baseline_income - baseline_expenses)
        baseline_sip = _money(surplus * Decimal("0.5")) if surplus > Decimal("0") else Decimal("5000.00")
    else:
        baseline_income = Decimal("80000.00")
        baseline_expenses = Decimal("50000.00")
        baseline_sip = Decimal("15000.00")

    # 2. Check linked goal if provided
    target_goal: Goal | None = None
    if request.parameters.target_goal_id is not None:
        target_goal = (
            db.query(Goal)
            .filter(Goal.id == request.parameters.target_goal_id, Goal.user_id == user_id)
            .first()
        )
        if target_goal is None:
            raise ValueError(f"Goal {request.parameters.target_goal_id} not found for this user.")

    # 3. Compute deterministic projections
    comparison, trajectory = calculate_scenario_trajectory(
        baseline_income=baseline_income,
        baseline_expenses=baseline_expenses,
        baseline_sip=baseline_sip,
        existing_corpus=existing_corpus,
        params=request.parameters,
        target_goal=target_goal,
    )

    # 4. Generate AI explanation
    ai_explanation = generate_scenario_explanation(
        scenario_name=request.scenario_name,
        comparison=comparison,
        trajectory=trajectory,
        params=request.parameters,
        client=client,
    )

    return ScenarioSimulationResponse(
        scenario_name=request.scenario_name,
        time_horizon_years=request.parameters.time_horizon_years,
        assumed_annual_return_percent=request.parameters.assumed_annual_return_percent,
        comparison=comparison,
        yearly_trajectory=trajectory,
        ai_explanation=ai_explanation,
    )
