"""Sellable product ORM model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Numeric, String, Text, func, text
from sqlalchemy.dialects.mysql import BIGINT, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.contract_price import ContractPrice
    from app.models.order_item import OrderItem


class Product(Base):
    """A catalog item with a fallback price and current stock quantity."""

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("default_price >= 0", name="chk_products_default_price"),
        CheckConstraint("stock >= 0", name="chk_products_stock"),
        Index("idx_products_category_id", "category_id"),
        Index("idx_products_active", "active"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    category_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("categories.id", name="fk_products_category", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    default_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, server_default=text("0"))
    image_url: Mapped[str | None] = mapped_column(String(2048))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )

    category: Mapped[Category] = relationship(back_populates="products")
    contract_prices: Mapped[list[ContractPrice]] = relationship(back_populates="product")
    order_items: Mapped[list[OrderItem]] = relationship(back_populates="product")
