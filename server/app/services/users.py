"""Database operations for user administration."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def list_users(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 100,
) -> list[User]:
    """Return application users ordered by ID."""

    statement = (
        select(User)
        .order_by(User.id)
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(statement).all())