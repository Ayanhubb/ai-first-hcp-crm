"""Interaction CRUD APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.api.deps import RequireAnyRole, get_interaction_service
from app.schemas.common import Page, PaginationParams
from app.schemas.enums import InteractionSentiment, InteractionStatus
from app.schemas.interaction import (
    InteractionCreate,
    InteractionDetail,
    InteractionSummary,
    InteractionUpdate,
)
from app.services.interaction_service import InteractionService

router = APIRouter(prefix="/interactions", tags=["Interactions"])


def _correlation_uuid(request: Request) -> UUID:
    raw = getattr(request.state, "correlation_id", None)
    try:
        return UUID(str(raw)) if raw else UUID(int=0)
    except ValueError:
        return UUID(int=0)


@router.post(
    "",
    response_model=InteractionDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create interaction",
)
def create_interaction(
    payload: InteractionCreate,
    request: Request,
    current_user: RequireAnyRole,
    service: Annotated[InteractionService, Depends(get_interaction_service)],
) -> InteractionDetail:
    client = request.client.host if request.client else None
    return service.create(
        payload,
        actor=current_user,
        correlation_id=_correlation_uuid(request),
        ip_address=client,
    )


@router.get("", response_model=Page[InteractionSummary], summary="List interactions")
def list_interactions(
    current_user: RequireAnyRole,
    service: Annotated[InteractionService, Depends(get_interaction_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    hcp_id: UUID | None = None,
    visit_from: datetime | None = None,
    visit_to: datetime | None = None,
    sentiment: InteractionSentiment | None = None,
    status_filter: InteractionStatus | None = Query(None, alias="status"),
    user_id: UUID | None = None,
    sort: str | None = None,
) -> Page[InteractionSummary]:
    return service.list_interactions(
        actor=current_user,
        pagination=PaginationParams(page=page, page_size=page_size),
        hcp_id=hcp_id,
        visit_from=visit_from,
        visit_to=visit_to,
        sentiment=sentiment,
        status=status_filter,
        user_id=user_id,
        sort=sort,
    )


@router.get(
    "/{interaction_id}",
    response_model=InteractionDetail,
    summary="Get interaction",
)
def get_interaction(
    interaction_id: UUID,
    current_user: RequireAnyRole,
    service: Annotated[InteractionService, Depends(get_interaction_service)],
) -> InteractionDetail:
    return service.get_by_id(interaction_id, actor=current_user)


@router.patch(
    "/{interaction_id}",
    response_model=InteractionDetail,
    summary="Update interaction",
)
def update_interaction(
    interaction_id: UUID,
    payload: InteractionUpdate,
    request: Request,
    current_user: RequireAnyRole,
    service: Annotated[InteractionService, Depends(get_interaction_service)],
) -> InteractionDetail:
    client = request.client.host if request.client else None
    return service.update(
        interaction_id,
        payload,
        actor=current_user,
        correlation_id=_correlation_uuid(request),
        ip_address=client,
    )


@router.delete(
    "/{interaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete interaction",
    response_class=Response,
)
def delete_interaction(
    interaction_id: UUID,
    request: Request,
    current_user: RequireAnyRole,
    service: Annotated[InteractionService, Depends(get_interaction_service)],
) -> Response:
    client = request.client.host if request.client else None
    service.soft_delete(
        interaction_id,
        actor=current_user,
        correlation_id=_correlation_uuid(request),
        ip_address=client,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
