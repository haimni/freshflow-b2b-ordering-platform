"""MySQL integration tests for transactional order operations."""

from decimal import Decimal

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.models.contract_price import ContractPrice
from app.models.enums import OrderStatus
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.services import orders as order_service


def get_product_stock(
    db: Session,
    product_id: int,
) -> Decimal:
    """Read current product stock directly from MySQL."""

    db.expire_all()

    stock = db.scalar(
        select(Product.stock).where(
            Product.id == product_id
        )
    )

    assert stock is not None

    return stock


def count_orders(db: Session) -> int:
    """Return the number of stored orders."""

    return db.scalar(
        select(func.count()).select_from(Order)
    ) or 0


def count_order_items(db: Session) -> int:
    """Return the number of stored order items."""

    return db.scalar(
        select(func.count()).select_from(OrderItem)
    ) or 0


def test_create_order_uses_contract_price_and_reduces_stock(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """Creating an order stores snapshots and reserves stock."""

    order = order_service.create_order(
        db_session,
        customer_id=int(
            order_scenario["customer_id"]
        ),
        created_by_user_id=int(
            order_scenario["user_id"]
        ),
        requested_items=[
            (
                int(order_scenario["product_id"]),
                Decimal("2.000"),
            )
        ],
    )

    assert order.status == OrderStatus.PENDING
    assert order.contract_id == int(
        order_scenario["contract_id"]
    )
    assert order.total == Decimal("15.00")

    assert len(order.items) == 1

    item = order.items[0]

    assert item.product_id == int(
        order_scenario["product_id"]
    )
    assert item.quantity == Decimal("2.000")
    assert item.unit_price == Decimal("7.50")
    assert item.line_total == Decimal("15.00")

    assert get_product_stock(
        db_session,
        int(order_scenario["product_id"]),
    ) == Decimal("8.000")

    assert count_orders(db_session) == 1
    assert count_order_items(db_session) == 1


def test_cancel_order_restores_stock_only_once(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """Cancellation restores stock and cannot run twice."""

    order = order_service.create_order(
        db_session,
        customer_id=int(
            order_scenario["customer_id"]
        ),
        created_by_user_id=int(
            order_scenario["user_id"]
        ),
        requested_items=[
            (
                int(order_scenario["product_id"]),
                Decimal("3.000"),
            )
        ],
    )

    assert get_product_stock(
        db_session,
        int(order_scenario["product_id"]),
    ) == Decimal("7.000")

    cancelled_order = order_service.cancel_order(
        db_session,
        customer_id=int(
            order_scenario["customer_id"]
        ),
        order_id=order.id,
    )

    assert (
        cancelled_order.status
        == OrderStatus.CANCELLED
    )

    assert get_product_stock(
        db_session,
        int(order_scenario["product_id"]),
    ) == Decimal("10.000")

    with pytest.raises(
        order_service.OrderNotCancellableError
    ):
        order_service.cancel_order(
            db_session,
            customer_id=int(
                order_scenario["customer_id"]
            ),
            order_id=order.id,
        )

    assert get_product_stock(
        db_session,
        int(order_scenario["product_id"]),
    ) == Decimal("10.000")


def test_insufficient_stock_rolls_back_entire_order(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """Insufficient stock leaves stock and orders unchanged."""

    with pytest.raises(
        order_service.InsufficientStockError
    ):
        order_service.create_order(
            db_session,
            customer_id=int(
                order_scenario["customer_id"]
            ),
            created_by_user_id=int(
                order_scenario["user_id"]
            ),
            requested_items=[
                (
                    int(order_scenario["product_id"]),
                    Decimal("11.000"),
                )
            ],
        )

    assert get_product_stock(
        db_session,
        int(order_scenario["product_id"]),
    ) == Decimal("10.000")

    assert count_orders(db_session) == 0
    assert count_order_items(db_session) == 0


def test_customer_without_current_contract_cannot_order(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """An inactive contract prevents order creation."""

    contract = db_session.get(
        Contract,
        int(order_scenario["contract_id"]),
    )

    assert contract is not None

    contract.active = False
    db_session.commit()

    with pytest.raises(
        order_service.ContractRequiredError
    ):
        order_service.create_order(
            db_session,
            customer_id=int(
                order_scenario["customer_id"]
            ),
            created_by_user_id=int(
                order_scenario["user_id"]
            ),
            requested_items=[
                (
                    int(order_scenario["product_id"]),
                    Decimal("1.000"),
                )
            ],
        )

    assert get_product_stock(
        db_session,
        int(order_scenario["product_id"]),
    ) == Decimal("10.000")

    assert count_orders(db_session) == 0


def test_missing_contract_price_uses_default_price(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """A missing override falls back to product default price."""

    db_session.execute(
        delete(ContractPrice).where(
            ContractPrice.id
            == int(
                order_scenario[
                    "contract_price_id"
                ]
            )
        )
    )

    db_session.commit()

    order = order_service.create_order(
        db_session,
        customer_id=int(
            order_scenario["customer_id"]
        ),
        created_by_user_id=int(
            order_scenario["user_id"]
        ),
        requested_items=[
            (
                int(order_scenario["product_id"]),
                Decimal("2.000"),
            )
        ],
    )

    assert order.total == Decimal("18.00")
    assert len(order.items) == 1
    assert (
        order.items[0].unit_price
        == Decimal("9.00")
    )
    assert (
        order.items[0].line_total
        == Decimal("18.00")
    )

    assert get_product_stock(
        db_session,
        int(order_scenario["product_id"]),
    ) == Decimal("8.000")