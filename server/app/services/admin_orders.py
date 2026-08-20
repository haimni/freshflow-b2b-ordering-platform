"""Administrator order-management operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import OrderStatus
from app.models.order import Order
from app.services import orders as order_service

ADMIN_STATUS_TRANSITIONS = {
    OrderStatus.PENDING: OrderStatus.CONFIRMED,
    OrderStatus.CONFIRMED: OrderStatus.PROCESSING,
    OrderStatus.PROCESSING: OrderStatus.COMPLETED,
}


class AdminOrderNotFoundError(Exception):
    """Raised when an administrator order cannot be found."""


class InvalidOrderTransitionError(Exception):
    """Raised when an order status transition is invalid."""

    def __init__(
        self,
        current_status: OrderStatus,
        requested_status: OrderStatus,
    ) -> None:
        self.current_status = current_status
        self.requested_status = requested_status

        super().__init__(
            "Invalid order transition from "
            f"{current_status.value} to "
            f"{requested_status.value}"
        )


class AdminOrderDataIntegrityError(Exception):
    """Raised when an updated order cannot be reloaded."""


def list_orders(
    db: Session,
    *,
    customer_id: int | None = None,
    order_status: OrderStatus | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[Order]:
    """Return orders visible to an administrator."""

    statement = (
        select(Order)
        .options(
            selectinload(Order.items),
        )
        .order_by(
            Order.created_at.desc(),
            Order.id.desc(),
        )
    )

    if customer_id is not None:
        statement = statement.where(
            Order.customer_id == customer_id,
        )

    if order_status is not None:
        statement = statement.where(
            Order.status == order_status,
        )

    statement = (
        statement
        .offset(offset)
        .limit(limit)
    )

    return list(
        db.scalars(statement).all()
    )


def get_order(
    db: Session,
    *,
    order_id: int,
) -> Order | None:
    """Return one order for administrator inspection."""

    statement = (
        select(Order)
        .where(
            Order.id == order_id,
        )
        .options(
            selectinload(Order.items),
        )
    )

    return db.scalar(statement)


def update_order_status(
    db: Session,
    *,
    order_id: int,
    requested_status: OrderStatus,
) -> Order:
    """Apply one valid administrator status transition."""

    if requested_status == OrderStatus.CANCELLED:
        return order_service.cancel_order(
            db,
            order_id=order_id,
            allowed_statuses=(
                order_service
                .ADMIN_CANCELLABLE_STATUSES
            ),
        )

    try:
        statement = (
            select(Order)
            .where(
                Order.id == order_id,
            )
            .with_for_update()
        )

        order = db.scalar(statement)

        if order is None:
            raise AdminOrderNotFoundError(
                "Order not found"
            )

        allowed_next_status = (
            ADMIN_STATUS_TRANSITIONS.get(
                order.status
            )
        )

        if requested_status != allowed_next_status:
            raise InvalidOrderTransitionError(
                order.status,
                requested_status,
            )

        order.status = requested_status

        db.commit()

    except Exception:
        db.rollback()
        raise

    updated_order = get_order(
        db,
        order_id=order_id,
    )

    if updated_order is None:
        raise AdminOrderDataIntegrityError(
            "Updated order could not be reloaded"
        )

    return updated_order