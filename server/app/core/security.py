"""Password hashing and JWT utilities."""

from datetime import UTC, datetime, timedelta

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Create a secure Argon2 hash for a plaintext password."""

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    stored_password_hash: str,
) -> bool:
    """Return whether a plaintext password matches its stored hash."""

    try:
        return password_hash.verify(
            plain_password,
            stored_password_hash,
        )
    except Exception:
        # A malformed or unsupported stored hash must fail authentication
        # instead of causing an internal server error.
        return False


def create_access_token(
    subject: int,
    *,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed, time-limited access token."""

    now = datetime.now(UTC)

    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(
            minutes=settings.access_token_expire_minutes
        )
    )

    payload = {
        "sub": str(subject),
        "type": "access",
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> int:
    """Validate an access token and return its user ID."""

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    if payload.get("type") != "access":
        raise InvalidTokenError("Invalid token type")

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject.isdigit():
        raise InvalidTokenError("Invalid token subject")

    user_id = int(subject)

    if user_id <= 0:
        raise InvalidTokenError("Invalid user ID")

    return user_id