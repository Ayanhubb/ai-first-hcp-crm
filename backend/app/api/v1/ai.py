"""AI Assistant APIs — suggestions only; durable writes via Interaction APIs."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.api.deps import RequireAnyRole, get_ai_assist_service
from app.schemas.ai import (
    AiAssistRequest,
    AiAssistResponse,
    AiEditRequest,
    AiHistorySummaryRequest,
    AiHistorySummaryResponse,
)
from app.services.ai_assist_service import AiAssistService

router = APIRouter(prefix="/ai", tags=["AI"])


def _correlation_uuid(request: Request) -> UUID:
    raw = getattr(request.state, "correlation_id", None)
    try:
        return UUID(str(raw)) if raw else UUID(int=0)
    except ValueError:
        return UUID(int=0)


@router.post("/assist", response_model=AiAssistResponse, summary="Analyze interaction notes")
def assist(
    payload: AiAssistRequest,
    request: Request,
    current_user: RequireAnyRole,
    service: Annotated[AiAssistService, Depends(get_ai_assist_service)],
) -> AiAssistResponse:
    return service.assist(
        payload,
        actor=current_user,
        correlation_id=_correlation_uuid(request),
    )


@router.post("/edit", response_model=AiAssistResponse, summary="Guided rewrite / regenerate")
def edit(
    payload: AiEditRequest,
    request: Request,
    current_user: RequireAnyRole,
    service: Annotated[AiAssistService, Depends(get_ai_assist_service)],
) -> AiAssistResponse:
    return service.edit(
        payload,
        actor=current_user,
        correlation_id=_correlation_uuid(request),
    )


@router.post(
    "/history-summary",
    response_model=AiHistorySummaryResponse,
    summary="Summarize prior HCP interactions",
)
def history_summary(
    payload: AiHistorySummaryRequest,
    request: Request,
    current_user: RequireAnyRole,
    service: Annotated[AiAssistService, Depends(get_ai_assist_service)],
) -> AiHistorySummaryResponse:
    return service.history_summary(
        payload,
        actor=current_user,
        correlation_id=_correlation_uuid(request),
    )
