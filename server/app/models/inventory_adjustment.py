"""Manual inventory-adjustment ORM model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.mysql import BIGINT, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class InventoryAdjustment(Base):
    """An auditable manual change to one product's stock."""

    __tablename__ = "inventory_adjustments"

    __table_args__ = (
        CheckConstraint(
            "quantity_change <> 0",
            name=(
                "chk_inventory_adjustments_"
                "quantity_change"
            ),
        ),
        CheckConstraint(
            "stock_before >= 0",
            name=(
                "chk_inventory_adjustments_"
                "stock_before"
            ),
        ),
        CheckConstraint(
            "stock_after >= 0",
            name=(
                "chk_inventory_adjustments_"
                "stock_after"
            ),
        ),
        CheckConstraint(
            "stock_after = stock_before + quantity_change",
            name=(
                "chk_inventory_adjustments_"
                "stock_balance"
            ),
        ),
        CheckConstraint(
            "CHAR_LENGTH(TRIM(reason)) > 0",
            name=(
                "chk_inventory_adjustments_"
                "reason"
            ),
        ),
        Index(
            "idx_inventory_adjustments_product_id",
            "product_id",
        ),
        Index(
            "idx_inventory_adjustments_"
            "performed_by_user_id",
            "performed_by_user_id",
        ),
        Index(
            "idx_inventory_adjustments_created_at",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
    )

    product_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "products.id",
            name=(
                "fk_inventory_adjustments_"
                "product"
            ),
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    performed_by_user_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "users.id",
            name=(
                "fk_inventory_adjustments_"
                "performed_by_user"
            ),
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    quantity_change: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
    )

    stock_before: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
    )

    stock_after: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    product: Mapped[Product] = relationship(
        back_populates="inventory_adjustments",
    )

    performed_by_user: Mapped[User] = relationship(
        back_populates="inventory_adjustments",
    )