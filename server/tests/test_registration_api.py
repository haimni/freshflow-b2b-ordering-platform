"""API tests for customer self-registration."""

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.v1.routes import auth as auth_routes
from app.db.session import get_db
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


def valid_registration_payload() -> dict[str, str]:
    """Return a valid registration request."""

    return {
        "company_name": "  New Customer Ltd  ",
        "business_number": "515000099",
        "phone": "02-555-0199",
        "name": "  New Manager  ",
        "email": "NEW.MANAGER@EXAMPLE.COM",
        "password": "SecureDevelopment123!",
    }


def test_customer_registration_success(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid registration creates a customer manager."""

    created_user = User(
        id=10,
        customer_id=5,
        name="New Manager",
        email="new.manager@example.com",
        password_hash="must-not-be-returned",
        role=UserRole.CUSTOMER_MANAGER,
        active=True,
    )

    def fake_register_customer(
        db: Any,
        **registration_data: Any,
    ) -> User:
        assert registration_data == {
            "company_name": "New Customer Ltd",
            "business_number": "515000099",
            "phone": "02-555-0199",
            "name": "New Manager",
            "email": "new.manager@example.com",
            "password": "SecureDevelopment123!",
        }

        return created_user

    monkeypatch.setattr(
        auth_routes.registration_service,
        "register_customer",
        fake_register_customer,
    )

    response = client.post(
        "/api/v1/auth/register",
        json=valid_registration_payload(),
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 10,
        "customer_id": 5,
        "name": "New Manager",
        "email": "new.manager@example.com",
        "role": "customer_manager",
        "active": True,
    }
    assert "password_hash" not in response.json()


def test_duplicate_registration_returns_conflict(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Duplicate email or business number returns HTTP 409."""

    def fake_register_customer(
        db: Any,
        **registration_data: Any,
    ) -> User:
        raise (
            auth_routes.registration_service
            .RegistrationConflictError()
        )

    monkeypatch.setattr(
        auth_routes.registration_service,
        "register_customer",
        fake_register_customer,
    )

    response = client.post(
        "/api/v1/auth/register",
        json=valid_registration_payload(),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Email or business number already registered",
    }


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("email", "not-an-email"),
        ("password", "too-short"),
    ],
)
def test_invalid_registration_is_rejected_before_service(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    field_name: str,
    invalid_value: str,
) -> None:
    """Invalid registration data returns HTTP 422."""

    service_called = False

    def fake_register_customer(
        db: Any,
        **registration_data: Any,
    ) -> User:
        nonlocal service_called
        service_called = True

        raise AssertionError(
            "Registration service must not be called"
        )

    monkeypatch.setattr(
        auth_routes.registration_service,
        "register_customer",
        fake_register_customer,
    )

    payload = valid_registration_payload()
    payload[field_name] = invalid_value

    response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert response.status_code == 422
    assert service_called is False