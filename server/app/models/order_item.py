"""Order line-item ORM model."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.product import Product


class OrderItem(Base):
    """An immutable quantity and price snapshot belonging to one order."""

    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint("order_id", "product_id", name="uq_order_items_order_product"),
        CheckConstraint("quantity > 0", name="chk_order_items_quantity"),
        CheckConstraint("unit_price >= 0", name="chk_order_items_unit_price"),
        CheckConstraint("line_total >= 0", name="chk_order_items_line_total"),
        Index("idx_order_items_product_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    order_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("orders.id", name="fk_order_items_order", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    product_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("products.id", name="fk_order_items_product", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="order_items")
