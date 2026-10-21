
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RiskAssessment
from app.schemas.risk_assessment import RiskAssessmentRequest


def calculate_risk_score(payload: RiskAssessmentRequest) -> int:
    """Calculate a deterministic score from five validated answers."""
    answers = payload.model_dump()
    return sum(answers.values())


def categorize_risk(score: int) -> str:
    """Map a score from 0–20 to its predefined risk category."""
    if not 0 <= score <= 20:
        raise ValueError("Risk score must be between 0 and 20.")

    if score <= 6:
        return "conservative"
    if score <= 13:
        return "moderate"
    return "aggressive"


def create_risk_assessment(
    db: Session,
    user_id: int,
    payload: RiskAssessmentRequest,
) -> RiskAssessment:
    answers = payload.model_dump()
    score = calculate_risk_score(payload)
    category = categorize_risk(score)

    assessment = RiskAssessment(
        user_id=user_id,
        answers=answers,
        risk_score=score,
        risk_category=category,
    )

    db.add(assessment)

    try:
        db.commit()
        db.refresh(assessment)
    except Exception:
        db.rollback()
        raise

    return assessment


def get_latest_risk_assessment(
    db: Session,
    user_id: int,
) -> RiskAssessment | None:
    statement = (
        select(RiskAssessment)
        .where(RiskAssessment.user_id == user_id)
        .order_by(
            RiskAssessment.assessed_at.desc(),
            RiskAssessment.id.desc(),
        )
        .limit(1)
    )
    return db.scalars(statement).first()
