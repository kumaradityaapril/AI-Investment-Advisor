import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.research_agent import ResearchReport, ResearchRequest
from app.services.research_agent_service import (
    ResearchAgentError,
    run_research_agent,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/research",
    tags=["AI Research Agent"],
)


@router.post(
    "",
    response_model=ResearchReport,
    status_code=status.HTTP_200_OK,
)
def run_research(
    request: ResearchRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Execute autonomous AI research using bounded tools:
    - Investor indexed financial documents (RAG)
    - Deterministic financial calculations
    - Verified Indian financial information and regulatory facts
    """
    try:
        return run_research_agent(
            db=db,
            user_id=current_user.id,
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ResearchAgentError as exc:
        logger.exception("Research execution failed for user %s: %s", current_user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Research agent execution failed: {exc}",
        ) from exc

