"""Administrator-only order endpoints."""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps.auth import CurrentAdmin
from app.models.enums import OrderStatus
from app.schemas.admin_order import (
    AdminOrderStatusUpdate,
)
from app.schemas.order import OrderRead
from app.services import admin_orders as order_service
from app.services import orders as customer_order_service

router = APIRouter(
    prefix="/admin/orders",
    tags=["administration"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]

OrderId = Annotated[
    int,
    Path(gt=0),
]

CustomerIdFilter = Annotated[
    int | None,
    Query(gt=0),
]

StatusFilter = Annotated[
    OrderStatus | None,
    Query(alias="status"),
]

Offset = Annotated[
    int,
    Query(ge=0),
]

Limit = Annotated[
    int,
    Query(ge=1, le=100),
]


@router.get(
    "",
    response_model=list[OrderRead],
)
def read_orders(
    current_admin: CurrentAdmin,
    db: DatabaseSession,
    customer_id: CustomerIdFilter = None,
    order_status: StatusFilter = None,
    offset: Offset = 0,
    limit: Limit = 100,
) -> list[OrderRead]:
    """Return orders to an authenticated administrator."""

    return order_service.list_orders(
        db,
        customer_id=customer_id,
        order_status=order_status,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{order_id}",
    response_model=OrderRead,
)
def read_order(
    order_id: OrderId,
    current_admin: CurrentAdmin,
    db: DatabaseSession,
) -> OrderRead:
    """Return one order to an administrator."""

    order = order_service.get_order(
        db,
        order_id=order_id,
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return order


@router.patch(
    "/{order_id}/status",
    response_model=OrderRead,
)
def update_order_status(
    order_id: OrderId,
    status_request: AdminOrderStatusUpdate,
    current_admin: CurrentAdmin,
    db: DatabaseSession,
) -> OrderRead:
    """Advance or cancel an order."""

    try:
        return order_service.update_order_status(
            db,
            order_id=order_id,
            requested_status=status_request.status,
        )

    except (
        order_service.AdminOrderNotFoundError,
        customer_order_service.OrderNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        ) from error

    except (
        order_service.InvalidOrderTransitionError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Invalid order transition from "
                f"{error.current_status.value} to "
                f"{error.requested_status.value}"
            ),
        ) from error

    except (
        customer_order_service
        .OrderNotCancellableError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Order cannot be cancelled from "
                f"status {error.current_status.value}"
            ),
        ) from error

    except (
        customer_order_service
        .OrderDataIntegrityError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Stored order data is inconsistent",
        ) from error

    except (
        order_service.AdminOrderDataIntegrityError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Updated order could not be loaded",
        ) from error