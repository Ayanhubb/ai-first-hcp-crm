"""Shared request/response schemas and list pagination helpers."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


class ORMModel(BaseModel):
    """Base for response models built from ORM entities."""

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class StrictModel(BaseModel):
    """Base for mutating request bodies (forbid unknown fields)."""

    model_config = ConfigDict(extra="forbid")


class PaginationParams(BaseModel):
    """Offset pagination query params (api_design.md §5)."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=50)


class Page(BaseModel, Generic[T]):
    """List envelope with items and pagination meta."""

    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=50)


class SortSpec(BaseModel):
    """Parsed ``field:asc|desc`` sort token."""

    field: str
    direction: str  # asc | desc

    @property
    def is_desc(self) -> bool:
        return self.direction == "desc"


def parse_sort(
    sort: str | None,
    *,
    whitelist: frozenset[str],
    default: str,
) -> SortSpec:
    """
    Parse ``sort`` query param.

    Format: ``field:asc|desc``. Unknown fields raise ValueError for 422 mapping.
    """
    raw = (sort or default).strip()
    if ":" in raw:
        field, direction = raw.split(":", 1)
    else:
        field, direction = raw, "asc"

    field = field.strip()
    direction = direction.strip().lower()
    if field not in whitelist:
        raise ValueError(f"Unsupported sort field: {field}")
    if direction not in {"asc", "desc"}:
        raise ValueError("Sort direction must be 'asc' or 'desc'")
    return SortSpec(field=field, direction=direction)


class SortQuery(BaseModel):
    """Optional sort string validated against a whitelist at the service layer."""

    sort: str | None = None

    @field_validator("sort")
    @classmethod
    def nonempty_if_present(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            return None
        return value
