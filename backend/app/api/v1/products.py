"""Product catalog APIs."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import RequireAnyRole, get_product_service
from app.schemas.common import Page, PaginationParams
from app.schemas.product import ProductResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=Page[ProductResponse], summary="List products")
def list_products(
    _user: RequireAnyRole,
    service: Annotated[ProductService, Depends(get_product_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    query: str | None = Query(None, max_length=200),
    therapeutic_area: str | None = None,
    is_active: bool | None = True,
    sort: str | None = None,
) -> Page[ProductResponse]:
    return service.list_products(
        pagination=PaginationParams(page=page, page_size=page_size),
        query=query,
        therapeutic_area=therapeutic_area,
        is_active=is_active,
        sort=sort,
    )


@router.get("/{product_id}", response_model=ProductResponse, summary="Get product")
def get_product(
    product_id: UUID,
    _user: RequireAnyRole,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    return service.get_by_id(product_id)
