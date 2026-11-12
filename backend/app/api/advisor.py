import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.ai_advisor import AIAdvisorRequest, AIAdvisorResponse
from app.schemas.analysis_history import (
    AnalysisHistoryDetail,
    AnalysisHistoryListResponse,
)
from app.schemas.analysis_diff import (
    AnalysisDiffRequest,
    AnalysisDiffResponse,
)
from app.schemas.research_agent import ResearchReport, ResearchRequest
from app.services.analysis_diff_service import (
    AnalysisDiffError,
    compute_analysis_diff,
)
from app.services.research_agent_service import (
    ResearchAgentError,
    run_research_agent,
)
from app.services.advisor_orchestration_service import (
    AdvisorOrchestrationError,
    get_ai_advisor_response,
)
from app.services.analysis_history_service import (
    AnalysisHistoryError,
    delete_user_analysis,
    get_user_analysis_by_id,
    list_user_analyses,
    save_analysis_history,
)
from app.services.financial_context_service import build_financial_context

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/advisor",
    tags=["AI Advisor & Analysis History"],
)


@router.post(
    "/analyze",
    response_model=AIAdvisorResponse,
    status_code=status.HTTP_200_OK,
)
def run_advisor_analysis(
    request: AIAdvisorRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    response: Response,
):
    """
    Run personalized, grounded AI Advisor analysis and automatically
    persist an immutable snapshot to history.
    """
    try:
        advisor_response = get_ai_advisor_response(
            db=db,
            user_id=current_user.id,
            request=request,
        )

        financial_context = build_financial_context(
            db=db,
            user_id=current_user.id,
        )

        saved_history = save_analysis_history(
            db=db,
            user_id=current_user.id,
            question=request.question,
            response=advisor_response,
            financial_context=financial_context,
        )

        response.headers["X-Analysis-Id"] = str(saved_history.id)
        return advisor_response

    except AdvisorOrchestrationError as exc:
        logger.exception("AI Advisor orchestration failed for user %s.", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Advisor analysis failed: {exc}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/history",
    response_model=AnalysisHistoryListResponse,
    status_code=status.HTTP_200_OK,
)
def get_advisor_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    """
    Retrieve previous advisor analyses for the authenticated investor.
    """
    try:
        items, total = list_user_analyses(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
        return AnalysisHistoryListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as exc:
        logger.exception("Failed to retrieve analysis history for user %s.", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis history.",
        ) from exc


@router.post(
    "/history/diff",
    response_model=AnalysisDiffResponse,
    status_code=status.HTTP_200_OK,
)
def compare_analysis_snapshots(
    request: AnalysisDiffRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Compare two historical financial analyses for the authenticated investor.
    Calculates deterministic metric deltas, risk shifts, goal progress differences,
    and identifies potentially obsolete advice.
    """
    try:
        return compute_analysis_diff(
            db=db,
            user_id=current_user.id,
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except AnalysisDiffError as exc:
        logger.exception("Analysis diff failed for user %s.", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis diff failed: {exc}",
        ) from exc


@router.post(
    "/research",
    response_model=ResearchReport,
    status_code=status.HTTP_200_OK,
)
def run_advisor_research(
    request: ResearchRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Execute autonomous AI research across financial documents,
    deterministic calculations, and verified regulatory information.
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
        logger.exception("AI research failed for user %s: %s", current_user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Research agent error: {exc}",
        ) from exc


@router.get(
    "/history/{analysis_id}",
    response_model=AnalysisHistoryDetail,
    status_code=status.HTTP_200_OK,
)
def get_advisor_analysis_detail(
    analysis_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Retrieve one previous analysis with its complete context and response snapshot.
    Enforces user ownership.
    """
    record = get_user_analysis_by_id(
        db=db,
        user_id=current_user.id,
        analysis_id=analysis_id,
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis {analysis_id} not found.",
        )

    return AnalysisHistoryDetail(
        id=record.id,
        user_id=record.user_id,
        question=record.question,
        advisor_model=record.advisor_model,
        financial_context_snapshot=record.financial_context_snapshot,
        advisor_response_snapshot=record.advisor_response_snapshot,
        evidence_references=record.evidence_references,
        created_at=record.created_at,
    )


@router.delete(
    "/history/{analysis_id}",
    status_code=status.HTTP_200_OK,
)
def delete_advisor_analysis(
    analysis_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Delete a saved analysis. Enforces user ownership.
    """
    try:
        deleted = delete_user_analysis(
            db=db,
            user_id=current_user.id,
            analysis_id=analysis_id,
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis {analysis_id} not found.",
            )

        return {"detail": "Analysis deleted successfully."}

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to delete analysis %s.", analysis_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete analysis.",
        ) from exc

