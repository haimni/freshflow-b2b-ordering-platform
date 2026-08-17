"""Authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import get_db
from app.deps.auth import CurrentUser
from app.schemas.auth import AccessToken
from app.schemas.user import UserRead
from app.services import auth as auth_service

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/login",
    response_model=AccessToken,
)
def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    db: DatabaseSession,
) -> AccessToken:
    """Authenticate a user and return a bearer access token."""

    user = auth_service.authenticate_user(
        db,
        email=form_data.username,
        password=form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AccessToken(
        access_token=create_access_token(subject=user.id),
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserRead,
)
def read_current_user(
    current_user: CurrentUser,
) -> UserRead:
    """Return the currently authenticated user."""

    return current_user