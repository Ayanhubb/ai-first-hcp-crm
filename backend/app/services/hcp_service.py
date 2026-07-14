"""HCP search and detail use cases."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.repositories.hcp_repository import HcpRepository
from app.schemas.common import Page, PaginationParams, parse_sort
from app.schemas.hcp import HcpCreate, HcpResponse, HcpSummary


_HCP_SORT = frozenset({"last_name", "specialty", "city"})


class HcpService:
    """Search, retrieve, and create healthcare professionals."""

    def __init__(self, session: Session, hcp_repo: HcpRepository | None = None) -> None:
        self._session = session
        self._hcps = hcp_repo or HcpRepository(session)

    def create(self, payload: HcpCreate) -> HcpResponse:
        if not payload.first_name or not payload.last_name or not payload.specialty:
            raise ValidationAppError(
                "first_name, last_name, and specialty are required",
                details=[{"field": "body", "issue": "missing required fields"}],
            )
        try:
            row = self._hcps.create(
                first_name=payload.first_name,
                last_name=payload.last_name,
                specialty=payload.specialty,
                institution=payload.institution,
                city=payload.city,
                state=payload.state,
                country=payload.country,
                email=payload.email,
                phone=payload.phone,
                registration_number=payload.registration_number,
            )
            self._session.commit()
        except Exception as exc:  # noqa: BLE001 — map unique constraint to 409
            self._session.rollback()
            msg = str(exc).lower()
            if "uq_hcps_registration_number" in msg or "registration_number" in msg:
                raise ConflictError("Registration number already exists") from exc
            raise
        return self.get_by_id(row.id)

    def search(
        self,
        *,
        pagination: PaginationParams,
        query: str | None = None,
        specialty: str | None = None,
        city: str | None = None,
        institution: str | None = None,
        sort: str | None = None,
    ) -> Page[HcpSummary]:
        if query is not None and len(query.strip()) < 2:
            raise ValidationAppError(
                "query must be at least 2 characters when provided",
                details=[{"field": "query", "issue": "min length 2"}],
            )
        try:
            sort_spec = parse_sort(sort, whitelist=_HCP_SORT, default="last_name:asc")
        except ValueError as exc:
            raise ValidationAppError(str(exc), details=[{"field": "sort", "issue": str(exc)}]) from exc

        rows, total = self._hcps.search(
            page=pagination.page,
            page_size=pagination.page_size,
            sort=sort_spec,
            query=query.strip() if query else None,
            specialty=specialty,
            city=city,
            institution=institution,
        )
        return Page[HcpSummary](
            items=[HcpSummary.model_validate(row) for row in rows],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    def get_by_id(self, hcp_id: uuid.UUID) -> HcpResponse:
        hcp = self._hcps.get_by_id(hcp_id)
        if hcp is None:
            raise NotFoundError("Healthcare professional not found")
        return HcpResponse(
            id=hcp.id,
            first_name=hcp.first_name,
            last_name=hcp.last_name,
            specialty=hcp.specialty,
            institution=hcp.institution,
            city=hcp.city,
            state=hcp.state,
            country=hcp.country,
            email=hcp.email,
            phone=hcp.phone,
            registration_number=hcp.registration_number,
            metadata=hcp.metadata_,
            created_at=hcp.created_at,
            updated_at=hcp.updated_at,
        )
