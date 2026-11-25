from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

GoalTitle = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=150),
]
GoalType = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=50),
]


class GoalCreate(BaseModel):
    title: GoalTitle
    goal_type: GoalType
    target_amount: Decimal = Field(
        gt=Decimal("0"),
        le=Decimal("100000000000"),
        max_digits=14,
        decimal_places=2,
        description="Target corpus up to ₹1,00,000 Crores",
    )
    time_horizon_months: int = Field(gt=0, le=600, description="Horizon up to 50 years")
    planned_monthly_investment: Decimal | None = Field(
        default=None,
        gt=Decimal("0"),
        le=Decimal("1000000000"),
        max_digits=14,
        decimal_places=2,
    )


class GoalUpdate(BaseModel):
    title: GoalTitle
    goal_type: GoalType
    target_amount: Decimal = Field(
        gt=Decimal("0"),
        le=Decimal("100000000000"),
        max_digits=14,
        decimal_places=2,
        description="Target corpus up to ₹1,00,000 Crores",
    )
    time_horizon_months: int = Field(gt=0, le=600, description="Horizon up to 50 years")
    planned_monthly_investment: Decimal | None = Field(
        default=None,
        gt=Decimal("0"),
        le=Decimal("1000000000"),
        max_digits=14,
        decimal_places=2,
    )


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    goal_type: str
    target_amount: Decimal
    time_horizon_months: int
    planned_monthly_investment: Decimal | None
    created_at: datetime
