"""API tests for authenticated customer orders."""

from collections.abc import Generator
from datetime import datetime
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.v1.routes import customer_orders
from app.db.session import get_db
from app.deps.auth import get_current_user
from app.main import app
from app.models.enums import OrderStatus, UserRole
from app.models.order import Order
from app.models.order_item import OrderItem
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


def create_customer_user() -> User:
    """Create an authenticated customer manager."""

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


def create_order(
    *,
    order_id: int = 10,
    customer_id: int = 1,
    status: OrderStatus = OrderStatus.PENDING,
) -> Order:
    """Create an in-memory order for API tests."""

    order = Order(
        id=order_id,
        customer_id=customer_id,
        contract_id=5,
        created_by_user_id=2,
        total=Decimal("15.80"),
        status=status,
        created_at=datetime(2026, 8, 19, 12, 0, 0),
        updated_at=datetime(2026, 8, 19, 12, 0, 0),
    )

    order.items.append(
        OrderItem(
            id=100,
            order_id=order_id,
            product_id=1,
            quantity=Decimal("2.000"),
            unit_price=Decimal("7.90"),
            line_total=Decimal("15.80"),
        )
    )

    return order


def authenticate_customer(
    user: User,
) -> None:
    """Override authentication with one customer user."""

    def override_current_user() -> User:
        return user

    app.dependency_overrides[
        get_current_user
    ] = override_current_user


