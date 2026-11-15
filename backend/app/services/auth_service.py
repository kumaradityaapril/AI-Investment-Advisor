
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models import User


def register_user(
    db: Session,
    email: str,
    password: str,
    name: str | None = None,
) -> User:
    normalized_email = email.strip().lower()

    existing_user = db.scalars(
        select(User).where(User.email == normalized_email)
    ).first()

    if existing_user:
        raise ValueError("An account with this email already exists.")

    user = User(
        email=normalized_email,
        name=name.strip() if name and name.strip() else None,
        hashed_password=hash_password(password),
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except Exception as err:
        db.rollback()
        err_str = str(err).lower()
        # Auto-heal: If database schema was missing 'name' column, add it and retry once
        if "name" in err_str and "column" in err_str:
            try:
                db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(255);"))
                db.commit()
                db.add(user)
                db.commit()
                db.refresh(user)
                return user
            except Exception:
                db.rollback()
                raise
        raise

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    normalized_email = email.strip().lower()

    user = db.scalars(
        select(User).where(User.email == normalized_email)
    ).first()

    if user is None:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(
            minutes=settings.access_token_expire_minutes
        ),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
