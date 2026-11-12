from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class AnalysisHistory(Base):
    """
    Immutable snapshot of an AI Advisor recommendation session.
    Preserves historical financial context, generated recommendations,
    and document citations as they existed at generation time.
    """

    __tablename__ = "analysis_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    advisor_model: Mapped[str] = mapped_column(String(100), nullable=False)

    financial_context_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False
    )
    advisor_response_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False
    )
    evidence_references: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="analyses")

