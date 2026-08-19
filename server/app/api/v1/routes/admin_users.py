"""Administrator-only user endpoints."""

from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps.auth import CurrentAdmin
from app.schemas.user import UserRead
from app.services import users as user_service
from fastapi import Depends

router = APIRouter(
    prefix="/admin/users",
    tags=["administration"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get(
    "",
    response_model=list[UserRead],
)
def read_users(
    current_admin: CurrentAdmin,
    db: DatabaseSession,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[UserRead]:
    """Return users to an authenticated administrator."""

    return user_service.list_users(
        db,
        offset=offset,
        limit=limit,
    )