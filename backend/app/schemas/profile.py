from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProfileUpdate(BaseModel):
    age: Optional[int] = Field(default=None, ge=18, le=120)
    monthly_income: Optional[Decimal] = Field(
        default=None, ge=Decimal("0"), max_digits=14, decimal_places=2
    )
    monthly_expenses: Optional[Decimal] = Field(
        default=None, ge=Decimal("0"), max_digits=14, decimal_places=2
    )
    savings: Optional[Decimal] = Field(
        default=None, ge=Decimal("0"), max_digits=14, decimal_places=2
    )
    existing_investments: Optional[Decimal] = Field(
        default=None, ge=Decimal("0"), max_digits=14, decimal_places=2
    )
    monthly_investment_capacity: Optional[Decimal] = Field(
        default=None, ge=Decimal("0"), max_digits=14, decimal_places=2
    )

    @model_validator(mode="after")
    def validate_financial_values(self):
        if (
            self.monthly_income is not None
            and self.monthly_expenses is not None
            and self.monthly_expenses > self.monthly_income
        ):
            raise ValueError("Monthly expenses cannot exceed monthly income.")
        return self


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    age: Optional[int] = None
    monthly_income: Optional[Decimal] = None
    monthly_expenses: Optional[Decimal] = None
    savings: Optional[Decimal] = None
    existing_investments: Optional[Decimal] = None
    monthly_investment_capacity: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
