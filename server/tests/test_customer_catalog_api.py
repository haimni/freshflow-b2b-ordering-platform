"""Tests for the authenticated customer catalog."""

from collections.abc import Generator
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.v1.routes import customer_catalog
from app.db.session import get_db
from app.deps.auth import get_current_user
from app.main import app
from app.models.enums import UserRole
from app.models.product import Product
from app.models.user import User
from app.services.customer_catalog import PricedProduct


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create an isolated API client."""

    def override_get_db() -> Generator[object, None, None]:
        yield object()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def create_customer_user() -> User:
    """Create an authenticated customer user."""

    return User(
        id=2,
        customer_id=1,
        name="Customer Manager",
        email="manager@example.com",
        password_hash="must-not-be-returned",
        role=UserRole.CUSTOMER_MANAGER,
        active=True,
    )


def create_admin_user() -> User:
    """Create an authenticated administrator."""

    return User(
        id=1,
        customer_id=None,
        name="Administrator",
        email="admin@example.com",
        password_hash="must-not-be-returned",
        role=UserRole.ADMIN,
        active=True,
    )


def create_product() -> Product:
    """Create an in-memory catalog product."""

    return Product(
        id=1,
        category_id=1,
        name="Tomatoes",
        description="Fresh tomatoes",
        default_price=Decimal("8.90"),
        stock=Decimal("250.000"),
        image_url=None,
        active=True,
    )


def test_customer_receives_effective_prices(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A customer receives its effective contract price."""

    customer_user = create_customer_user()
    product = create_product()

    def override_current_user() -> User:
        return customer_user

    def fake_list_customer_products(
        db: Any,
        *,
        customer_id: int,
        category_id: int | None,
        offset: int,
        limit: int,
    ) -> list[PricedProduct]:
        assert customer_id == 1
        assert category_id == 1
        assert offset == 0
        assert limit == 100

        return [
            PricedProduct(
                product=product,
                effective_price=Decimal("7.90"),
                price_source="contract",
                contract_id=1,
            )
        ]

    app.dependency_overrides[
        get_current_user
    ] = override_current_user

    monkeypatch.setattr(
        customer_catalog.catalog_service,
        "list_customer_products",
        fake_list_customer_products,
    )

    response = client.get(
        "/api/v1/customer/products",
        params={"category_id": 1},
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "category_id": 1,
            "name": "Tomatoes",
            "description": "Fresh tomatoes",
            "stock": "250.000",
            "image_url": None,
            "effective_price": "7.90",
            "price_source": "contract",
            "contract_id": 1,
        }
    ]


def test_admin_cannot_use_customer_catalog(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An administrator cannot impersonate a customer."""

    admin_user = create_admin_user()
    service_called = False

    def override_current_user() -> User:
        return admin_user

    def fake_list_customer_products(
        db: Any,
        **kwargs: Any,
    ) -> list[PricedProduct]:
        nonlocal service_called
        service_called = True
        return []

    app.dependency_overrides[
        get_current_user
    ] = override_current_user

    monkeypatch.setattr(
        customer_catalog.catalog_service,
        "list_customer_products",
        fake_list_customer_products,
    )

    response = client.get("/api/v1/customer/products")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Insufficient permissions",
    }
    assert service_called is False


def test_customer_catalog_requires_authentication(
    client: TestClient,
) -> None:
    """An unauthenticated request receives HTTP 401."""

    response = client.get("/api/v1/customer/products")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_multiple_current_contracts_return_conflict(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ambiguous customer pricing returns HTTP 409."""

    customer_user = create_customer_user()

    def override_current_user() -> User:
        return customer_user

    def fake_list_customer_products(
        db: Any,
        **kwargs: Any,
    ) -> list[PricedProduct]:
        raise (
            customer_catalog.catalog_service
            .MultipleCurrentContractsError()
        )

    app.dependency_overrides[
        get_current_user
    ] = override_current_user

    monkeypatch.setattr(
        customer_catalog.catalog_service,
        "list_customer_products",
        fake_list_customer_products,
    )

    response = client.get("/api/v1/customer/products")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Multiple current contracts found",
    }