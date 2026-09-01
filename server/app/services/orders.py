"""Transactional customer order operations."""

from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.contract_price import ContractPrice
from app.models.enums import OrderStatus
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.services.customer_catalog import get_current_contract

MONEY_QUANTUM = Decimal("0.01")
MAX_ORDER_AMOUNT = Decimal("9999999999.99")

CUSTOMER_CANCELLABLE_STATUSES = frozenset({
    OrderStatus.PENDING,
})

ADMIN_CANCELLABLE_STATUSES = frozenset({
    OrderStatus.PENDING,
    OrderStatus.CONFIRMED,
})


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


class OrderNotFoundError(Exception):
    """Raised when a customer order cannot be found."""


class OrderNotCancellableError(Exception):
    """Raised when an order cannot be cancelled."""

    def __init__(
        self,
        current_status: OrderStatus,
    ) -> None:
        self.current_status = current_status

        super().__init__(
            "Order cannot be cancelled from status "
            f"{current_status.value}"
        )


class OrderDataIntegrityError(Exception):
    """Raised when stored order data is inconsistent."""


def get_customer_orders(
    db: Session,
    *,
    customer_id: int,
    offset: int = 0,
    limit: int = 20,
) -> list[Order]:
    """Return orders belonging to one customer."""

    statement = (
        select(Order)
        .where(
            Order.customer_id == customer_id,
        )
        .options(
            selectinload(Order.items),
        )
        .order_by(
            Order.created_at.desc(),
            Order.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    return list(
        db.scalars(statement).all()
    )


def get_customer_order(
    db: Session,
    *,
    customer_id: int,
    order_id: int,
) -> Order | None:
    """Return one order only when it belongs to the customer."""

    statement = (
        select(Order)
        .where(
            Order.id == order_id,
            Order.customer_id == customer_id,
        )
        .options(
            selectinload(Order.items),
        )
    )

    return db.scalar(statement)


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
                    product_name=product.name,
                    quantity=quantity,
                    unit_price=unit_price,
                    line_total=line_total,
                )
            )

        order.total = total

        db.add(order)
        db.commit()

    except Exception:
        db.rollback()
        raise

    saved_order = get_customer_order(
        db,
        customer_id=customer_id,
        order_id=order.id,
    )

    if saved_order is None:
        raise OrderDataIntegrityError(
            "Created order could not be reloaded"
        )

    return saved_order


def cancel_order(
    db: Session,
    *,
    order_id: int,
    customer_id: int | None = None,
    allowed_statuses: frozenset[OrderStatus] = (
        CUSTOMER_CANCELLABLE_STATUSES
    ),
) -> Order:
    """Cancel an allowed order and restore stock atomically."""

    try:
        order_statement = (
            select(Order)
            .where(
                Order.id == order_id,
            )
            .with_for_update()
        )

        if customer_id is not None:
            order_statement = order_statement.where(
                Order.customer_id == customer_id,
            )

        order = db.scalar(order_statement)

        if order is None:
            raise OrderNotFoundError(
                "Order not found"
            )

        if order.status not in allowed_statuses:
            raise OrderNotCancellableError(
                order.status
            )

        item_statement = (
            select(OrderItem)
            .where(
                OrderItem.order_id == order.id,
            )
            .order_by(
                OrderItem.product_id,
            )
        )

        order_items = list(
            db.scalars(item_statement).all()
        )

        if not order_items:
            raise OrderDataIntegrityError(
                "Order contains no items"
            )

        product_ids = [
            item.product_id
            for item in order_items
        ]

        product_statement = (
            select(Product)
            .where(
                Product.id.in_(product_ids),
            )
            .order_by(
                Product.id,
            )
            .with_for_update()
        )

        products = list(
            db.scalars(product_statement).all()
        )

        if len(products) != len(product_ids):
            raise OrderDataIntegrityError(
                "One or more order products are missing"
            )

        products_by_id = {
            product.id: product
            for product in products
        }

        for item in order_items:
            product = products_by_id[item.product_id]
            product.stock += item.quantity

        order.status = OrderStatus.CANCELLED

        saved_customer_id = order.customer_id

        db.commit()

    except Exception:
        db.rollback()
        raise

    cancelled_order = get_customer_order(
        db,
        customer_id=saved_customer_id,
        order_id=order_id,
    )

    if cancelled_order is None:
        raise OrderDataIntegrityError(
            "Cancelled order could not be reloaded"
        )

    return cancelled_order