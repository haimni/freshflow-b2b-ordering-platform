"""Tests for administrator-only user endpoints."""

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.v1.routes import admin_users
from app.db.session import get_db
from app.deps.auth import get_current_user
from app.main import app
from app.models.enums import UserRole
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
    """Create an in-memory user for authorization tests."""

    return User(
        id=user_id,
        customer_id=customer_id,
        name=f"Test User {user_id}",
        email=f"user{user_id}@example.com",
        password_hash="must-not-be-returned",
        role=role,
        active=True,
    )


def test_admin_can_list_users(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An administrator can retrieve application users."""

    admin = create_user(
        user_id=1,
        role=UserRole.ADMIN,
        customer_id=None,
    )

    customer_user = create_user(
        user_id=2,
        role=UserRole.CUSTOMER_USER,
        customer_id=1,
    )

    def override_current_user() -> User:
        return admin

    def fake_list_users(
        db: Any,
        *,
        offset: int,
        limit: int,
    ) -> list[User]:
        assert offset == 0
        assert limit == 100

        return [admin, customer_user]

    app.dependency_overrides[
        get_current_user
    ] = override_current_user

    monkeypatch.setattr(
        admin_users.user_service,
        "list_users",
        fake_list_users,
    )

    response = client.get("/api/v1/admin/users")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["role"] == "admin"
    assert response.json()[1]["role"] == "customer_user"

    assert "password_hash" not in response.json()[0]
    assert "password_hash" not in response.json()[1]


def test_customer_user_cannot_list_users(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A customer user receives HTTP 403."""

    customer_user = create_user(
        user_id=2,
        role=UserRole.CUSTOMER_USER,
        customer_id=1,
    )

    service_called = False

    def override_current_user() -> User:
        return customer_user

    def fake_list_users(
        db: Any,
        *,
        offset: int,
        limit: int,
    ) -> list[User]:
        nonlocal service_called
        service_called = True
        return []

    app.dependency_overrides[
        get_current_user
    ] = override_current_user

    monkeypatch.setattr(
        admin_users.user_service,
        "list_users",
        fake_list_users,
    )

    response = client.get("/api/v1/admin/users")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Insufficient permissions",
    }

    # Authorization must fail before querying user data.
    assert service_called is False


def test_unauthenticated_user_cannot_list_users(
    client: TestClient,
) -> None:
    """A request without a token receives HTTP 401."""

    response = client.get("/api/v1/admin/users")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"