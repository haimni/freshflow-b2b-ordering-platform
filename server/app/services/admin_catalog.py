"""Administrator catalog-management operations."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product


class CategoryNotFoundError(Exception):
    """Raised when a category cannot be found."""


class CategoryNameConflictError(Exception):
    """Raised when a category name already exists."""


class CategoryHasActiveProductsError(Exception):
    """Raised when disabling a category with active products."""


class InactiveCategoryError(Exception):
    """Raised when an active product uses an inactive category."""


class ProductNotFoundError(Exception):
    """Raised when a product cannot be found."""


def create_category(
    db: Session,
    *,
    name: str,
    description: str | None,
    active: bool,
) -> Category:
    """Create one category."""

    try:
        existing_category = db.scalar(
            select(Category).where(
                Category.name == name
            )
        )

        if existing_category is not None:
            raise CategoryNameConflictError(
                "Category name already exists"
            )

        category = Category(
            name=name,
            description=description,
            active=active,
        )

        db.add(category)
        db.commit()
        db.refresh(category)

        return category

    except IntegrityError as error:
        db.rollback()

        raise CategoryNameConflictError(
            "Category name already exists"
        ) from error

    except Exception:
        db.rollback()
        raise


def update_category(
    db: Session,
    *,
    category_id: int,
    changes: dict[str, Any],
) -> Category:
    """Update one category under a row lock."""

    try:
        category = db.scalar(
            select(Category)
            .where(
                Category.id == category_id
            )
            .with_for_update()
        )

        if category is None:
            raise CategoryNotFoundError(
                "Category not found"
            )

        new_name = changes.get("name")

        if (
            new_name is not None
            and new_name != category.name
        ):
            conflicting_category = db.scalar(
                select(Category).where(
                    Category.name == new_name,
                    Category.id != category_id,
                )
            )

            if conflicting_category is not None:
                raise CategoryNameConflictError(
                    "Category name already exists"
                )

        if changes.get("active") is False:
            active_product_id = db.scalar(
                select(Product.id)
                .where(
                    Product.category_id == category_id,
                    Product.active.is_(True),
                )
                .limit(1)
                .with_for_update()
            )

            if active_product_id is not None:
                raise CategoryHasActiveProductsError(
                    "Category has active products"
                )

        for field_name, value in changes.items():
            setattr(category, field_name, value)

        db.commit()
        db.refresh(category)

        return category

    except IntegrityError as error:
        db.rollback()

        raise CategoryNameConflictError(
            "Category name already exists"
        ) from error

    except Exception:
        db.rollback()
        raise


def create_product(
    db: Session,
    *,
    category_id: int,
    name: str,
    description: str | None,
    default_price: object,
    stock: object,
    image_url: str | None,
    active: bool,
) -> Product:
    """Create one product with its initial stock."""

    try:
        category = db.scalar(
            select(Category)
            .where(
                Category.id == category_id
            )
            .with_for_update()
        )

        if category is None:
            raise CategoryNotFoundError(
                "Category not found"
            )

        if active and not category.active:
            raise InactiveCategoryError(
                "Active product requires an active category"
            )

        product = Product(
            category_id=category_id,
            name=name,
            description=description,
            default_price=default_price,
            stock=stock,
            image_url=image_url,
            active=active,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        return product

    except Exception:
        db.rollback()
        raise


def update_product(
    db: Session,
    *,
    product_id: int,
    changes: dict[str, Any],
) -> Product:
    """Update product metadata without changing stock."""

    try:
        product = db.scalar(
            select(Product)
            .where(
                Product.id == product_id
            )
            .with_for_update()
        )

        if product is None:
            raise ProductNotFoundError(
                "Product not found"
            )

        effective_category_id = int(
            changes.get(
                "category_id",
                product.category_id,
            )
        )

        effective_active = bool(
            changes.get(
                "active",
                product.active,
            )
        )

        category = db.scalar(
            select(Category)
            .where(
                Category.id == effective_category_id
            )
            .with_for_update()
        )

        if category is None:
            raise CategoryNotFoundError(
                "Category not found"
            )

        if effective_active and not category.active:
            raise InactiveCategoryError(
                "Active product requires an active category"
            )

        for field_name, value in changes.items():
            setattr(product, field_name, value)

        db.commit()
        db.refresh(product)

        return product

    except Exception:
        db.rollback()
        raise