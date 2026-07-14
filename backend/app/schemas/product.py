"""Product catalog schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import ORMModel, Page


class ProductResponse(ORMModel):
    id: UUID
    code: str
    name: str
    therapeutic_area: str | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProductListParams(ORMModel):
    query: str | None = Field(default=None, max_length=200)
    therapeutic_area: str | None = None
    is_active: bool | None = True
    sort: str | None = None


ProductPage = Page[ProductResponse]
