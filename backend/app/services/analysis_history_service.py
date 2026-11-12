import logging
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.analysis_history import AnalysisHistory
from app.schemas.ai_advisor import AIAdvisorResponse
from app.schemas.analysis_history import (
    AnalysisHistoryDetail,
    AnalysisHistorySummary,
)
from app.schemas.financial_context import FinancialContext

logger = logging.getLogger(__name__)


class AnalysisHistoryError(Exception):
    """Raised when analysis history operations fail."""


def save_analysis_history(
    db: Session,
    user_id: int,
    question: str,
    response: AIAdvisorResponse,
    financial_context: FinancialContext,
    advisor_model: str = settings.advisor_model,
) -> AnalysisHistory:
    """
    Save an immutable snapshot of an advisor analysis session.
    """
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise ValueError("Invalid user ID.")

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    try:
        context_snapshot = financial_context.model_dump(mode="json")
        response_snapshot = response.model_dump(mode="json")
        evidence_snapshot = [
            ev.model_dump(mode="json") for ev in response.evidence
        ]

        record = AnalysisHistory(
            user_id=user_id,
            question=question.strip(),
            advisor_model=advisor_model,
            financial_context_snapshot=context_snapshot,
            advisor_response_snapshot=response_snapshot,
            evidence_references=evidence_snapshot,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        logger.info(
            "Saved analysis history id=%s for user_id=%s",
            record.id,
            user_id,
        )
        return record

    except Exception as exc:
        db.rollback()
        logger.exception("Failed to save analysis history for user %s.", user_id)
        raise AnalysisHistoryError(
            f"Failed to save analysis history: {exc}"
        ) from exc


def list_user_analyses(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[AnalysisHistorySummary], int]:
    """
    List previous analysis sessions for the authenticated user.
    """
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise ValueError("Invalid user ID.")

    count_stmt = (
        select(func.count(AnalysisHistory.id))
        .where(AnalysisHistory.user_id == user_id)
    )
    total = db.scalar(count_stmt) or 0

    stmt = (
        select(AnalysisHistory)
        .where(AnalysisHistory.user_id == user_id)
        .order_by(desc(AnalysisHistory.created_at))
        .offset(skip)
        .limit(limit)
    )

    records = db.scalars(stmt).all()

    items = []
    for r in records:
        resp = r.advisor_response_snapshot or {}
        overall = resp.get("overall_assessment", "")
        recs = resp.get("recommendations", [])
        items.append(
            AnalysisHistorySummary(
                id=r.id,
                user_id=r.user_id,
                question=r.question,
                advisor_model=r.advisor_model,
                overall_assessment=overall,
                recommendations_count=len(recs),
                created_at=r.created_at,
            )
        )

    return items, total


def get_user_analysis_by_id(
    db: Session,
    user_id: int,
    analysis_id: int,
) -> AnalysisHistory | None:
    """
    Retrieve one analysis session, strictly enforcing user ownership.
    """
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise ValueError("Invalid user ID.")

    if not isinstance(analysis_id, int) or isinstance(analysis_id, bool) or analysis_id <= 0:
        raise ValueError("Invalid analysis ID.")

    stmt = select(AnalysisHistory).where(
        AnalysisHistory.id == analysis_id,
        AnalysisHistory.user_id == user_id,
    )
    return db.scalars(stmt).first()


def delete_user_analysis(
    db: Session,
    user_id: int,
    analysis_id: int,
) -> bool:
    """
    Delete one saved analysis session, strictly enforcing user ownership.
    """
    record = get_user_analysis_by_id(db, user_id=user_id, analysis_id=analysis_id)
    if record is None:
        return False

    try:
        db.delete(record)
        db.commit()
        logger.info(
            "Deleted analysis history id=%s for user_id=%s",
            analysis_id,
            user_id,
        )
        return True
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Failed to delete analysis history %s for user %s.",
            analysis_id,
            user_id,
        )
        raise AnalysisHistoryError(
            f"Failed to delete analysis history: {exc}"
        ) from exc

