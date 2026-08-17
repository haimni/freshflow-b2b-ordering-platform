"""Tests for password hashing and JWT security utilities."""

from datetime import timedelta

import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password() -> None:
    """A password matches its hash but is not stored as plaintext."""

    password = "DevelopmentPassword123!"

    stored_hash = hash_password(password)

    assert stored_hash != password
    assert verify_password(password, stored_hash) is True
    assert verify_password("WrongPassword", stored_hash) is False


def test_malformed_password_hash_is_rejected() -> None:
    """A malformed stored hash fails safely."""

    assert (
        verify_password(
            "DevelopmentPassword123!",
            "NOT_A_REAL_PASSWORD_HASH",
        )
        is False
    )


def test_access_token_round_trip() -> None:
    """A generated token contains a recoverable user ID."""

    token = create_access_token(subject=42)

    assert decode_access_token(token) == 42


def test_expired_access_token_is_rejected() -> None:
    """An expired access token cannot be decoded."""

    token = create_access_token(
        subject=42,
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_token_with_wrong_secret_is_rejected() -> None:
    """A token signed by another sufficiently long secret is rejected."""

    foreign_token = jwt.encode(
        {
            "sub": "42",
            "type": "access",
        },
        "different-secret-that-is-at-least-32-bytes-long",
        algorithm="HS256",
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(foreign_token)