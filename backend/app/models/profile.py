from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    age: Mapped[Optional[int]] = mapped_column(Integer)
    monthly_income: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    monthly_expenses: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    savings: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    existing_investments: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(14, 2)
    )
    monthly_investment_capacity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(14, 2)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")
