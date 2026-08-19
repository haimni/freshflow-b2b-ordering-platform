"""API tests for authentication endpoints."""

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.v1.routes import auth as auth_routes
from app.core.security import create_access_token
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


def create_admin_user() -> User:
    """Create an in-memory administrator for API tests."""

    return User(
        id=1,
        customer_id=None,
        name="Test Administrator",
        email="admin@example.com",
        password_hash="not-returned-by-the-api",
        role=UserRole.ADMIN,
        active=True,
    )


def test_login_success(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid credentials return a bearer token."""

    admin_user = create_admin_user()

    def fake_authenticate_user(
        db: Any,
        *,
        email: str,
        password: str,
    ) -> User:
        assert email == "admin@example.com"
        assert password == "CorrectPassword123!"
        return admin_user

    monkeypatch.setattr(
        auth_routes.auth_service,
        "authenticate_user",
        fake_authenticate_user,
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@example.com",
            "password": "CorrectPassword123!",
        },
    )

    assert response.status_code == 200

    response_body = response.json()

    assert response_body["token_type"] == "bearer"
    assert isinstance(response_body["access_token"], str)
    assert response_body["access_token"]


def test_login_with_invalid_credentials(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid credentials return HTTP 401."""

    def fake_authenticate_user(
        db: Any,
        *,
        email: str,
        password: str,
    ) -> None:
        return None

    monkeypatch.setattr(
        auth_routes.auth_service,
        "authenticate_user",
        fake_authenticate_user,
    )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@example.com",
            "password": "WrongPassword",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Incorrect email or password",
    }
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_returns_authenticated_user(
    client: TestClient,
) -> None:
    """The current-user endpoint returns safe user data."""

    admin_user = create_admin_user()

    def override_current_user() -> User:
        return admin_user

    app.dependency_overrides[
        get_current_user
    ] = override_current_user

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "customer_id": None,
        "name": "Test Administrator",
        "email": "admin@example.com",
        "role": "admin",
        "active": True,
    }

    assert "password_hash" not in response.json()


def test_me_without_token(
    client: TestClient,
) -> None:
    """A request without a bearer token is rejected."""

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_with_invalid_token(
    client: TestClient,
) -> None:
    """A malformed bearer token is rejected."""

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials",
    }


def test_me_with_expired_token(
    client: TestClient,
) -> None:
    """An expired bearer token is rejected."""

    from datetime import timedelta

    expired_token = create_access_token(
        subject=1,
        expires_delta=timedelta(seconds=-1),
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {expired_token}",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials",
    }