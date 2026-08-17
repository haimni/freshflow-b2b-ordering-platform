"""Shared enum values stored by the FreshFlow database."""

from enum import Enum


class UserRole(str, Enum):
    """Authorization roles supported by the platform."""

    ADMIN = "admin"
    CUSTOMER_MANAGER = "customer_manager"
    CUSTOMER_USER = "customer_user"


class OrderStatus(str, Enum):
    """Allowed states in the order workflow."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
