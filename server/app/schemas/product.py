"""Pydantic schemas for catalog products."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductRead(BaseModel):
    """Product data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    name: str
    description: str | None
    default_price: Decimal
    stock: Decimal
    image_url: str | None
    active: bool