from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Goal
from app.schemas.goal import GoalCreate, GoalUpdate


def create_goal(
    db: Session,
    user_id: int,
    payload: GoalCreate,
) -> Goal:
    goal = Goal(
        user_id=user_id,
        **payload.model_dump(),
    )
    db.add(goal)
    try:
        db.commit()
        db.refresh(goal)
    except Exception:
        db.rollback()
        raise
    return goal


def get_goals(db: Session, user_id: int) -> list[Goal]:
    statement = (
        select(Goal)
        .where(Goal.user_id == user_id)
        .order_by(Goal.created_at.desc())
    )
    return list(db.scalars(statement).all())


def get_goal(db: Session, user_id: int, goal_id: int) -> Goal | None:
    statement = select(Goal).where(
        Goal.id == goal_id,
        Goal.user_id == user_id,
    )
    return db.scalars(statement).first()


def update_goal(
    db: Session,
    user_id: int,
    goal_id: int,
    payload: GoalUpdate,
) -> Goal | None:
    goal = get_goal(db, user_id, goal_id)
    if goal is None:
        return None

    update_data = payload.model_dump()
    for field, value in update_data.items():
        setattr(goal, field, value)

    try:
        db.commit()
        db.refresh(goal)
    except Exception:
        db.rollback()
        raise
    return goal


def delete_goal(db: Session, user_id: int, goal_id: int) -> bool:
    goal = get_goal(db, user_id, goal_id)
    if goal is None:
        return False

    try:
        db.delete(goal)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
