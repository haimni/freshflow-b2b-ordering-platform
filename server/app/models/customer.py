"""Customer organization ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, UniqueConstraint, func, text
from sqlalchemy.dialects.mysql import BIGINT, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.contract import Contract
    from app.models.order import Order
    from app.models.user import User


class Customer(Base):
    """A business organization that buys products through FreshFlow."""

    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("business_number", name="uq_customers_business_number"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))
    business_number: Mapped[str] = mapped_column(String(30), nullable=False)
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )

    users: Mapped[list[User]] = relationship(back_populates="customer")
    contracts: Mapped[list[Contract]] = relationship(back_populates="customer")
    orders: Mapped[list[Order]] = relationship(back_populates="customer")
