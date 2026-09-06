"""Schemas for manual inventory adjustments."""

from datetime import datetime
from decimal import Decimal
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class InventoryAdjustmentCreate(BaseModel):
    """Requested manual stock quantity change."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    quantity_change: Decimal = Field(
        max_digits=12,
        decimal_places=3,
    )

    reason: str = Field(
        min_length=1,
        max_length=500,
    )

    @model_validator(mode="after")
    def reject_zero_change(self) -> Self:
        """Require a real stock change."""

        if self.quantity_change == 0:
            raise ValueError(
                "quantity_change cannot be zero"
            )

        return self


class InventoryAdjustmentProductRead(BaseModel):
    """Product identity included in adjustment history."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    name: str


class InventoryAdjustmentUserRead(BaseModel):
    """Administrator identity included in adjustment history."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    name: str


class InventoryAdjustmentRead(BaseModel):
    """Stored manual inventory adjustment."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    product_id: int
    performed_by_user_id: int
    quantity_change: Decimal
    stock_before: Decimal
    stock_after: Decimal
    reason: str
    created_at: datetime

    product: InventoryAdjustmentProductRead
    performed_by_user: InventoryAdjustmentUserRead