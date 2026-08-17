"""Database operations for the product catalog."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product


def list_active_categories(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 100,
) -> list[Category]:
    """Return active categories ordered by name."""

    statement = (
        select(Category)
        .where(Category.active.is_(True))
        .order_by(Category.name)
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def list_active_products(
    db: Session,
    *,
    category_id: int | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[Product]:
    """Return active products, optionally filtered by category."""

    statement = (
        select(Product)
        .where(Product.active.is_(True))
        .order_by(Product.name)
    )

    if category_id is not None:
        statement = statement.where(
            Product.category_id == category_id
        )

    statement = statement.offset(offset).limit(limit)

    return list(db.scalars(statement).all())


def get_active_product(
    db: Session,
    product_id: int,
) -> Product | None:
    """Return one active product, or None when it cannot be found."""

    statement = select(Product).where(
        Product.id == product_id,
        Product.active.is_(True),
    )

    return db.scalar(statement)