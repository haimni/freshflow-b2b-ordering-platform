"""Schemas for the customer-specific catalog."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class CustomerProductRead(BaseModel):
    """Product with the effective price for one customer."""

    id: int
    category_id: int
    name: str
    description: str | None
    stock: Decimal
    image_url: str | None
    effective_price: Decimal
    price_source: Literal["contract", "default"]
    contract_id: int | None