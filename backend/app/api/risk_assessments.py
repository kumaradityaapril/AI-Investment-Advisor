
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.risk_assessment import (
    RiskAssessmentRequest,
    RiskAssessmentResponse,
)
from app.services.risk_assessment_service import (
    create_risk_assessment,
    get_latest_risk_assessment,
)

router = APIRouter(
    prefix="/risk-assessments",
    tags=["Risk Assessment"],
)


@router.post(
    "",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_risk_assessment(
    payload: RiskAssessmentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return create_risk_assessment(
        db=db,
        user_id=current_user.id,
        payload=payload,
    )


@router.get(
    "/latest",
    response_model=RiskAssessmentResponse,
)
def read_latest_risk_assessment(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    assessment = get_latest_risk_assessment(
        db=db,
        user_id=current_user.id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No risk assessment found. Please complete the questionnaire first.",
        )

    return assessment
