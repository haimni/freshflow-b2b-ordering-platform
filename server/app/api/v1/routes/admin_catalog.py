"""Administrator-only catalog endpoints."""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps.auth import CurrentAdmin
from app.schemas.category import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
)
from app.schemas.product import (
    ProductCreate,
    ProductRead,
    ProductUpdate,
)
from app.services import admin_catalog as catalog_service

router = APIRouter(
    prefix="/admin",
    tags=["administration"],
)

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]

CategoryId = Annotated[
    int,
    Path(gt=0),
]

ProductId = Annotated[
    int,
    Path(gt=0),
]


@router.post(
    "/categories",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    category_request: CategoryCreate,
    current_admin: CurrentAdmin,
    db: DatabaseSession,
) -> CategoryRead:
    """Create a product category."""

    try:
        return catalog_service.create_category(
            db,
            name=category_request.name,
            description=category_request.description,
            active=category_request.active,
        )

    except (
        catalog_service.CategoryNameConflictError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category name already exists",
        ) from error


@router.patch(
    "/categories/{category_id}",
    response_model=CategoryRead,
)
def update_category(
    category_id: CategoryId,
    category_request: CategoryUpdate,
    current_admin: CurrentAdmin,
    db: DatabaseSession,
) -> CategoryRead:
    """Update category metadata or active state."""

    try:
        return catalog_service.update_category(
            db,
            category_id=category_id,
            changes=category_request.model_dump(
                exclude_unset=True
            ),
        )

    except (
        catalog_service.CategoryNotFoundError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        ) from error

    except (
        catalog_service.CategoryNameConflictError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category name already exists",
        ) from error

    except (
        catalog_service.CategoryHasActiveProductsError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category has active products",
        ) from error


@router.post(
    "/products",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product_request: ProductCreate,
    current_admin: CurrentAdmin,
    db: DatabaseSession,
) -> ProductRead:
    """Create a product with initial stock."""

    try:
        return catalog_service.create_product(
            db,
            category_id=product_request.category_id,
            name=product_request.name,
            description=product_request.description,
            default_price=product_request.default_price,
            stock=product_request.stock,
            image_url=product_request.image_url,
            active=product_request.active,
        )

    except (
        catalog_service.CategoryNotFoundError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        ) from error

    except (
        catalog_service.InactiveCategoryError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "An active product requires "
                "an active category"
            ),
        ) from error


@router.patch(
    "/products/{product_id}",
    response_model=ProductRead,
)
def update_product(
    product_id: ProductId,
    product_request: ProductUpdate,
    current_admin: CurrentAdmin,
    db: DatabaseSession,
) -> ProductRead:
    """Update product metadata without changing stock."""

    try:
        return catalog_service.update_product(
            db,
            product_id=product_id,
            changes=product_request.model_dump(
                exclude_unset=True
            ),
        )

    except (
        catalog_service.ProductNotFoundError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        ) from error

    except (
        catalog_service.CategoryNotFoundError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        ) from error

    except (
        catalog_service.InactiveCategoryError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "An active product requires "
                "an active category"
            ),
        ) from error