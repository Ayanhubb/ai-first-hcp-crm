"""Healthcare professional schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import ORMModel, Page, StrictModel


class HcpCreate(StrictModel):
    """Create a healthcare professional master record."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    specialty: str = Field(min_length=1, max_length=150)
    institution: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=50)
    registration_number: str | None = Field(default=None, max_length=100)

    @field_validator("first_name", "last_name", "specialty")
    @classmethod
    def required_strip(cls, value: str) -> str:
        trimmed = (value or "").strip()
        if not trimmed:
            raise ValueError("must not be blank")
        return trimmed

    @field_validator(
        "institution",
        "city",
        "state",
        "country",
        "email",
        "phone",
        "registration_number",
    )
    @classmethod
    def optional_strip(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None


class HcpResponse(ORMModel):
    id: UUID
    first_name: str
    last_name: str
    specialty: str
    institution: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    email: str | None = None
    phone: str | None = None
    registration_number: str | None = None
    metadata: dict[str, Any] | None = Field(default=None, validation_alias="metadata_")
    created_at: datetime | None = None
    updated_at: datetime | None = None


class HcpSummary(ORMModel):
    """Lean HCP row for list/search results."""

    id: UUID
    first_name: str
    last_name: str
    specialty: str
    institution: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None


class HcpSearchParams(ORMModel):
    query: str | None = None
    specialty: str | None = None
    city: str | None = None
    institution: str | None = None
    sort: str | None = None

    @field_validator("query")
    @classmethod
    def query_min_length(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        if not trimmed:
            return None
        if len(trimmed) < 2:
            raise ValueError("query must be at least 2 characters when provided")
        return trimmed


HcpPage = Page[HcpSummary]
