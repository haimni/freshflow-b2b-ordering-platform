"""Customer-specific catalog and contract pricing."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.models.contract_price import ContractPrice
from app.models.product import Product


class MultipleCurrentContractsError(Exception):
    """Raised when customer pricing is ambiguous."""


@dataclass(frozen=True, slots=True)
class PricedProduct:
    """A product combined with its effective customer price."""

    product: Product
    effective_price: Decimal
    price_source: Literal["contract", "default"]
    contract_id: int | None


def get_current_contract(
    db: Session,
    *,
    customer_id: int,
    on_date: date | None = None,
) -> Contract | None:
    """Return the single contract valid on the requested date."""

    effective_date = on_date or date.today()

    statement = (
        select(Contract)
        .where(
            Contract.customer_id == customer_id,
            Contract.active.is_(True),
            Contract.valid_from <= effective_date,
            or_(
                Contract.valid_until.is_(None),
                Contract.valid_until >= effective_date,
            ),
        )
        .order_by(
            Contract.valid_from.desc(),
            Contract.id.desc(),
        )
        .limit(2)
    )

    contracts = list(db.scalars(statement).all())

    if len(contracts) > 1:
        raise MultipleCurrentContractsError(
            f"Customer {customer_id} has multiple current contracts"
        )

    if not contracts:
        return None

    return contracts[0]


def list_customer_products(
    db: Session,
    *,
    customer_id: int,
    category_id: int | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[PricedProduct]:
    """Return active products with customer-specific prices."""

    contract = get_current_contract(
        db,
        customer_id=customer_id,
    )

    if contract is None:
        statement = (
            select(Product)
            .where(Product.active.is_(True))
            .order_by(Product.name)
        )

        if category_id is not None:
            statement = statement.where(
                Product.category_id == category_id
            )

        statement = statement.offset(offset).limit(limit)

        products = list(db.scalars(statement).all())

        return [
            PricedProduct(
                product=product,
                effective_price=product.default_price,
                price_source="default",
                contract_id=None,
            )
            for product in products
        ]

    statement = (
        select(
            Product,
            ContractPrice.price,
        )
        .outerjoin(
            ContractPrice,
            and_(
                ContractPrice.product_id == Product.id,
                ContractPrice.contract_id == contract.id,
            ),
        )
        .where(Product.active.is_(True))
        .order_by(Product.name)
    )

    if category_id is not None:
        statement = statement.where(
            Product.category_id == category_id
        )

    statement = statement.offset(offset).limit(limit)

    rows = db.execute(statement).all()

    return [
        PricedProduct(
            product=product,
            effective_price=(
                contract_price
                if contract_price is not None
                else product.default_price
            ),
            price_source=(
                "contract"
                if contract_price is not None
                else "default"
            ),
            contract_id=contract.id,
        )
        for product, contract_price in rows
    ]