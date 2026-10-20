from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services.profile_service import get_profile, upsert_profile

router = APIRouter(prefix="/profile", tags=["Financial Profile"])


@router.get("/me", response_model=ProfileResponse)
def read_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    profile = get_profile(db, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial profile not found. Create one using PUT /profile/me.",
        )
    return profile


@router.put("/me", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return upsert_profile(db, current_user.id, payload)
