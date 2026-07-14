"""Product catalog persistence repository."""

from __future__ import annotations

import uuid

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.common import SortSpec


class ProductRepository:
    """Data access for ``products``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        return self._session.get(Product, product_id)

    def get_by_ids(self, product_ids: list[uuid.UUID]) -> list[Product]:
        if not product_ids:
            return []
        stmt = select(Product).where(Product.id.in_(product_ids))
        return list(self._session.scalars(stmt).all())

    def match_by_names(self, names: list[str]) -> list[Product]:
        if not names:
            return []
        lowered = [n.strip().lower() for n in names if n and n.strip()]
        if not lowered:
            return []
        stmt = select(Product).where(
            Product.is_active.is_(True),
            or_(*[func.lower(Product.name) == name for name in lowered]),
        )
        return list(self._session.scalars(stmt).all())

    def list(
        self,
        *,
        page: int,
        page_size: int,
        sort: SortSpec,
        query: str | None = None,
        therapeutic_area: str | None = None,
        is_active: bool | None = True,
    ) -> tuple[list[Product], int]:
        filters: list[object] = []
        if is_active is not None:
            filters.append(Product.is_active.is_(is_active))
        if therapeutic_area:
            filters.append(Product.therapeutic_area.ilike(therapeutic_area.strip()))
        if query:
            pattern = f"%{query.strip()}%"
            filters.append(or_(Product.code.ilike(pattern), Product.name.ilike(pattern)))

        count_stmt = select(func.count()).select_from(Product)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total = int(self._session.scalar(count_stmt) or 0)

        order_col = {
            "name": Product.name,
            "code": Product.code,
            "therapeutic_area": Product.therapeutic_area,
        }.get(sort.field, Product.name)
        order_by = order_col.desc() if sort.is_desc else order_col.asc()

        stmt: Select[tuple[Product]] = select(Product)
        if filters:
            stmt = stmt.where(*filters)
        stmt = (
            stmt.order_by(order_by)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self._session.scalars(stmt).all()), total
