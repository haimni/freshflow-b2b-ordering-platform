"""Authentication-related database operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    """Return a user by normalized email address."""

    normalized_email = email.strip().lower()

    statement = select(User).where(
        User.email == normalized_email
    )

    return db.scalar(statement)


def authenticate_user(
    db: Session,
    *,
    email: str,
    password: str,
) -> User | None:
    """Authenticate an active user with email and password."""

    user = get_user_by_email(db, email)

    if user is None:
        return None

    if not user.active:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user