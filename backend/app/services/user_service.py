
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def create_user(
    db: Session,
    email: str,
    hashed_password: str,
) -> User:
    user = User(
        email=email,
        hashed_password=hashed_password,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return db.scalars(statement).first()


def update_user_email(
    db: Session,
    user_id: int,
    new_email: str,
) -> User | None:
    user = db.get(User, user_id)

    if user is None:
        return None

    user.email = new_email
    db.commit()
    db.refresh(user)

    return user


def delete_user(db: Session, user_id: int) -> bool:
    user = db.get(User, user_id)

    if user is None:
        return False

    db.delete(user)
    db.commit()

    return True
