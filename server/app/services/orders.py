"""Transactional customer order operations."""

from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.contract_price import ContractPrice
from app.models.enums import OrderStatus
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.services.customer_catalog import get_current_contract

MONEY_QUANTUM = Decimal("0.01")
MAX_ORDER_AMOUNT = Decimal("9999999999.99")


class ContractRequiredError(Exception):
    """Raised when a customer has no current contract."""


class ProductUnavailableError(Exception):
    """Raised when an ordered product cannot be purchased."""


class InsufficientStockError(Exception):
    """Raised when a product does not have enough stock."""

    def __init__(
        self,
        product_id: int,
    ) -> None:
        self.product_id = product_id

        super().__init__(
            f"Insufficient stock for product {product_id}"
        )


class OrderAmountTooLargeError(Exception):
    """Raised when an amount exceeds database precision."""


def create_order(
    db: Session,
    *,
    customer_id: int,
    created_by_user_id: int,
    requested_items: list[tuple[int, Decimal]],
) -> Order:
    """Create a pending order and reserve stock atomically."""

    try:
        contract = get_current_contract(
            db,
            customer_id=customer_id,
        )

        if contract is None:
            raise ContractRequiredError(
                "A current contract is required"
            )

        product_ids = sorted({
            product_id
            for product_id, _ in requested_items
        })

        if len(product_ids) != len(requested_items):
            raise ProductUnavailableError(
                "Duplicate products are not allowed"
            )

        product_statement = (
            select(Product)
            .where(
                Product.id.in_(product_ids),
                Product.active.is_(True),
            )
            .order_by(Product.id)
            .with_for_update()
        )

        products = list(
            db.scalars(product_statement).all()
        )

        if len(products) != len(product_ids):
            raise ProductUnavailableError(
                "One or more products are unavailable"
            )

        products_by_id = {
            product.id: product
            for product in products
        }

        price_statement = (
            select(
                ContractPrice.product_id,
                ContractPrice.price,
            )
            .where(
                ContractPrice.contract_id == contract.id,
                ContractPrice.product_id.in_(product_ids),
            )
            .with_for_update()
        )

        contract_prices = dict(
            db.execute(price_statement).all()
        )

        order = Order(
            customer_id=customer_id,
            contract_id=contract.id,
            created_by_user_id=created_by_user_id,
            total=Decimal("0.00"),
            status=OrderStatus.PENDING,
        )

        total = Decimal("0.00")

        for product_id, quantity in requested_items:
            product = products_by_id[product_id]

            if quantity > product.stock:
                raise InsufficientStockError(product_id)

            raw_unit_price = contract_prices.get(
                product_id,
                product.default_price,
            )

            unit_price = Decimal(raw_unit_price).quantize(
                MONEY_QUANTUM,
                rounding=ROUND_HALF_UP,
            )

            line_total = (
                quantity * unit_price
            ).quantize(
                MONEY_QUANTUM,
                rounding=ROUND_HALF_UP,
            )

            if line_total > MAX_ORDER_AMOUNT:
                raise OrderAmountTooLargeError(
                    "Order line exceeds maximum amount"
                )

            total += line_total

            if total > MAX_ORDER_AMOUNT:
                raise OrderAmountTooLargeError(
                    "Order total exceeds maximum amount"
                )

            product.stock -= quantity

            order.items.append(
                OrderItem(
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=unit_price,
                    line_total=line_total,
                )
            )

        order.total = total

        db.add(order)
        db.commit()

        return order

    except Exception:
        db.rollback()
        raise