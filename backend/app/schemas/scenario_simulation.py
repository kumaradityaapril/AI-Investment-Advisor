from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCENARIO_DISCLAIMER = (
    "These figures are hypothetical mathematical projections based on constant return and compounding "
    "assumptions. They do not represent guaranteed returns, performance forecasts, or personalized investment advice. "
    "Actual market returns fluctuate, and capital is subject to market risks."
)


class ScenarioParameterChanges(BaseModel):
    """Parameters modified in a hypothetical financial scenario."""

    model_config = ConfigDict(extra="ignore")

    delta_monthly_investment: Decimal | None = Field(
        default=None,
        description="Change in monthly investment amount (e.g. +5000 or -2000)",
    )
    new_monthly_investment: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        description="Explicit replacement monthly investment amount",
    )
    delta_monthly_income: Decimal | None = Field(
        default=None,
        description="Change in monthly income (e.g. salary increment)",
    )
    new_monthly_income: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        description="Explicit replacement monthly income",
    )
    delta_monthly_expenses: Decimal | None = Field(
        default=None,
        description="Change in monthly living expenses (e.g. cost-cutting or lifestyle inflation)",
    )
    new_monthly_expenses: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        description="Explicit replacement monthly expenses",
    )
    one_time_lump_sum: Decimal | None = Field(
        default=Decimal("0"),
        ge=Decimal("0"),
        description="Additional one-time lump-sum contribution (e.g. bonus, windfall)",
    )
    assumed_annual_return_percent: Decimal = Field(
        default=Decimal("10.0"),
        ge=Decimal("0.0"),
        le=Decimal("30.0"),
        description="Annualized return percentage assumption",
    )
    time_horizon_years: int = Field(
        default=10,
        ge=1,
        le=40,
        description="Investment simulation horizon in years",
    )
    target_goal_id: int | None = Field(
        default=None,
        gt=0,
        description="Optional financial goal ID to assess target shortfall progress",
    )


class BaseFinancialOverrides(BaseModel):
    """Optional manual baseline inputs for investors without a saved profile."""

    model_config = ConfigDict(extra="forbid")

    monthly_income: Decimal = Field(ge=Decimal("0"), default=Decimal("80000.00"))
    monthly_expenses: Decimal = Field(ge=Decimal("0"), default=Decimal("50000.00"))
    current_monthly_investment: Decimal = Field(ge=Decimal("0"), default=Decimal("15000.00"))
    existing_accumulated_corpus: Decimal = Field(ge=Decimal("0"), default=Decimal("100000.00"))


