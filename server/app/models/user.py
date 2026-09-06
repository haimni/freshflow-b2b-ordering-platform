"""Authenticated user ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.mysql import BIGINT, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.order import Order
    from app.models.inventory_adjustment import (
        InventoryAdjustment,
    )


class User(Base):
    """An internal administrator or a representative of one customer."""

    __tablename__ = "users"

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint(
            "(role = 'admin' AND customer_id IS NULL) OR "
            "(role IN ('customer_manager', 'customer_user') "
            "AND customer_id IS NOT NULL)",
            name="chk_users_role_customer",
        ),
        Index("idx_users_customer_id", "customer_id"),
        Index("idx_users_role", "role"),
    )

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
    )

    customer_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "customers.id",
            name="fk_users_customer",
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SqlEnum(
            UserRole,
            name="user_role",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("1"),
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text(
            "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        ),
    )

    customer: Mapped[Customer | None] = relationship(
        back_populates="users",
    )

    created_orders: Mapped[list[Order]] = relationship(
        back_populates="created_by_user",
    )

    inventory_adjustments: Mapped[
    list[InventoryAdjustment]
    ] = relationship(
        back_populates="performed_by_user",
    )