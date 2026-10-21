from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RiskAnswer = int


class RiskAssessmentRequest(BaseModel):
    investment_experience: RiskAnswer = Field(ge=0, le=4)
    time_horizon: RiskAnswer = Field(ge=0, le=4)
    loss_reaction: RiskAnswer = Field(ge=0, le=4)
    growth_preference: RiskAnswer = Field(ge=0, le=4)
    financial_stability: RiskAnswer = Field(ge=0, le=4)


class RiskAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    answers: dict[str, int]
    risk_score: int = Field(ge=0, le=20)
    risk_category: Literal["conservative", "moderate", "aggressive"]
    assessed_at: datetime
    disclaimer: str = (
        "Educational risk-tolerance indicator only. "
        "This result is not financial advice or a guarantee of investment suitability. "
        "Consider your financial circumstances, goals, and ability to absorb losses."
    )
