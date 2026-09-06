"""Transactional manual inventory-adjustment operations."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import (
    Session,
    selectinload,
)

from app.models.inventory_adjustment import (
    InventoryAdjustment,
)
from app.models.product import Product

MAX_STOCK = Decimal("999999999.999")


class InventoryProductNotFoundError(Exception):
    """Raised when the adjusted product cannot be found."""


class InventoryBelowZeroError(Exception):
    """Raised when an adjustment would create negative stock."""


class InventoryTooLargeError(Exception):
    """Raised when stock would exceed database precision."""


class InventoryAdjustmentDataIntegrityError(Exception):
    """Raised when a saved adjustment cannot be reloaded."""


def get_inventory_adjustment(
    db: Session,
    *,
    adjustment_id: int,
) -> InventoryAdjustment | None:
    """Return one adjustment with display relationships."""

    statement = (
        select(InventoryAdjustment)
        .where(
            InventoryAdjustment.id == adjustment_id,
        )
        .options(
            selectinload(
                InventoryAdjustment.product,
            ),
            selectinload(
                InventoryAdjustment.performed_by_user,
            ),
        )
    )

    return db.scalar(statement)


def list_inventory_adjustments(
    db: Session,
    *,
    product_id: int | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[InventoryAdjustment]:
    """Return manual inventory adjustments newest first."""

    statement = (
        select(InventoryAdjustment)
        .options(
            selectinload(
                InventoryAdjustment.product,
            ),
            selectinload(
                InventoryAdjustment.performed_by_user,
            ),
        )
        .order_by(
            InventoryAdjustment.created_at.desc(),
            InventoryAdjustment.id.desc(),
        )
    )

    if product_id is not None:
        statement = statement.where(
            InventoryAdjustment.product_id == product_id,
        )

    statement = statement.offset(offset).limit(limit)

    return list(
        db.scalars(statement).all()
    )


def adjust_inventory(
    db: Session,
    *,
    product_id: int,
    performed_by_user_id: int,
    quantity_change: Decimal,
    reason: str,
) -> InventoryAdjustment:
    """Change product stock and record the adjustment atomically."""

    try:
        product = db.scalar(
            select(Product)
            .where(
                Product.id == product_id,
            )
            .with_for_update()
        )

        if product is None:
            raise InventoryProductNotFoundError(
                "Product not found"
            )

        stock_before = Decimal(product.stock)
        stock_after = stock_before + quantity_change

        if stock_after < 0:
            raise InventoryBelowZeroError(
                "Adjustment would create negative stock"
            )

        if stock_after > MAX_STOCK:
            raise InventoryTooLargeError(
                "Adjustment exceeds maximum stock"
            )

        adjustment = InventoryAdjustment(
            product_id=product.id,
            performed_by_user_id=performed_by_user_id,
            quantity_change=quantity_change,
            stock_before=stock_before,
            stock_after=stock_after,
            reason=reason,
        )

        product.stock = stock_after

        db.add(adjustment)
        db.commit()

        adjustment_id = adjustment.id

    except Exception:
        db.rollback()
        raise

    saved_adjustment = get_inventory_adjustment(
        db,
        adjustment_id=adjustment_id,
    )

    if saved_adjustment is None:
        raise InventoryAdjustmentDataIntegrityError(
            "Saved adjustment could not be reloaded"
        )

    return saved_adjustment