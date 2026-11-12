import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.scenario_simulation import (
    ScenarioSimulationRequest,
    ScenarioSimulationResponse,
    ScenarioTemplateItem,
)
from app.services.scenario_simulator_service import (
    PREDEFINED_SCENARIO_TEMPLATES,
    ScenarioSimulationError,
    run_scenario_simulation,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/scenarios",
    tags=["Financial Scenario Simulator"],
)


@router.get(
    "/templates",
    response_model=list[ScenarioTemplateItem],
    status_code=status.HTTP_200_OK,
)
def get_scenario_templates():
    """
    Retrieve pre-configured scenario templates for quick simulation:
    - Step up monthly SIP by ₹5,000
    - Deploy ₹1,00,000 lump sum bonus
    - Trim expenses by ₹4,000 and redirect to SIP
    - Conservative market return stress test (7%)
    - Extended 15-year compounding horizon
    """
    return PREDEFINED_SCENARIO_TEMPLATES


@router.post(
    "/simulate",
    response_model=ScenarioSimulationResponse,
    status_code=status.HTTP_200_OK,
)
def simulate_financial_scenario(
    request: ScenarioSimulationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Run deterministic financial scenario simulation and generate AI-grounded explanation.
    """
    try:
        return run_scenario_simulation(
            db=db,
            user_id=current_user.id,
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ScenarioSimulationError as exc:
        logger.exception("Scenario simulation failed for user %s: %s", current_user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario simulation error: {exc}",
        ) from exc

