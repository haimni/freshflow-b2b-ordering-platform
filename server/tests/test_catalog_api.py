"""Tests for the read-only catalog API."""

from collections.abc import Generator
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.v1.routes import catalog as catalog_routes
from app.db.session import get_db
from app.main import app
from app.models.category import Category
from app.models.product import Product


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create an API client without opening a real database session."""

    def override_get_db() -> Generator[object, None, None]:
        yield object()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def test_read_categories(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The categories endpoint returns serialized active categories."""

    categories = [
        Category(
            id=1,
            name="ירקות",
            description="ירקות טריים",
            active=True,
        ),
        Category(
            id=2,
            name="פירות",
            description="פירות טריים",
            active=True,
        ),
    ]

    def fake_list_active_categories(
        db: Any,
        *,
        offset: int,
        limit: int,
    ) -> list[Category]:
        return categories

    monkeypatch.setattr(
        catalog_routes.catalog_service,
        "list_active_categories",
        fake_list_active_categories,
    )

    response = client.get("/api/v1/categories")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "ירקות",
            "description": "ירקות טריים",
            "active": True,
        },
        {
            "id": 2,
            "name": "פירות",
            "description": "פירות טריים",
            "active": True,
        },
    ]


def test_read_products_with_category_filter(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The products endpoint forwards its filters to the service."""

    received_arguments: dict[str, int | None] = {}

    products = [
        Product(
            id=1,
            category_id=1,
            name="עגבניות",
            description="מחיר לקילוגרם",
            default_price=Decimal("8.90"),
            stock=Decimal("250.000"),
            image_url=None,
            active=True,
        )
    ]

    def fake_list_active_products(
        db: Any,
        *,
        category_id: int | None,
        offset: int,
        limit: int,
    ) -> list[Product]:
        received_arguments["category_id"] = category_id
        received_arguments["offset"] = offset
        received_arguments["limit"] = limit
        return products

    monkeypatch.setattr(
        catalog_routes.catalog_service,
        "list_active_products",
        fake_list_active_products,
    )

    response = client.get(
        "/api/v1/products",
        params={
            "category_id": 1,
            "offset": 5,
            "limit": 20,
        },
    )

    assert response.status_code == 200
    assert received_arguments == {
        "category_id": 1,
        "offset": 5,
        "limit": 20,
    }

    assert response.json() == [
        {
            "id": 1,
            "category_id": 1,
            "name": "עגבניות",
            "description": "מחיר לקילוגרם",
            "default_price": "8.90",
            "stock": "250.000",
            "image_url": None,
            "active": True,
        }
    ]


def test_read_existing_product(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An existing product is returned with HTTP 200."""

    product = Product(
        id=1,
        category_id=1,
        name="עגבניות",
        description=None,
        default_price=Decimal("8.90"),
        stock=Decimal("250.000"),
        image_url=None,
        active=True,
    )

    def fake_get_active_product(
        db: Any,
        product_id: int,
    ) -> Product:
        assert product_id == 1
        return product

    monkeypatch.setattr(
        catalog_routes.catalog_service,
        "get_active_product",
        fake_get_active_product,
    )

    response = client.get("/api/v1/products/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["name"] == "עגבניות"


def test_read_missing_product(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing product returns HTTP 404."""

    def fake_get_active_product(
        db: Any,
        product_id: int,
    ) -> None:
        return None

    monkeypatch.setattr(
        catalog_routes.catalog_service,
        "get_active_product",
        fake_get_active_product,
    )

    response = client.get("/api/v1/products/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Product not found",
    }


@pytest.mark.parametrize(
    ("query_string", "expected_status"),
    [
        ("offset=-1", 422),
        ("limit=0", 422),
        ("limit=101", 422),
        ("category_id=0", 422),
    ],
)
def test_product_query_validation(
    client: TestClient,
    query_string: str,
    expected_status: int,
) -> None:
    """Invalid product query parameters are rejected."""

    response = client.get(
        f"/api/v1/products?{query_string}"
    )

    assert response.status_code == expected_status