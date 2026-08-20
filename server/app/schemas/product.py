"""Pydantic schemas for catalog products."""

from decimal import Decimal
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class ProductCreate(BaseModel):
    """Product creation request."""

    model_config = ConfigDict(
    str_strip_whitespace=True,
    extra="forbid",
    )

    category_id: int = Field(gt=0)

    name: str = Field(
        min_length=1,
        max_length=150,
    )

    description: str | None = None

    default_price: Decimal = Field(
        ge=0,
        max_digits=10,
        decimal_places=2,
    )

    stock: Decimal = Field(
        default=Decimal("0.000"),
        ge=0,
        max_digits=12,
        decimal_places=3,
    )

    image_url: str | None = Field(
        default=None,
        max_length=2048,
    )

    active: bool = True


class ProductUpdate(BaseModel):
    """Partial product metadata update."""

    model_config = ConfigDict(
    str_strip_whitespace=True,
    extra="forbid",
    )

    category_id: int | None = Field(
        default=None,
        gt=0,
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    description: str | None = None

    default_price: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
    )

    image_url: str | None = Field(
        default=None,
        max_length=2048,
    )

    active: bool | None = None

    @model_validator(mode="after")
    def validate_update(self) -> Self:
        """Require fields and reject null non-nullable values."""

        if not self.model_fields_set:
            raise ValueError(
                "At least one field must be provided"
            )

        non_nullable_fields = (
            "category_id",
            "name",
            "default_price",
            "active",
        )

        for field_name in non_nullable_fields:
            if (
                field_name in self.model_fields_set
                and getattr(self, field_name) is None
            ):
                raise ValueError(
                    f"{field_name} cannot be null"
                )

        return self


class ProductRead(BaseModel):
    """Product data returned by the API."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    category_id: int
    name: str
    description: str | None
    default_price: Decimal
    stock: Decimal
    image_url: str | None
    active: bool