class ScenarioSimulationRequest(BaseModel):
    """User request to simulate a hypothetical financial scenario."""

    model_config = ConfigDict(extra="ignore")

    scenario_name: str = Field(min_length=3, max_length=120, description="Short title for scenario")
    parameters: ScenarioParameterChanges | None = None
    base_overrides: BaseFinancialOverrides | None = None

    @field_validator("scenario_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Scenario name cannot be empty.")
        return s

    @model_validator(mode="before")
    @classmethod
    def resolve_parameters(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_params = data.get("parameters")
            if isinstance(raw_params, dict):
                params = dict(raw_params)
            else:
                params = {}

            # Map flat fields into parameters if present at top level
            if "monthly_investment_delta" in data and "delta_monthly_investment" not in params:
                params["delta_monthly_investment"] = data["monthly_investment_delta"]
            if "delta_monthly_investment" in data and "delta_monthly_investment" not in params:
                params["delta_monthly_investment"] = data["delta_monthly_investment"]

            if "lump_sum_investment" in data and "one_time_lump_sum" not in params:
                params["one_time_lump_sum"] = data["lump_sum_investment"]
            if "one_time_lump_sum" in data and "one_time_lump_sum" not in params:
                params["one_time_lump_sum"] = data["one_time_lump_sum"]

            if "expected_annual_return_percent" in data and "assumed_annual_return_percent" not in params:
                params["assumed_annual_return_percent"] = data["expected_annual_return_percent"]
            if "assumed_annual_return_percent" in data and "assumed_annual_return_percent" not in params:
                params["assumed_annual_return_percent"] = data["assumed_annual_return_percent"]

            if "time_horizon_years" in data and "time_horizon_years" not in params:
                params["time_horizon_years"] = data["time_horizon_years"]

            data["parameters"] = params
        return data

    @model_validator(mode="after")
    def validate_params(self) -> "ScenarioSimulationRequest":
        if self.parameters is None:
            self.parameters = ScenarioParameterChanges()
        return self


class TrajectoryPoint(BaseModel):
    """Annual projected corpus snapshot along the simulation timeline."""

    year: int
    baseline_projected_corpus: Decimal
    scenario_projected_corpus: Decimal
    delta_corpus: Decimal
    baseline_total_invested: Decimal
    scenario_total_invested: Decimal


class ScenarioMetricsComparison(BaseModel):
    """Deterministic comparison between baseline trajectory and simulated scenario."""

    baseline_monthly_investment: Decimal
    scenario_monthly_investment: Decimal
    baseline_monthly_surplus: Decimal
    scenario_monthly_surplus: Decimal
    baseline_projected_value: Decimal
    scenario_projected_value: Decimal
    absolute_growth_delta: Decimal
    percentage_corpus_increase: Decimal | None = None
    additional_out_of_pocket_invested: Decimal
    net_wealth_gain_from_change: Decimal
    wealth_multiplier_on_new_capital: Decimal | None = None
    goal_id: int | None = None
    goal_title: str | None = None
    baseline_goal_shortfall: Decimal | None = None
    scenario_goal_shortfall: Decimal | None = None
    goal_shortfall_reduction: Decimal | None = None


class ScenarioAIExplanation(BaseModel):
    """Grounded AI narrative explaining financial scenario trade-offs and impact."""

    model_config = ConfigDict(extra="ignore")

    summary_narrative: str = Field(min_length=10, max_length=1500)
    key_advantages: list[str] = Field(min_length=1, max_length=10)
    trade_offs_and_risks: list[str] = Field(min_length=1, max_length=10)
    goal_impact_analysis: str | None = Field(default=None, max_length=1000)
    practical_next_steps: list[str] = Field(min_length=1, max_length=10)
    assumptions_disclaimer: str = Field(default=SCENARIO_DISCLAIMER)

    key_takeaways: list[str] = Field(default_factory=list, description="Alias for key_advantages")
    risk_considerations: list[str] = Field(default_factory=list, description="Alias for trade_offs_and_risks")

    @model_validator(mode="after")
    def populate_narrative_aliases(self) -> "ScenarioAIExplanation":
        if not self.key_takeaways and self.key_advantages:
            self.key_takeaways = list(self.key_advantages)
        if not self.risk_considerations and self.trade_offs_and_risks:
            self.risk_considerations = list(self.trade_offs_and_risks)
        return self


class ScenarioProjectionSummary(BaseModel):
    final_future_value: Decimal
    total_invested: Decimal
    total_interest: Decimal


class ScenarioDifferenceSummary(BaseModel):
    future_value_delta: Decimal
    total_invested_delta: Decimal
    total_interest_delta: Decimal
    percentage_increase: Decimal | None = None


class ScenarioSimulationResponse(BaseModel):
    """Complete response containing deterministic calculations and AI narrative."""

    model_config = ConfigDict(extra="ignore")

    scenario_name: str
    time_horizon_years: int
    assumed_annual_return_percent: Decimal
    comparison: ScenarioMetricsComparison
    yearly_trajectory: list[TrajectoryPoint]
    ai_explanation: ScenarioAIExplanation
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    baseline_projection: ScenarioProjectionSummary | None = None
    scenario_projection: ScenarioProjectionSummary | None = None
    difference: ScenarioDifferenceSummary | None = None
    disclaimer: str | None = None

    @model_validator(mode="after")
    def populate_projection_summaries(self) -> "ScenarioSimulationResponse":
        b_invested = self.yearly_trajectory[-1].baseline_total_invested if self.yearly_trajectory else Decimal("0")
        s_invested = self.yearly_trajectory[-1].scenario_total_invested if self.yearly_trajectory else Decimal("0")

        b_future = self.comparison.baseline_projected_value
        s_future = self.comparison.scenario_projected_value

        if self.baseline_projection is None:
            self.baseline_projection = ScenarioProjectionSummary(
                final_future_value=b_future,
                total_invested=b_invested,
                total_interest=max(Decimal("0"), b_future - b_invested),
            )
        if self.scenario_projection is None:
            self.scenario_projection = ScenarioProjectionSummary(
                final_future_value=s_future,
                total_invested=s_invested,
                total_interest=max(Decimal("0"), s_future - s_invested),
            )
        if self.difference is None:
            self.difference = ScenarioDifferenceSummary(
                future_value_delta=self.comparison.absolute_growth_delta,
                total_invested_delta=self.comparison.additional_out_of_pocket_invested,
                total_interest_delta=self.comparison.net_wealth_gain_from_change,
                percentage_increase=self.comparison.percentage_corpus_increase,
            )
        if not self.disclaimer:
            self.disclaimer = self.ai_explanation.assumptions_disclaimer or SCENARIO_DISCLAIMER
        return self


class ScenarioTemplateItem(BaseModel):
    """Pre-configured popular scenario template."""

    template_id: str
    title: str
    description: str
    parameters: ScenarioParameterChanges

