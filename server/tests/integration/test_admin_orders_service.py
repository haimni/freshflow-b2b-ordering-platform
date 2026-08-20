"""MySQL integration tests for administrator order management."""

from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import OrderStatus
from app.models.order import Order
from app.models.product import Product
from app.services import admin_orders
from app.services import orders as order_service


def create_pending_order(
    db: Session,
    scenario: dict[str, object],
    *,
    quantity: Decimal = Decimal("2.000"),
) -> Order:
    """Create one real pending order in MySQL."""

    return order_service.create_order(
        db,
        customer_id=int(
            scenario["customer_id"]
        ),
        created_by_user_id=int(
            scenario["user_id"]
        ),
        requested_items=[
            (
                int(scenario["product_id"]),
                quantity,
            )
        ],
    )


def get_order_status(
    db: Session,
    order_id: int,
) -> OrderStatus:
    """Read the current order status directly from MySQL."""

    db.expire_all()

    order_status = db.scalar(
        select(Order.status).where(
            Order.id == order_id
        )
    )

    assert order_status is not None

    return order_status


def get_product_stock(
    db: Session,
    product_id: int,
) -> Decimal:
    """Read the current product stock directly from MySQL."""

    db.expire_all()

    stock = db.scalar(
        select(Product.stock).where(
            Product.id == product_id
        )
    )

    assert stock is not None

    return stock


def test_admin_can_complete_full_order_workflow(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """An administrator advances one workflow state at a time."""

    order = create_pending_order(
        db_session,
        order_scenario,
    )

    confirmed_order = (
        admin_orders.update_order_status(
            db_session,
            order_id=order.id,
            requested_status=OrderStatus.CONFIRMED,
        )
    )

    assert (
        confirmed_order.status
        == OrderStatus.CONFIRMED
    )

    processing_order = (
        admin_orders.update_order_status(
            db_session,
            order_id=order.id,
            requested_status=OrderStatus.PROCESSING,
        )
    )

    assert (
        processing_order.status
        == OrderStatus.PROCESSING
    )

    completed_order = (
        admin_orders.update_order_status(
            db_session,
            order_id=order.id,
            requested_status=OrderStatus.COMPLETED,
        )
    )

    assert (
        completed_order.status
        == OrderStatus.COMPLETED
    )

    assert get_order_status(
        db_session,
        order.id,
    ) == OrderStatus.COMPLETED

    # Status progression must not alter reserved stock.
    assert get_product_stock(
        db_session,
        int(order_scenario["product_id"]),
    ) == Decimal("8.000")


def test_admin_cannot_skip_workflow_state(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """A pending order cannot jump directly to processing."""

    order = create_pending_order(
        db_session,
        order_scenario,
    )

    with pytest.raises(
        admin_orders.InvalidOrderTransitionError
    ) as captured_error:
        admin_orders.update_order_status(
            db_session,
            order_id=order.id,
            requested_status=OrderStatus.PROCESSING,
        )

    assert (
        captured_error.value.current_status
        == OrderStatus.PENDING
    )

    assert (
        captured_error.value.requested_status
        == OrderStatus.PROCESSING
    )

    assert get_order_status(
        db_session,
        order.id,
    ) == OrderStatus.PENDING

    assert get_product_stock(
        db_session,
        int(order_scenario["product_id"]),
    ) == Decimal("8.000")


def test_admin_cannot_move_order_backwards(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """A confirmed order cannot return to pending."""

    order = create_pending_order(
        db_session,
        order_scenario,
    )

    admin_orders.update_order_status(
        db_session,
        order_id=order.id,
        requested_status=OrderStatus.CONFIRMED,
    )

    with pytest.raises(
        admin_orders.InvalidOrderTransitionError
    ):
        admin_orders.update_order_status(
            db_session,
            order_id=order.id,
            requested_status=OrderStatus.PENDING,
        )

    assert get_order_status(
        db_session,
        order.id,
    ) == OrderStatus.CONFIRMED

    assert get_product_stock(
        db_session,
        int(order_scenario["product_id"]),
    ) == Decimal("8.000")


def test_admin_can_cancel_confirmed_order(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """Cancelling a confirmed order restores stock."""

    order = create_pending_order(
        db_session,
        order_scenario,
        quantity=Decimal("3.000"),
    )

    assert get_product_stock(
        db_session,
        int(order_scenario["product_id"]),
    ) == Decimal("7.000")

    admin_orders.update_order_status(
        db_session,
        order_id=order.id,
        requested_status=OrderStatus.CONFIRMED,
    )

    cancelled_order = (
        admin_orders.update_order_status(
            db_session,
            order_id=order.id,
            requested_status=OrderStatus.CANCELLED,
        )
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
        admin_orders.update_order_status(
            db_session,
            order_id=order.id,
            requested_status=OrderStatus.CANCELLED,
        )

    # A second cancellation must not restore stock again.
    assert get_product_stock(
        db_session,
        int(order_scenario["product_id"]),
    ) == Decimal("10.000")


def test_admin_cannot_cancel_processing_order(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """A processing order cannot be cancelled."""

    order = create_pending_order(
        db_session,
        order_scenario,
    )

    admin_orders.update_order_status(
        db_session,
        order_id=order.id,
        requested_status=OrderStatus.CONFIRMED,
    )

    admin_orders.update_order_status(
        db_session,
        order_id=order.id,
        requested_status=OrderStatus.PROCESSING,
    )

    with pytest.raises(
        order_service.OrderNotCancellableError
    ) as captured_error:
        admin_orders.update_order_status(
            db_session,
            order_id=order.id,
            requested_status=OrderStatus.CANCELLED,
        )

    assert (
        captured_error.value.current_status
        == OrderStatus.PROCESSING
    )

    assert get_order_status(
        db_session,
        order.id,
    ) == OrderStatus.PROCESSING

    # Stock stays reserved for the processing order.
    assert get_product_stock(
        db_session,
        int(order_scenario["product_id"]),
    ) == Decimal("8.000")


def test_admin_can_filter_orders(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """Administrator filters return matching orders."""

    order = create_pending_order(
        db_session,
        order_scenario,
    )

    admin_orders.update_order_status(
        db_session,
        order_id=order.id,
        requested_status=OrderStatus.CONFIRMED,
    )

    matching_orders = admin_orders.list_orders(
        db_session,
        customer_id=int(
            order_scenario["customer_id"]
        ),
        order_status=OrderStatus.CONFIRMED,
        offset=0,
        limit=100,
    )

    assert len(matching_orders) == 1
    assert matching_orders[0].id == order.id

    nonmatching_orders = admin_orders.list_orders(
        db_session,
        customer_id=int(
            order_scenario["customer_id"]
        ),
        order_status=OrderStatus.PENDING,
        offset=0,
        limit=100,
    )

    assert nonmatching_orders == []