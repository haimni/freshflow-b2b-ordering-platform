"""Schemas for administrator order operations."""

from pydantic import BaseModel, ConfigDict

from app.models.enums import OrderStatus
from app.schemas.order import OrderRead


class AdminOrderStatusUpdate(BaseModel):
    """Requested administrator order status."""

    status: OrderStatus


class AdminOrderCustomerRead(BaseModel):
    """Customer identity shown with an administrator order."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    company_name: str


class AdminOrderRead(OrderRead):
    """Order details visible to an administrator."""

    customer: AdminOrderCustomerRead