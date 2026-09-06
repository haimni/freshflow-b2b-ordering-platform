"""Administrator-only inventory adjustment endpoints."""

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
from app.schemas.inventory_adjustment import (
    InventoryAdjustmentCreate,
    InventoryAdjustmentRead,
)
from app.services import inventory as inventory_service

router = APIRouter(
    prefix="/admin",
    tags=["administration"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]

ProductId = Annotated[
    int,
    Path(gt=0),
]

ProductIdFilter = Annotated[
    int | None,
    Query(gt=0),
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
    "/inventory-adjustments",
    response_model=list[InventoryAdjustmentRead],
)
def read_inventory_adjustments(
    current_admin: CurrentAdmin,
    db: DatabaseSession,
    product_id: ProductIdFilter = None,
    offset: Offset = 0,
    limit: Limit = 100,
) -> list[InventoryAdjustmentRead]:
    """Return manual inventory adjustment history."""

    return inventory_service.list_inventory_adjustments(
        db,
        product_id=product_id,
        offset=offset,
        limit=limit,
    )


@router.post(
    "/products/{product_id}/inventory-adjustments",
    response_model=InventoryAdjustmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory_adjustment(
    product_id: ProductId,
    adjustment_request: InventoryAdjustmentCreate,
    current_admin: CurrentAdmin,
    db: DatabaseSession,
) -> InventoryAdjustmentRead:
    """Adjust product stock and create an audit record."""

    try:
        return inventory_service.adjust_inventory(
            db,
            product_id=product_id,
            performed_by_user_id=current_admin.id,
            quantity_change=(
                adjustment_request.quantity_change
            ),
            reason=adjustment_request.reason,
        )

    except (
        inventory_service.InventoryProductNotFoundError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        ) from error

    except (
        inventory_service.InventoryBelowZeroError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Inventory adjustment would create "
                "negative stock"
            ),
        ) from error

    except (
        inventory_service.InventoryTooLargeError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Inventory amount is too large",
        ) from error

    except (
        inventory_service
        .InventoryAdjustmentDataIntegrityError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Saved inventory adjustment "
                "could not be loaded"
            ),
        ) from error