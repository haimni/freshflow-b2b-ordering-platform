"""Schemas for administrator order operations."""

from pydantic import BaseModel

from app.models.enums import OrderStatus


class AdminOrderStatusUpdate(BaseModel):
    """Requested administrator order status."""

    status: OrderStatus