from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

COMPARISON_DISCLAIMER = (
    "This investment comparison is for educational and informational purposes only "
    "and does not constitute personalized investment advice. Past performance and "
    "projected returns are not indicative of future results. All investments carry risk, "
    "including the potential loss of principal. Consult a certified financial advisor "
    "before making financial commitments."
)

RiskLevel = Literal["low", "moderate", "high", "very_high"]
LiquidityLevel = Literal["low", "moderate", "high", "locked"]
InvestmentType = Literal["lump_sum", "monthly_sip"]


class InvestmentOptionInput(BaseModel):
    """An investment vehicle to be compared."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=100, description="e.g. Fixed Deposit, Nifty 50 Index Fund")
    category: str = Field(min_length=2, max_length=50, description="e.g. fixed_income, equity_mutual_fund, ppf, gold")
    expected_annual_return_percent: Decimal = Field(
        ge=Decimal("-100.0"),
        le=Decimal("200.0"),
        description="Assumed or indicative annual return percentage",
    )
    risk_level: RiskLevel
    liquidity: LiquidityLevel
    lock_in_period_months: int = Field(default=0, ge=0)
    recommended_horizon_months: int = Field(default=12, ge=1)
    tax_implications: str = Field(min_length=3, max_length=500)
    capital_protection: str = Field(min_length=3, max_length=300)
    advantages: list[str] = Field(min_length=1, max_length=10)
    disadvantages: list[str] = Field(min_length=1, max_length=10)

    @field_validator("expected_annual_return_percent")
    @classmethod
    def validate_finite_return(cls, v: Decimal) -> Decimal:
        if not v.is_finite():
            raise ValueError("Expected annual return must be a finite number.")
        return v


class InvestmentComparisonRequest(BaseModel):
    """Request payload to compare multiple investment options."""

    model_config = ConfigDict(extra="forbid")

    options: list[InvestmentOptionInput] = Field(
        min_length=2,
        max_length=5,
        description="At least 2 and at most 5 options to compare side-by-side.",
    )
    investment_amount: Decimal | None = Field(
        default=None,
        gt=Decimal("0.0"),
        description="Optional principal or monthly SIP amount for quantitative projections.",
    )
    investment_type: InvestmentType = Field(
        default="lump_sum",
        description="lump_sum or monthly_sip",
    )
    time_horizon_months: int | None = Field(
        default=None,
        gt=0,
        le=600,
        description="Optional projection duration in months.",
    )
    investor_question: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional specific inquiry regarding the comparison.",
    )

    @model_validator(mode="after")
    def validate_projection_fields(self):
        # Unique option names
        names = [opt.name.strip().casefold() for opt in self.options]
        if len(names) != len(set(names)):
            raise ValueError("Investment options must have unique names.")

        # If amount is provided, horizon must be provided for calculation
        if self.investment_amount is not None and self.time_horizon_months is None:
            raise ValueError("time_horizon_months is required when investment_amount is supplied.")
        if self.time_horizon_months is not None and self.investment_amount is None:
            raise ValueError("investment_amount is required when time_horizon_months is supplied.")

        return self


class OptionSuitability(BaseModel):
    """Suitability of an investment option for specific investor profiles."""

    model_config = ConfigDict(extra="forbid")

    option_name: str = Field(min_length=2, max_length=100)
    suitable_for: str = Field(min_length=5, max_length=500)
    unsuitable_for: str = Field(min_length=5, max_length=500)
    key_tradeoff: str = Field(min_length=5, max_length=500)


class InvestmentComparisonItem(BaseModel):
    """Side-by-side comparison row for one investment option."""

    model_config = ConfigDict(extra="forbid")

    name: str
    category: str
    expected_annual_return_percent: Decimal
    risk_level: RiskLevel
    liquidity: LiquidityLevel
    lock_in_period_months: int
    recommended_horizon_months: int
    tax_implications: str
    capital_protection: str
    advantages: list[str]
    disadvantages: list[str]
    projected_future_value: Decimal | None = None
    projected_total_investment: Decimal | None = None
    projected_total_earnings: Decimal | None = None


class InvestmentComparisonExplanation(BaseModel):
    """AI-generated comparative analysis without picking winners."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=10, max_length=1500)
    key_differences: list[str] = Field(min_length=1, max_length=10)
    suitability_analysis: list[OptionSuitability] = Field(min_length=2, max_length=5)
    risk_tradeoffs: list[str] = Field(min_length=1, max_length=10)
    assumptions_and_missing_info: list[str] = Field(default_factory=list, max_length=10)


class InvestmentComparisonResponse(BaseModel):
    """Final unified response for investment comparison."""

    model_config = ConfigDict(extra="forbid")

    comparison_table: list[InvestmentComparisonItem]
    ai_explanation: InvestmentComparisonExplanation
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    disclaimer: Literal[COMPARISON_DISCLAIMER] = COMPARISON_DISCLAIMER

