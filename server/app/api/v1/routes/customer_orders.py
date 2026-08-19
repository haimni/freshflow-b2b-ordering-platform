"""Authenticated customer order endpoints."""

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
from app.deps.auth import CurrentCustomerUser
from app.schemas.order import OrderCreate, OrderRead
from app.services import orders as order_service
from app.services.customer_catalog import (
    MultipleCurrentContractsError,
)

router = APIRouter(
    prefix="/customer/orders",
    tags=["customer orders"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]

OrderId = Annotated[
    int,
    Path(gt=0),
]

Offset = Annotated[
    int,
    Query(ge=0),
]

Limit = Annotated[
    int,
    Query(ge=1, le=100),
]


def require_customer_id(
    current_user: CurrentCustomerUser,
) -> int:
    """Return the authenticated customer's identifier."""

    if current_user.customer_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account required",
        )

    return current_user.customer_id


@router.get(
    "",
    response_model=list[OrderRead],
)
def read_customer_orders(
    current_user: CurrentCustomerUser,
    db: DatabaseSession,
    offset: Offset = 0,
    limit: Limit = 20,
) -> list[OrderRead]:
    """Return orders belonging to the authenticated customer."""

    customer_id = require_customer_id(
        current_user
    )

    return order_service.get_customer_orders(
        db,
        customer_id=customer_id,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{order_id}",
    response_model=OrderRead,
)
def read_customer_order(
    order_id: OrderId,
    current_user: CurrentCustomerUser,
    db: DatabaseSession,
) -> OrderRead:
    """Return one order belonging to the authenticated customer."""

    customer_id = require_customer_id(
        current_user
    )

    order = order_service.get_customer_order(
        db,
        customer_id=customer_id,
        order_id=order_id,
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return order


@router.post(
    "",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_order(
    order_request: OrderCreate,
    current_user: CurrentCustomerUser,
    db: DatabaseSession,
) -> OrderRead:
    """Create a pending order for the authenticated customer."""

    customer_id = require_customer_id(
        current_user
    )

    try:
        return order_service.create_order(
            db,
            customer_id=customer_id,
            created_by_user_id=current_user.id,
            requested_items=[
                (
                    item.product_id,
                    item.quantity,
                )
                for item in order_request.items
            ],
        )

    except order_service.ContractRequiredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A current contract is required",
        ) from error

    except MultipleCurrentContractsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Multiple current contracts found",
        ) from error

    except order_service.ProductUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more products are unavailable",
        ) from error

    except order_service.InsufficientStockError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Insufficient stock for product "
                f"{error.product_id}"
            ),
        ) from error

    except order_service.OrderAmountTooLargeError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Order amount is too large",
        ) from error


@router.post(
    "/{order_id}/cancel",
    response_model=OrderRead,
)
def cancel_customer_order(
    order_id: OrderId,
    current_user: CurrentCustomerUser,
    db: DatabaseSession,
) -> OrderRead:
    """Cancel a pending customer order and restore stock."""

    customer_id = require_customer_id(
        current_user
    )

    try:
        return order_service.cancel_order(
            db,
            customer_id=customer_id,
            order_id=order_id,
        )

    except order_service.OrderNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        ) from error

    except order_service.OrderNotCancellableError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Only pending orders can be cancelled; "
                f"current status is {error.current_status.value}"
            ),
        ) from error

    except order_service.OrderDataIntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored order data is inconsistent",
        ) from error