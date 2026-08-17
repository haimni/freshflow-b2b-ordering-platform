"""Read-only endpoints for categories and products."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.category import CategoryRead
from app.schemas.product import ProductRead
from app.services import catalog as catalog_service

router = APIRouter(tags=["catalog"])

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/categories",
    response_model=list[CategoryRead],
)
def read_categories(
    db: DatabaseSession,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[CategoryRead]:
    """Return active product categories."""

    return catalog_service.list_active_categories(
        db,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/products",
    response_model=list[ProductRead],
)
def read_products(
    db: DatabaseSession,
    category_id: Annotated[int | None, Query(gt=0)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[ProductRead]:
    """Return active products with an optional category filter."""

    return catalog_service.list_active_products(
        db,
        category_id=category_id,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/products/{product_id}",
    response_model=ProductRead,
)
def read_product(
    product_id: int,
    db: DatabaseSession,
) -> ProductRead:
    """Return one active product."""

    product = catalog_service.get_active_product(db, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product