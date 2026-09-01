"""Schemas for creating and returning customer orders."""

from datetime import datetime
from decimal import Decimal
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.models.enums import OrderStatus


class OrderItemCreate(BaseModel):
    """One requested product and quantity."""

    product_id: int = Field(gt=0)

    quantity: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=3,
    )


class OrderCreate(BaseModel):
    """Customer order request."""

    items: list[OrderItemCreate] = Field(
        min_length=1,
        max_length=100,
    )

    @model_validator(mode="after")
    def reject_duplicate_products(self) -> Self:
        """Reject repeated products in one order."""

        product_ids = [
            item.product_id
            for item in self.items
        ]

        if len(product_ids) != len(set(product_ids)):
            raise ValueError(
                "Each product may appear only once per order"
            )

        return self


class OrderItemRead(BaseModel):
    """Stored order-item price snapshot."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    product_id: int
    product_name: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


class OrderRead(BaseModel):
    """Customer order response."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    customer_id: int
    contract_id: int
    created_by_user_id: int
    total: Decimal
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead]