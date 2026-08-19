"""Order header ORM model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Numeric,
    func,
    text,
)
from sqlalchemy.dialects.mysql import BIGINT, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import OrderStatus

if TYPE_CHECKING:
    from app.models.contract import Contract
    from app.models.customer import Customer
    from app.models.order_item import OrderItem
    from app.models.user import User


class Order(Base):
    """An order created under one customer contract."""

    __tablename__ = "orders"

    __table_args__ = (
        CheckConstraint(
            "total >= 0",
            name="chk_orders_total",
        ),
        Index(
            "idx_orders_customer_id",
            "customer_id",
        ),
        Index(
            "idx_orders_contract_id",
            "contract_id",
        ),
        Index(
            "idx_orders_created_by_user_id",
            "created_by_user_id",
        ),
        Index(
            "idx_orders_status",
            "status",
        ),
        Index(
            "idx_orders_created_at",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
    )

    customer_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "customers.id",
            name="fk_orders_customer",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    contract_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "contracts.id",
            name="fk_orders_contract",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    created_by_user_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "users.id",
            name="fk_orders_created_by_user",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    status: Mapped[OrderStatus] = mapped_column(
        SqlEnum(
            OrderStatus,
            name="order_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        server_default=text("'pending'"),
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

    customer: Mapped[Customer] = relationship(
        back_populates="orders",
    )

    contract: Mapped[Contract] = relationship(
        back_populates="orders",
    )

    created_by_user: Mapped[User] = relationship(
        back_populates="created_orders",
    )

    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order",
    )