"""Healthcare professional persistence repository."""

from __future__ import annotations

import uuid

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.hcp import HealthcareProfessional
from app.schemas.common import SortSpec


class HcpRepository:
    """Data access for ``healthcare_professionals``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, hcp_id: uuid.UUID) -> HealthcareProfessional | None:
        return self._session.get(HealthcareProfessional, hcp_id)

    def create(
        self,
        *,
        first_name: str,
        last_name: str,
        specialty: str,
        institution: str | None = None,
        city: str | None = None,
        state: str | None = None,
        country: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        registration_number: str | None = None,
    ) -> HealthcareProfessional:
        row = HealthcareProfessional(
            first_name=first_name,
            last_name=last_name,
            specialty=specialty,
            institution=institution,
            city=city,
            state=state,
            country=country,
            email=email,
            phone=phone,
            registration_number=registration_number,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def search(
        self,
        *,
        page: int,
        page_size: int,
        sort: SortSpec,
        query: str | None = None,
        specialty: str | None = None,
        city: str | None = None,
        institution: str | None = None,
    ) -> tuple[list[HealthcareProfessional], int]:
        filters: list[object] = []
        if query:
            pattern = f"%{query}%"
            filters.append(
                or_(
                    HealthcareProfessional.first_name.ilike(pattern),
                    HealthcareProfessional.last_name.ilike(pattern),
                    HealthcareProfessional.institution.ilike(pattern),
                )
            )
        if specialty:
            filters.append(HealthcareProfessional.specialty.ilike(specialty.strip()))
        if city:
            filters.append(HealthcareProfessional.city.ilike(city.strip()))
        if institution:
            filters.append(HealthcareProfessional.institution.ilike(f"%{institution.strip()}%"))

        count_stmt = select(func.count()).select_from(HealthcareProfessional)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total = int(self._session.scalar(count_stmt) or 0)

        order_col = {
            "last_name": HealthcareProfessional.last_name,
            "specialty": HealthcareProfessional.specialty,
            "city": HealthcareProfessional.city,
        }[sort.field]
        order_by = order_col.desc() if sort.is_desc else order_col.asc()

        stmt: Select[tuple[HealthcareProfessional]] = select(HealthcareProfessional)
        if filters:
            stmt = stmt.where(*filters)
        stmt = (
            stmt.order_by(order_by, HealthcareProfessional.first_name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self._session.scalars(stmt).all()), total
