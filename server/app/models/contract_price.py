"""Negotiated contract-price ORM model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, UniqueConstraint, func, text as sa_text
from sqlalchemy.dialects.mysql import BIGINT, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.contract import Contract
    from app.models.product import Product


class ContractPrice(Base):
    """A product-specific price override within one contract."""

    __tablename__ = "contract_prices"
    __table_args__ = (
        UniqueConstraint("contract_id", "product_id", name="uq_contract_prices_contract_product"),
        CheckConstraint("price >= 0", name="chk_contract_prices_price"),
        Index("idx_contract_prices_product_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    contract_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("contracts.id", name="fk_contract_prices_contract", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    product_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("products.id", name="fk_contract_prices_product", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=sa_text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )

    contract: Mapped[Contract] = relationship(back_populates="prices")
    product: Mapped[Product] = relationship(back_populates="contract_prices")
