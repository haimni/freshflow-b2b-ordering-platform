"""Schemas for authentication tokens."""

from pydantic import BaseModel


class AccessToken(BaseModel):
    """Bearer access token returned after successful login."""

    access_token: str
    token_type: str = "bearer"