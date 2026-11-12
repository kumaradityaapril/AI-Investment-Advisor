import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.investment_comparison import (
    InvestmentComparisonRequest,
    InvestmentComparisonResponse,
)
from app.services.financial_context_service import build_financial_context
from app.services.investment_comparison_service import (
    InvestmentComparisonError,
    compare_investments,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/investment-comparison",
    tags=["Investment Comparison"],
)


@router.post(
    "/compare",
    response_model=InvestmentComparisonResponse,
    status_code=status.HTTP_200_OK,
)
def compare_investment_options(
    request: InvestmentComparisonRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Compare 2 to 5 investment options side-by-side.

    Provides:
    - Deterministic side-by-side comparison (liquidity, risk, lock-in, tax, capital protection).
    - Deterministic future value projections if investment amount & horizon are supplied.
    - AI-generated objective comparative analysis tailored to investor profile without declaring a winner.
    - Standard educational disclaimer.
    """
    # Attempt to load investor context for personalized suitability analysis
    financial_context = None
    try:
        financial_context = build_financial_context(db=db, user_id=current_user.id)
    except Exception as exc:
        logger.warning(
            "Could not load financial context for user %s during comparison: %s",
            current_user.id,
            exc,
        )

    try:
        return compare_investments(
            request=request,
            financial_context=financial_context,
        )
    except InvestmentComparisonError as exc:
        logger.exception("Investment comparison failed for user %s.", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Investment comparison failed: {exc}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

