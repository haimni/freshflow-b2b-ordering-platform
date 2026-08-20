"""Pydantic schemas for product categories."""

from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class CategoryCreate(BaseModel):
    """Category creation request."""

    model_config = ConfigDict(
    str_strip_whitespace=True,
    extra="forbid",
    )

    name: str = Field(
        min_length=1,
        max_length=120,
    )

    description: str | None = None
    active: bool = True


class CategoryUpdate(BaseModel):
    """Partial category update request."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )

    description: str | None = None
    active: bool | None = None

    @model_validator(mode="after")
    def validate_update(self) -> Self:
        """Require fields and reject null non-nullable values."""

        if not self.model_fields_set:
            raise ValueError(
                "At least one field must be provided"
            )

        for field_name in ("name", "active"):
            if (
                field_name in self.model_fields_set
                and getattr(self, field_name) is None
            ):
                raise ValueError(
                    f"{field_name} cannot be null"
                )

        return self


class CategoryRead(BaseModel):
    """Category data returned by the API."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    name: str
    description: str | None
    active: bool