"""Product catalog use cases."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.repositories.product_repository import ProductRepository
from app.schemas.common import Page, PaginationParams, parse_sort
from app.schemas.product import ProductResponse


_PRODUCT_SORT = frozenset({"name", "code", "therapeutic_area"})


class ProductService:
    """List and retrieve product catalog entries."""

    def __init__(self, session: Session, product_repo: ProductRepository | None = None) -> None:
        self._session = session
        self._products = product_repo or ProductRepository(session)

    def list_products(
        self,
        *,
        pagination: PaginationParams,
        query: str | None = None,
        therapeutic_area: str | None = None,
        is_active: bool | None = True,
        sort: str | None = None,
    ) -> Page[ProductResponse]:
        try:
            sort_spec = parse_sort(sort, whitelist=_PRODUCT_SORT, default="name:asc")
        except ValueError as exc:
            raise ValidationAppError(str(exc), details=[{"field": "sort", "issue": str(exc)}]) from exc

        rows, total = self._products.list(
            page=pagination.page,
            page_size=pagination.page_size,
            sort=sort_spec,
            query=query,
            therapeutic_area=therapeutic_area,
            is_active=is_active,
        )
        return Page[ProductResponse](
            items=[ProductResponse.model_validate(row) for row in rows],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    def get_by_id(self, product_id: uuid.UUID) -> ProductResponse:
        product = self._products.get_by_id(product_id)
        if product is None:
            raise NotFoundError("Product not found")
        return ProductResponse.model_validate(product)
