"""Customer contract ORM model."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.dialects.mysql import BIGINT, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ContractType

if TYPE_CHECKING:
    from app.models.contract_price import ContractPrice
    from app.models.customer import Customer
    from app.models.order import Order


class Contract(Base):
    """A dated commercial agreement belonging to one customer."""

    __tablename__ = "contracts"

    __table_args__ = (
        CheckConstraint(
            "valid_until IS NULL OR valid_until >= valid_from",
            name="chk_contracts_dates",
        ),
        Index(
            "idx_contracts_customer_id",
            "customer_id",
        ),
        Index(
            "idx_contracts_customer_active",
            "customer_id",
            "active",
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
            name="fk_contracts_customer",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    contract_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    contract_type: Mapped[ContractType] = mapped_column(
        SqlEnum(
            ContractType,
            name="contract_type",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        server_default=text("'custom'"),
    )

    valid_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    valid_until: Mapped[date | None] = mapped_column(
        Date,
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

    customer: Mapped[Customer] = relationship(
        back_populates="contracts",
    )

    prices: Mapped[list[ContractPrice]] = relationship(
        back_populates="contract",
    )

    orders: Mapped[list[Order]] = relationship(
        back_populates="contract",
    )