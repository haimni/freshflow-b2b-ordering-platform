"""Authenticated customer order endpoints."""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
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

    if current_user.customer_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account required",
        )

    try:
        return order_service.create_order(
            db,
            customer_id=current_user.customer_id,
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