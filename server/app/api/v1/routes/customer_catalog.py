"""Authenticated customer catalog endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps.auth import CurrentCustomerUser
from app.schemas.customer_catalog import CustomerProductRead
from app.services import customer_catalog as catalog_service

router = APIRouter(
    prefix="/customer/products",
    tags=["customer catalog"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get(
    "",
    response_model=list[CustomerProductRead],
)
def read_customer_products(
    current_user: CurrentCustomerUser,
    db: DatabaseSession,
    category_id: Annotated[int | None, Query(gt=0)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[CustomerProductRead]:
    """Return products priced for the authenticated customer."""

    if current_user.customer_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account required",
        )

    try:
        priced_products = catalog_service.list_customer_products(
            db,
            customer_id=current_user.customer_id,
            category_id=category_id,
            offset=offset,
            limit=limit,
        )
    except catalog_service.MultipleCurrentContractsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Multiple current contracts found",
        ) from error

    return [
        CustomerProductRead(
            id=item.product.id,
            category_id=item.product.category_id,
            name=item.product.name,
            description=item.product.description,
            stock=item.product.stock,
            image_url=item.product.image_url,
            effective_price=item.effective_price,
            price_source=item.price_source,
            contract_id=item.contract_id,
        )
        for item in priced_products
    ]