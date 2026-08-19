"""Schemas for registration and authentication."""

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
)


class AccessToken(BaseModel):
    """Bearer access token returned after successful login."""

    access_token: str
    token_type: str = "bearer"


class CustomerRegistration(BaseModel):
    """Public registration request for a new customer."""

    company_name: str = Field(
        min_length=2,
        max_length=150,
    )

    business_number: str = Field(
        min_length=2,
        max_length=30,
    )

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    name: str = Field(
        min_length=2,
        max_length=120,
    )

    email: EmailStr

    password: SecretStr = Field(
        min_length=12,
        max_length=128,
    )

    @field_validator(
        "company_name",
        "business_number",
        "name",
    )
    @classmethod
    def strip_required_text(
        cls,
        value: str,
    ) -> str:
        """Remove accidental surrounding whitespace."""

        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("Value cannot be empty")

        return stripped_value

    @field_validator("phone")
    @classmethod
    def normalize_phone(
        cls,
        value: str | None,
    ) -> str | None:
        """Convert an empty phone value to None."""

        if value is None:
            return None

        stripped_value = value.strip()

        return stripped_value or None

    @field_validator("email")
    @classmethod
    def normalize_email(
        cls,
        value: EmailStr,
    ) -> str:
        """Store email addresses in lowercase."""

        return str(value).strip().lower()