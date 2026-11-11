
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


REQUIRED_RISK_FACTORS = {
    "investment_experience",
    "time_horizon",
    "loss_reaction",
    "growth_preference",
    "financial_stability",
}


class InvestorProfileContext(BaseModel):
    age: int | None = None
    monthly_income: Decimal | None = None
    monthly_expenses: Decimal | None = None
    savings: Decimal | None = None
    existing_investments: Decimal | None = None
    monthly_investment_capacity: Decimal | None = None


class InvestorGoalContext(BaseModel):
    id: int
    title: str
    goal_type: str
    target_amount: Decimal
    time_horizon_months: int
    planned_monthly_investment: Decimal | None = None


class InvestorRiskContext(BaseModel):
    risk_score: int = Field(ge=0, le=20)
    risk_category: Literal[
        "conservative",
        "moderate",
        "aggressive",
    ]
    answers: dict[
        Literal[
            "investment_experience",
            "time_horizon",
            "loss_reaction",
            "growth_preference",
            "financial_stability",
        ],
        int,
    ]
    assessed_at: datetime

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, v: dict[str, int]) -> dict[str, int]:
        missing = REQUIRED_RISK_FACTORS - set(v.keys())
        if missing:
            raise ValueError(f"Missing required risk assessment answers: {missing}")
        for key, val in v.items():
            if not isinstance(val, int) or not (0 <= val <= 4):
                raise ValueError(
                    f"Answer for '{key}' must be an integer between 0 and 4."
                )
        return v


class InvestorDocumentContext(BaseModel):
    id: int
    filename: str
    status: str
    indexing_status: str
    indexed_at: datetime | None = None


class FinancialMetricsContext(BaseModel):
    monthly_surplus: Decimal | None = None
    annual_income: Decimal | None = None
    annual_expenses: Decimal | None = None
    savings_rate_percent: Decimal | None = None
    expense_ratio_percent: Decimal | None = None


class FinancialGoalAnalysis(BaseModel):
    goal_id: int
    goal_title: str
    required_monthly_contribution: Decimal
    planned_monthly_investment: Decimal | None = None
    monthly_contribution_shortfall: Decimal | None = None


class FinancialContext(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    profile: InvestorProfileContext | None = None
    goals: list[InvestorGoalContext] = Field(default_factory=list)
    risk_assessment: InvestorRiskContext | None = None
    documents: list[InvestorDocumentContext] = Field(default_factory=list)
    metrics: FinancialMetricsContext = Field(
        default_factory=FinancialMetricsContext
    )
    goal_analysis: list[FinancialGoalAnalysis] = Field(
        default_factory=list
    )
    generated_at: datetime
