from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Profile
from app.schemas.profile import ProfileUpdate


def get_profile(db: Session, user_id: int) -> Profile | None:
    statement = select(Profile).where(Profile.user_id == user_id)
    return db.scalars(statement).first()


def upsert_profile(
    db: Session,
    user_id: int,
    payload: ProfileUpdate,
) -> Profile:
    profile = get_profile(db, user_id)
    if profile is None:
        profile = Profile(user_id=user_id)
        db.add(profile)

    update_data = payload.model_dump()
    for field, value in update_data.items():
        setattr(profile, field, value)

    try:
        db.commit()
        db.refresh(profile)
    except Exception:
        db.rollback()
        raise

    return profile
