"""Healthcare professional APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import RequireAnyRole, get_hcp_service, get_interaction_service
from app.schemas.common import Page, PaginationParams
from app.schemas.hcp import HcpCreate, HcpResponse, HcpSummary
from app.schemas.interaction import InteractionSummary
from app.services.hcp_service import HcpService
from app.services.interaction_service import InteractionService

router = APIRouter(prefix="/hcps", tags=["HCPs"])


@router.post(
    "",
    response_model=HcpResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create HCP",
)
def create_hcp(
    payload: HcpCreate,
    _user: RequireAnyRole,
    service: Annotated[HcpService, Depends(get_hcp_service)],
) -> HcpResponse:
    return service.create(payload)


@router.get("", response_model=Page[HcpSummary], summary="Search / list HCPs")
def list_hcps(
    _user: RequireAnyRole,
    service: Annotated[HcpService, Depends(get_hcp_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    query: str | None = Query(None, min_length=2),
    specialty: str | None = None,
    city: str | None = None,
    institution: str | None = None,
    sort: str | None = None,
) -> Page[HcpSummary]:
    return service.search(
        pagination=PaginationParams(page=page, page_size=page_size),
        query=query,
        specialty=specialty,
        city=city,
        institution=institution,
        sort=sort,
    )


@router.get("/{hcp_id}", response_model=HcpResponse, summary="Get HCP by ID")
def get_hcp(
    hcp_id: UUID,
    _user: RequireAnyRole,
    service: Annotated[HcpService, Depends(get_hcp_service)],
) -> HcpResponse:
    return service.get_by_id(hcp_id)


@router.get(
    "/{hcp_id}/interactions",
    response_model=Page[InteractionSummary],
    summary="HCP interaction timeline",
)
def list_hcp_interactions(
    hcp_id: UUID,
    current_user: RequireAnyRole,
    service: Annotated[InteractionService, Depends(get_interaction_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    visit_from: datetime | None = None,
    visit_to: datetime | None = None,
    sort: str | None = None,
) -> Page[InteractionSummary]:
    return service.list_for_hcp(
        hcp_id,
        actor=current_user,
        pagination=PaginationParams(page=page, page_size=page_size),
        visit_from=visit_from,
        visit_to=visit_to,
        sort=sort,
    )
