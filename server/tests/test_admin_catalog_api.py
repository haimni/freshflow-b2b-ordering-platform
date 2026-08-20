"""API tests for administrator catalog management."""

from collections.abc import Generator
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.v1.routes import admin_catalog
from app.db.session import get_db
from app.deps.auth import get_current_user
from app.main import app
from app.models.category import Category
from app.models.enums import UserRole
from app.models.product import Product
from app.models.user import User


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create an isolated API test client."""

    def override_get_db() -> Generator[object, None, None]:
        yield object()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def create_user(
    *,
    user_id: int,
    role: UserRole,
    customer_id: int | None,
) -> User:
    """Create an in-memory authenticated user."""

    return User(
        id=user_id,
        customer_id=customer_id,
        name=f"Test User {user_id}",
        email=f"user{user_id}@example.com",
        password_hash="must-not-be-returned",
        role=role,
        active=True,
    )


def create_admin() -> User:
    """Create an administrator."""

    return create_user(
        user_id=1,
        role=UserRole.ADMIN,
        customer_id=None,
    )


def authenticate(user: User) -> None:
    """Override authentication with one user."""

    def override_current_user() -> User:
        return user

    app.dependency_overrides[
        get_current_user
    ] = override_current_user


def create_category() -> Category:
    """Create an in-memory category."""

    return Category(
        id=10,
        name="Vegetables",
        description="Fresh vegetables",
        active=True,
    )


def create_product() -> Product:
    """Create an in-memory product."""

    return Product(
        id=20,
        category_id=10,
        name="Tomatoes",
        description="Fresh tomatoes",
        default_price=Decimal("8.90"),
        stock=Decimal("25.000"),
        image_url=None,
        active=True,
    )


def test_admin_can_create_category(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An administrator can create a category."""

    authenticate(create_admin())

    category = create_category()

    def fake_create_category(
        db: Any,
        *,
        name: str,
        description: str | None,
        active: bool,
    ) -> Category:
        assert name == "Vegetables"
        assert description == "Fresh vegetables"
        assert active is True

        return category

    monkeypatch.setattr(
        admin_catalog.catalog_service,
        "create_category",
        fake_create_category,
    )

    response = client.post(
        "/api/v1/admin/categories",
        json={
            "name": "Vegetables",
            "description": "Fresh vegetables",
            "active": True,
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 10,
        "name": "Vegetables",
        "description": "Fresh vegetables",
        "active": True,
    }


def test_duplicate_category_returns_conflict(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A duplicate category name returns HTTP 409."""

    authenticate(create_admin())

    def fake_create_category(
        db: Any,
        **kwargs: Any,
    ) -> Category:
        raise (
            admin_catalog.catalog_service
            .CategoryNameConflictError()
        )

    monkeypatch.setattr(
        admin_catalog.catalog_service,
        "create_category",
        fake_create_category,
    )

    response = client.post(
        "/api/v1/admin/categories",
        json={
            "name": "Vegetables",
            "active": True,
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Category name already exists",
    }


def test_admin_can_deactivate_category(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An administrator can deactivate a category."""

    authenticate(create_admin())

    category = create_category()
    category.active = False

    def fake_update_category(
        db: Any,
        *,
        category_id: int,
        changes: dict[str, object],
    ) -> Category:
        assert category_id == 10
        assert changes == {
            "active": False,
        }

        return category

    monkeypatch.setattr(
        admin_catalog.catalog_service,
        "update_category",
        fake_update_category,
    )

    response = client.patch(
        "/api/v1/admin/categories/10",
        json={
            "active": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["active"] is False


def test_admin_can_create_product(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An administrator can create a product."""

    authenticate(create_admin())

    product = create_product()

    def fake_create_product(
        db: Any,
        *,
        category_id: int,
        name: str,
        description: str | None,
        default_price: object,
        stock: object,
        image_url: str | None,
        active: bool,
    ) -> Product:
        assert category_id == 10
        assert name == "Tomatoes"
        assert description == "Fresh tomatoes"
        assert default_price == Decimal("8.90")
        assert stock == Decimal("25.000")
        assert image_url is None
        assert active is True

        return product

    monkeypatch.setattr(
        admin_catalog.catalog_service,
        "create_product",
        fake_create_product,
    )

    response = client.post(
        "/api/v1/admin/products",
        json={
            "category_id": 10,
            "name": "Tomatoes",
            "description": "Fresh tomatoes",
            "default_price": "8.90",
            "stock": "25.000",
            "image_url": None,
            "active": True,
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 20,
        "category_id": 10,
        "name": "Tomatoes",
        "description": "Fresh tomatoes",
        "default_price": "8.90",
        "stock": "25.000",
        "image_url": None,
        "active": True,
    }


def test_active_product_requires_active_category(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An active product cannot use an inactive category."""

    authenticate(create_admin())

    def fake_create_product(
        db: Any,
        **kwargs: Any,
    ) -> Product:
        raise (
            admin_catalog.catalog_service
            .InactiveCategoryError()
        )

    monkeypatch.setattr(
        admin_catalog.catalog_service,
        "create_product",
        fake_create_product,
    )

    response = client.post(
        "/api/v1/admin/products",
        json={
            "category_id": 10,
            "name": "Tomatoes",
            "default_price": "8.90",
            "stock": "25.000",
            "active": True,
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "An active product requires "
            "an active category"
        ),
    }


def test_admin_can_update_product_metadata(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An administrator updates metadata without stock."""

    authenticate(create_admin())

    product = create_product()
    product.default_price = Decimal("9.50")

    def fake_update_product(
        db: Any,
        *,
        product_id: int,
        changes: dict[str, object],
    ) -> Product:
        assert product_id == 20
        assert changes == {
            "default_price": Decimal("9.50"),
        }

        return product

    monkeypatch.setattr(
        admin_catalog.catalog_service,
        "update_product",
        fake_update_product,
    )

    response = client.patch(
        "/api/v1/admin/products/20",
        json={
            "default_price": "9.50",
        },
    )

    assert response.status_code == 200
    assert response.json()["default_price"] == "9.50"


def test_customer_cannot_manage_catalog(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A customer cannot access catalog administration."""

    customer_user = create_user(
        user_id=2,
        role=UserRole.CUSTOMER_USER,
        customer_id=1,
    )

    authenticate(customer_user)

    service_called = False

    def fake_create_category(
        db: Any,
        **kwargs: Any,
    ) -> Category:
        nonlocal service_called
        service_called = True
        return create_category()

    monkeypatch.setattr(
        admin_catalog.catalog_service,
        "create_category",
        fake_create_category,
    )

    response = client.post(
        "/api/v1/admin/categories",
        json={
            "name": "Vegetables",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Insufficient permissions",
    }

    assert service_called is False


def test_admin_catalog_requires_authentication(
    client: TestClient,
) -> None:
    """Unauthenticated requests receive HTTP 401."""

    response = client.post(
        "/api/v1/admin/categories",
        json={
            "name": "Vegetables",
        },
    )

    assert response.status_code == 401
    assert response.headers[
        "www-authenticate"
    ] == "Bearer"


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        (
            "post",
            "/api/v1/admin/categories",
            {
                "name": "   ",
            },
        ),
        (
            "patch",
            "/api/v1/admin/categories/0",
            {
                "active": False,
            },
        ),
        (
            "patch",
            "/api/v1/admin/categories/10",
            {},
        ),
        (
            "post",
            "/api/v1/admin/products",
            {
                "category_id": 10,
                "name": "Tomatoes",
                "default_price": "-1.00",
            },
        ),
        (
            "patch",
            "/api/v1/admin/products/0",
            {
                "active": False,
            },
        ),
        (
            "patch",
            "/api/v1/admin/products/20",
            {
                "stock": "100.000",
            },
        ),
        (
            "patch",
            "/api/v1/admin/products/20",
            {},
        ),
    ],
)
def test_admin_catalog_validation(
    client: TestClient,
    method: str,
    path: str,
    body: dict[str, object],
) -> None:
    """Invalid catalog requests return HTTP 422."""

    authenticate(create_admin())

    response = client.request(
        method,
        path,
        json=body,
    )

    assert response.status_code == 422


def test_category_with_active_products_cannot_be_disabled(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A category with active products returns HTTP 409."""

    authenticate(create_admin())

    def fake_update_category(
        db: Any,
        *,
        category_id: int,
        changes: dict[str, object],
    ) -> Category:
        assert category_id == 10
        assert changes == {
            "active": False,
        }

        raise (
            admin_catalog.catalog_service
            .CategoryHasActiveProductsError()
        )

    monkeypatch.setattr(
        admin_catalog.catalog_service,
        "update_category",
        fake_update_category,
    )

    response = client.patch(
        "/api/v1/admin/categories/10",
        json={
            "active": False,
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Category has active products",
    }