def test_create_customer_order(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A customer can create a pending order."""

    customer_user = create_customer_user()
    pending_order = create_order()

    authenticate_customer(customer_user)

    def fake_create_order(
        db: Any,
        *,
        customer_id: int,
        created_by_user_id: int,
        requested_items: list[tuple[int, Decimal]],
    ) -> Order:
        assert customer_id == 1
        assert created_by_user_id == 2
        assert requested_items == [
            (
                1,
                Decimal("2.000"),
            )
        ]

        return pending_order

    monkeypatch.setattr(
        customer_orders.order_service,
        "create_order",
        fake_create_order,
    )

    response = client.post(
        "/api/v1/customer/orders",
        json={
            "items": [
                {
                    "product_id": 1,
                    "quantity": "2.000",
                }
            ]
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 10,
        "customer_id": 1,
        "contract_id": 5,
        "created_by_user_id": 2,
        "total": "15.80",
        "status": "pending",
        "created_at": "2026-08-19T12:00:00",
        "updated_at": "2026-08-19T12:00:00",
        "items": [
            {
                "id": 100,
                "product_id": 1,
                "quantity": "2.000",
                "unit_price": "7.90",
                "line_total": "15.80",
            }
        ],
    }


def test_read_customer_orders(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A customer can list only its orders."""

    customer_user = create_customer_user()
    pending_order = create_order()

    authenticate_customer(customer_user)

    def fake_get_customer_orders(
        db: Any,
        *,
        customer_id: int,
        offset: int,
        limit: int,
    ) -> list[Order]:
        assert customer_id == 1
        assert offset == 0
        assert limit == 20

        return [pending_order]

    monkeypatch.setattr(
        customer_orders.order_service,
        "get_customer_orders",
        fake_get_customer_orders,
    )

    response = client.get(
        "/api/v1/customer/orders"
    )

    assert response.status_code == 200

    response_body = response.json()

    assert len(response_body) == 1
    assert response_body[0]["id"] == 10
    assert response_body[0]["customer_id"] == 1
    assert response_body[0]["status"] == "pending"


def test_read_customer_order(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A customer can read one owned order."""

    customer_user = create_customer_user()
    pending_order = create_order()

    authenticate_customer(customer_user)

    def fake_get_customer_order(
        db: Any,
        *,
        customer_id: int,
        order_id: int,
    ) -> Order:
        assert customer_id == 1
        assert order_id == 10

        return pending_order

    monkeypatch.setattr(
        customer_orders.order_service,
        "get_customer_order",
        fake_get_customer_order,
    )

    response = client.get(
        "/api/v1/customer/orders/10"
    )

    assert response.status_code == 200
    assert response.json()["id"] == 10
    assert response.json()["customer_id"] == 1


def test_missing_customer_order_returns_not_found(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing or foreign order returns HTTP 404."""

    customer_user = create_customer_user()

    authenticate_customer(customer_user)

    def fake_get_customer_order(
        db: Any,
        *,
        customer_id: int,
        order_id: int,
    ) -> None:
        assert customer_id == 1
        assert order_id == 999

        return None

    monkeypatch.setattr(
        customer_orders.order_service,
        "get_customer_order",
        fake_get_customer_order,
    )

    response = client.get(
        "/api/v1/customer/orders/999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Order not found",
    }


def test_cancel_pending_order(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A customer can cancel a pending order."""

    customer_user = create_customer_user()

    cancelled_order = create_order(
        status=OrderStatus.CANCELLED,
    )

    authenticate_customer(customer_user)

    def fake_cancel_order(
        db: Any,
        *,
        customer_id: int,
        order_id: int,
    ) -> Order:
        assert customer_id == 1
        assert order_id == 10

        return cancelled_order

    monkeypatch.setattr(
        customer_orders.order_service,
        "cancel_order",
        fake_cancel_order,
    )

    response = client.post(
        "/api/v1/customer/orders/10/cancel"
    )

    assert response.status_code == 200
    assert response.json()["id"] == 10
    assert response.json()["status"] == "cancelled"


def test_cancel_missing_order_returns_not_found(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cancelling a missing or foreign order returns HTTP 404."""

    customer_user = create_customer_user()

    authenticate_customer(customer_user)

    def fake_cancel_order(
        db: Any,
        *,
        customer_id: int,
        order_id: int,
    ) -> Order:
        raise (
            customer_orders.order_service
            .OrderNotFoundError()
        )

    monkeypatch.setattr(
        customer_orders.order_service,
        "cancel_order",
        fake_cancel_order,
    )

    response = client.post(
        "/api/v1/customer/orders/999/cancel"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Order not found",
    }


def test_cancel_non_pending_order_returns_conflict(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An order that is no longer pending cannot be cancelled."""

    customer_user = create_customer_user()

    authenticate_customer(customer_user)

    def fake_cancel_order(
        db: Any,
        *,
        customer_id: int,
        order_id: int,
    ) -> Order:
        raise (
            customer_orders.order_service
            .OrderNotCancellableError(
                OrderStatus.CANCELLED
            )
        )

    monkeypatch.setattr(
        customer_orders.order_service,
        "cancel_order",
        fake_cancel_order,
    )

    response = client.post(
        "/api/v1/customer/orders/10/cancel"
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Only pending orders can be cancelled; "
            "current status is cancelled"
        ),
    }


def test_order_requires_current_contract(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An order cannot be created without a current contract."""

    customer_user = create_customer_user()

    authenticate_customer(customer_user)

    def fake_create_order(
        db: Any,
        **kwargs: Any,
    ) -> Order:
        raise (
            customer_orders.order_service
            .ContractRequiredError()
        )

    monkeypatch.setattr(
        customer_orders.order_service,
        "create_order",
        fake_create_order,
    )

    response = client.post(
        "/api/v1/customer/orders",
        json={
            "items": [
                {
                    "product_id": 1,
                    "quantity": "1.000",
                }
            ]
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "A current contract is required",
    }


def test_insufficient_stock_returns_conflict(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An order exceeding stock returns HTTP 409."""

    customer_user = create_customer_user()

    authenticate_customer(customer_user)

    def fake_create_order(
        db: Any,
        **kwargs: Any,
    ) -> Order:
        raise (
            customer_orders.order_service
            .InsufficientStockError(1)
        )

    monkeypatch.setattr(
        customer_orders.order_service,
        "create_order",
        fake_create_order,
    )

    response = client.post(
        "/api/v1/customer/orders",
        json={
            "items": [
                {
                    "product_id": 1,
                    "quantity": "999.000",
                }
            ]
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Insufficient stock for product 1",
    }


def test_duplicate_products_are_rejected(
    client: TestClient,
) -> None:
    """One product cannot appear twice in an order."""

    customer_user = create_customer_user()

    authenticate_customer(customer_user)

    response = client.post(
        "/api/v1/customer/orders",
        json={
            "items": [
                {
                    "product_id": 1,
                    "quantity": "1.000",
                },
                {
                    "product_id": 1,
                    "quantity": "2.000",
                },
            ]
        },
    )

    assert response.status_code == 422


def test_admin_cannot_use_customer_orders(
    client: TestClient,
) -> None:
    """An administrator cannot impersonate a customer."""

    admin_user = create_admin_user()

    def override_current_user() -> User:
        return admin_user

    app.dependency_overrides[
        get_current_user
    ] = override_current_user

    response = client.get(
        "/api/v1/customer/orders"
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Insufficient permissions",
    }


def test_customer_orders_require_authentication(
    client: TestClient,
) -> None:
    """Unauthenticated requests receive HTTP 401."""

    response = client.get(
        "/api/v1/customer/orders"
    )

    assert response.status_code == 401
    assert response.headers[
        "www-authenticate"
    ] == "Bearer"


@pytest.mark.parametrize(
    ("path", "method"),
    [
        (
            "/api/v1/customer/orders?offset=-1",
            "get",
        ),
        (
            "/api/v1/customer/orders?limit=0",
            "get",
        ),
        (
            "/api/v1/customer/orders?limit=101",
            "get",
        ),
        (
            "/api/v1/customer/orders/0",
            "get",
        ),
        (
            "/api/v1/customer/orders/0/cancel",
            "post",
        ),
    ],
)
def test_order_parameter_validation(
    client: TestClient,
    path: str,
    method: str,
) -> None:
    """Invalid order parameters return HTTP 422."""

    customer_user = create_customer_user()

    authenticate_customer(customer_user)

    response = client.request(
        method,
        path,
    )

    assert response.status_code == 422