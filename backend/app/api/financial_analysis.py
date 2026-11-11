
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.financial_context import FinancialContext
from app.services.financial_context_service import (
    build_financial_context,
    FinancialContextError,
)

router = APIRouter(
    prefix="/financial-analysis",
    tags=["Financial Analysis"],
)


@router.get(
    "/me",
    response_model=FinancialContext,
)
def get_my_financial_analysis(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Return the authenticated investor's complete financial analysis.

    Includes:
    - Financial profile
    - Financial goals
    - Latest risk assessment
    - Processed and indexed documents
    - Deterministic financial metrics
    - Goal contribution analysis
    """

    try:
        return build_financial_context(
            db=db,
            user_id=current_user.id,
        )

    except FinancialContextError as exc:
        if str(exc) == "Investor not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Investor not found.",
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate financial analysis.",
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
