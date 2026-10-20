from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.goal import GoalCreate, GoalResponse, GoalUpdate
from app.services.goal_service import (
    create_goal,
    delete_goal,
    get_goal,
    get_goals,
    update_goal,
)

router = APIRouter(prefix="/goals", tags=["Financial Goals"])


@router.post(
    "",
    response_model=GoalResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_financial_goal(
    payload: GoalCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return create_goal(db, current_user.id, payload)


@router.get("", response_model=list[GoalResponse])
def list_financial_goals(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return get_goals(db, current_user.id)


@router.get("/{goal_id}", response_model=GoalResponse)
def read_financial_goal(
    goal_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    goal = get_goal(db, current_user.id, goal_id)
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found.",
        )
    return goal


@router.put("/{goal_id}", response_model=GoalResponse)
def update_financial_goal(
    goal_id: int,
    payload: GoalUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    goal = update_goal(db, current_user.id, goal_id, payload)
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found.",
        )
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_financial_goal(
    goal_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    deleted = delete_goal(db, current_user.id, goal_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found.",
        )
    return None
