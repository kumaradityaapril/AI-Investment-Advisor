from uuid import uuid4
from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal
from app.services.user_service import (
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    update_user_email,
)


def test_user_crud():
    db = SessionLocal()
    user_id = None
    original_email = f"crud-test-{uuid4().hex}@example.com"
    updated_email = f"crud-updated-{uuid4().hex}@example.com"

    try:
        # CREATE
        user = create_user(
            db,
            email=original_email,
            hashed_password="test-hash-not-a-real-password",
        )
        user_id = user.id
        assert user.id is not None
        print("CREATE: PASS")

        # READ BY ID
        fetched_user = get_user_by_id(db, user_id)
        assert fetched_user is not None
        assert fetched_user.email == original_email
        print("READ BY ID: PASS")

        # READ BY EMAIL
        fetched_by_email = get_user_by_email(db, original_email)
        assert fetched_by_email is not None
        assert fetched_by_email.id == user_id
        print("READ BY EMAIL: PASS")

        # UPDATE
        updated_user = update_user_email(
            db, user_id, updated_email
        )
        assert updated_user is not None
        assert updated_user.email == updated_email
        print("UPDATE: PASS")

        # DELETE
        deleted = delete_user(db, user_id)
        assert deleted is True
        user_id = None
        assert get_user_by_id(db, updated_user.id) is None
        print("DELETE: PASS")

        # NON-EXISTENT USER
        assert get_user_by_id(db, -1) is None
        assert delete_user(db, -1) is False
        print("MISSING USER HANDLING: PASS")

    finally:
        # Cleanup if an earlier assertion fails.
        if user_id is not None:
            try:
                delete_user(db, user_id)
            except IntegrityError:
                db.rollback()
                raise
        db.close()


if __name__ == "__main__":
    test_user_crud()
    print("\nAll CRUD checks passed!")
