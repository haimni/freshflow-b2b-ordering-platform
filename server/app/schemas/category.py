"""Pydantic schemas for product categories."""

from pydantic import BaseModel, ConfigDict


class CategoryRead(BaseModel):
    """Category data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    active: bool