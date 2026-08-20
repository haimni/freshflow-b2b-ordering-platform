"""MySQL integration tests for administrator catalog management."""

from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product
from app.services import admin_catalog


def get_category(
    db: Session,
    category_id: int,
) -> Category:
    """Reload one category directly from MySQL."""

    db.expire_all()

    category = db.get(
        Category,
        category_id,
    )

    assert category is not None

    return category


def get_product(
    db: Session,
    product_id: int,
) -> Product:
    """Reload one product directly from MySQL."""

    db.expire_all()

    product = db.get(
        Product,
        product_id,
    )

    assert product is not None

    return product


def count_categories_named(
    db: Session,
    name: str,
) -> int:
    """Count categories with one name."""

    return db.scalar(
        select(func.count())
        .select_from(Category)
        .where(Category.name == name)
    ) or 0


def test_admin_can_create_category_and_product(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """Administrator creates a category and product."""

    category = admin_catalog.create_category(
        db_session,
        name="Integration Test Fruit",
        description="Fruit created by integration test",
        active=True,
    )

    product = admin_catalog.create_product(
        db_session,
        category_id=category.id,
        name="Integration Test Apple",
        description="Apple created by integration test",
        default_price=Decimal("6.50"),
        stock=Decimal("40.000"),
        image_url=None,
        active=True,
    )

    assert category.id is not None
    assert category.active is True

    assert product.id is not None
    assert product.category_id == category.id
    assert product.default_price == Decimal("6.50")
    assert product.stock == Decimal("40.000")
    assert product.active is True


def test_duplicate_category_name_is_rejected(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """A duplicate category name is rejected safely."""

    category_id = int(
        order_scenario["category_id"]
    )

    existing_category = get_category(
        db_session,
        category_id,
    )

    with pytest.raises(
        admin_catalog.CategoryNameConflictError
    ):
        admin_catalog.create_category(
            db_session,
            name=existing_category.name,
            description="Duplicate category",
            active=True,
        )

    assert count_categories_named(
        db_session,
        existing_category.name,
    ) == 1

    assert get_category(
        db_session,
        category_id,
    ).active is True


def test_category_with_active_product_cannot_be_disabled(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """An active product blocks category deactivation."""

    category_id = int(
        order_scenario["category_id"]
    )

    with pytest.raises(
        admin_catalog.CategoryHasActiveProductsError
    ):
        admin_catalog.update_category(
            db_session,
            category_id=category_id,
            changes={
                "active": False,
            },
        )

    assert get_category(
        db_session,
        category_id,
    ).active is True

    assert get_product(
        db_session,
        int(order_scenario["product_id"]),
    ).active is True


def test_category_can_be_disabled_after_products(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """Products are disabled before their category."""

    product_id = int(
        order_scenario["product_id"]
    )

    category_id = int(
        order_scenario["category_id"]
    )

    product = admin_catalog.update_product(
        db_session,
        product_id=product_id,
        changes={
            "active": False,
        },
    )

    assert product.active is False

    category = admin_catalog.update_category(
        db_session,
        category_id=category_id,
        changes={
            "active": False,
        },
    )

    assert category.active is False

    assert get_product(
        db_session,
        product_id,
    ).active is False

    assert get_category(
        db_session,
        category_id,
    ).active is False


def test_active_product_cannot_use_inactive_category(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """An active product cannot be created in an inactive category."""

    category = admin_catalog.create_category(
        db_session,
        name="Integration Test Inactive Category",
        description=None,
        active=False,
    )

    with pytest.raises(
        admin_catalog.InactiveCategoryError
    ):
        admin_catalog.create_product(
            db_session,
            category_id=category.id,
            name="Invalid Active Product",
            description=None,
            default_price=Decimal("5.00"),
            stock=Decimal("3.000"),
            image_url=None,
            active=True,
        )

    product_count = db_session.scalar(
        select(func.count())
        .select_from(Product)
        .where(
            Product.name == "Invalid Active Product"
        )
    )

    assert product_count == 0

    # An inactive product may be retained in an inactive category.
    inactive_product = admin_catalog.create_product(
        db_session,
        category_id=category.id,
        name="Inactive Archived Product",
        description=None,
        default_price=Decimal("5.00"),
        stock=Decimal("3.000"),
        image_url=None,
        active=False,
    )

    assert inactive_product.active is False
    assert inactive_product.category_id == category.id


def test_product_metadata_update_preserves_stock(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """Metadata updates do not alter product stock."""

    product_id = int(
        order_scenario["product_id"]
    )

    original_product = get_product(
        db_session,
        product_id,
    )

    original_stock = original_product.stock

    updated_product = admin_catalog.update_product(
        db_session,
        product_id=product_id,
        changes={
            "name": "Updated Integration Tomatoes",
            "default_price": Decimal("10.25"),
            "description": "Updated description",
        },
    )

    assert (
        updated_product.name
        == "Updated Integration Tomatoes"
    )

    assert (
        updated_product.default_price
        == Decimal("10.25")
    )

    assert updated_product.stock == original_stock

    stored_product = get_product(
        db_session,
        product_id,
    )

    assert stored_product.stock == Decimal("10.000")


def test_active_product_cannot_move_to_inactive_category(
    db_session: Session,
    order_scenario: dict[str, object],
) -> None:
    """Moving an active product to an inactive category fails."""

    product_id = int(
        order_scenario["product_id"]
    )

    original_category_id = int(
        order_scenario["category_id"]
    )

    inactive_category = (
        admin_catalog.create_category(
            db_session,
            name="Integration Test Disabled Destination",
            description=None,
            active=False,
        )
    )

    with pytest.raises(
        admin_catalog.InactiveCategoryError
    ):
        admin_catalog.update_product(
            db_session,
            product_id=product_id,
            changes={
                "category_id": inactive_category.id,
            },
        )

    stored_product = get_product(
        db_session,
        product_id,
    )

    assert (
        stored_product.category_id
        == original_category_id
    )

    assert stored_product.active is True