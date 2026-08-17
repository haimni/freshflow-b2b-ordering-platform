"""Authentication and authorization dependencies."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login"
)

DatabaseSession = Annotated[Session, Depends(get_db)]
BearerToken = Annotated[str, Depends(oauth2_scheme)]


def credentials_exception() -> HTTPException:
    """Create the standard invalid-credentials response."""

    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: BearerToken,
    db: DatabaseSession,
) -> User:
    """Return the active user represented by a valid access token."""

    try:
        user_id = decode_access_token(token)
    except InvalidTokenError as error:
        raise credentials_exception() from error

    user = db.get(User, user_id)

    if user is None or not user.active:
        raise credentials_exception()

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(
    *allowed_roles: UserRole,
) -> Callable[..., User]:
    """Create a dependency that permits only selected roles."""

    def role_dependency(
        current_user: CurrentUser,
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_dependency