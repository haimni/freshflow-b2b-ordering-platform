"""Pydantic schemas for application users."""

from pydantic import BaseModel, ConfigDict

from app.models.enums import UserRole


class UserRead(BaseModel):
    """Authenticated user information returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int | None
    name: str
    email: str
    role: UserRole
    active: bool