"""API tests for administrator order management."""

from collections.abc import Generator
from datetime import datetime
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.v1.routes import admin_orders
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


def create_order(
    *,
    order_status: OrderStatus = OrderStatus.PENDING,
) -> Order:
    """Create an in-memory order response."""

    order = Order(
        id=10,
        customer_id=1,
        contract_id=5,
        created_by_user_id=2,
        total=Decimal("15.00"),
        status=order_status,
        created_at=datetime(2026, 8, 20, 10, 0, 0),
        updated_at=datetime(2026, 8, 20, 10, 0, 0),
    )

    order.items.append(
        OrderItem(
            id=100,
            order_id=10,
            product_id=1,
            quantity=Decimal("2.000"),
            unit_price=Decimal("7.50"),
            line_total=Decimal("15.00"),
        )
    )

    return order


def authenticate(user: User) -> None:
    """Override authentication with one user."""

    def override_current_user() -> User:
        return user

    app.dependency_overrides[
        get_current_user
    ] = override_current_user


def create_admin() -> User:
    """Create an administrator."""

    return create_user(
        user_id=1,
        role=UserRole.ADMIN,
        customer_id=None,
    )


def test_admin_can_list_orders(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An administrator can list and filter orders."""

    authenticate(create_admin())

    pending_order = create_order()

    def fake_list_orders(
        db: Any,
        *,
        customer_id: int | None,
        order_status: OrderStatus | None,
        offset: int,
        limit: int,
    ) -> list[Order]:
        assert customer_id == 1
        assert order_status == OrderStatus.PENDING
        assert offset == 0
        assert limit == 100

        return [pending_order]

    monkeypatch.setattr(
        admin_orders.order_service,
        "list_orders",
        fake_list_orders,
    )

    response = client.get(
        "/api/v1/admin/orders",
        params={
            "customer_id": 1,
            "status": "pending",
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == 10
    assert response.json()[0]["status"] == "pending"


def test_admin_can_read_order(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An administrator can read one order."""

    authenticate(create_admin())

    pending_order = create_order()

    def fake_get_order(
        db: Any,
        *,
        order_id: int,
    ) -> Order:
        assert order_id == 10

        return pending_order

    monkeypatch.setattr(
        admin_orders.order_service,
        "get_order",
        fake_get_order,
    )

    response = client.get(
        "/api/v1/admin/orders/10"
    )

    assert response.status_code == 200
    assert response.json()["id"] == 10


def test_missing_admin_order_returns_not_found(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing order returns HTTP 404."""

    authenticate(create_admin())

    def fake_get_order(
        db: Any,
        *,
        order_id: int,
    ) -> None:
        assert order_id == 999
        return None

    monkeypatch.setattr(
        admin_orders.order_service,
        "get_order",
        fake_get_order,
    )

    response = client.get(
        "/api/v1/admin/orders/999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Order not found",
    }


def test_admin_can_advance_order_status(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An administrator can apply the next status."""

    authenticate(create_admin())

    confirmed_order = create_order(
        order_status=OrderStatus.CONFIRMED,
    )

    def fake_update_order_status(
        db: Any,
        *,
        order_id: int,
        requested_status: OrderStatus,
    ) -> Order:
        assert order_id == 10
        assert requested_status == OrderStatus.CONFIRMED

        return confirmed_order

    monkeypatch.setattr(
        admin_orders.order_service,
        "update_order_status",
        fake_update_order_status,
    )

    response = client.patch(
        "/api/v1/admin/orders/10/status",
        json={
            "status": "confirmed",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


def test_invalid_status_transition_returns_conflict(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Skipping a workflow state returns HTTP 409."""

    authenticate(create_admin())

    def fake_update_order_status(
        db: Any,
        *,
        order_id: int,
        requested_status: OrderStatus,
    ) -> Order:
        raise (
            admin_orders.order_service
            .InvalidOrderTransitionError(
                OrderStatus.PENDING,
                OrderStatus.PROCESSING,
            )
        )

    monkeypatch.setattr(
        admin_orders.order_service,
        "update_order_status",
        fake_update_order_status,
    )

    response = client.patch(
        "/api/v1/admin/orders/10/status",
        json={
            "status": "processing",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Invalid order transition from "
            "pending to processing"
        ),
    }


def test_processing_order_cannot_be_cancelled(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cancelling a processing order returns HTTP 409."""

    authenticate(create_admin())

    def fake_update_order_status(
        db: Any,
        *,
        order_id: int,
        requested_status: OrderStatus,
    ) -> Order:
        raise (
            admin_orders
            .customer_order_service
            .OrderNotCancellableError(
                OrderStatus.PROCESSING
            )
        )

    monkeypatch.setattr(
        admin_orders.order_service,
        "update_order_status",
        fake_update_order_status,
    )

    response = client.patch(
        "/api/v1/admin/orders/10/status",
        json={
            "status": "cancelled",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Order cannot be cancelled from "
            "status processing"
        ),
    }


def test_customer_cannot_manage_admin_orders(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A customer cannot access administrator orders."""

    customer_user = create_user(
        user_id=2,
        role=UserRole.CUSTOMER_USER,
        customer_id=1,
    )

    authenticate(customer_user)

    service_called = False

    def fake_list_orders(
        db: Any,
        **kwargs: Any,
    ) -> list[Order]:
        nonlocal service_called
        service_called = True
        return []

    monkeypatch.setattr(
        admin_orders.order_service,
        "list_orders",
        fake_list_orders,
    )

    response = client.get(
        "/api/v1/admin/orders"
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Insufficient permissions",
    }

    assert service_called is False


def test_admin_orders_require_authentication(
    client: TestClient,
) -> None:
    """Unauthenticated requests receive HTTP 401."""

    response = client.get(
        "/api/v1/admin/orders"
    )

    assert response.status_code == 401
    assert response.headers[
        "www-authenticate"
    ] == "Bearer"


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        (
            "get",
            "/api/v1/admin/orders?customer_id=0",
            None,
        ),
        (
            "get",
            "/api/v1/admin/orders?offset=-1",
            None,
        ),
        (
            "get",
            "/api/v1/admin/orders?limit=0",
            None,
        ),
        (
            "get",
            "/api/v1/admin/orders?limit=101",
            None,
        ),
        (
            "get",
            "/api/v1/admin/orders?status=unknown",
            None,
        ),
        (
            "patch",
            "/api/v1/admin/orders/0/status",
            {
                "status": "confirmed",
            },
        ),
    ],
)
def test_admin_order_parameter_validation(
    client: TestClient,
    method: str,
    path: str,
    json_body: dict[str, str] | None,
) -> None:
    """Invalid administrator parameters return HTTP 422."""

    authenticate(create_admin())

    response = client.request(
        method,
        path,
        json=json_body,
    )

    assert response.status_code == 422