"""AI assist request/response schemas (suggestions only; no durable CRM writes)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import StrictModel
from app.schemas.enums import AiRunStatus, FollowUpPriority, InteractionSentiment


class AiAssistRequest(StrictModel):
    hcp_id: UUID
    notes: str = Field(min_length=20, max_length=20000)
    interaction_id: UUID | None = None
    include_history: bool = True


class AiEditRequest(StrictModel):
    hcp_id: UUID
    notes: str = Field(min_length=1, max_length=20000)
    edit_instruction: str = Field(min_length=5, max_length=2000)
    current_ai_fields: dict[str, Any] | None = None
    regenerate_derived: bool = True


class AiHistorySummaryRequest(StrictModel):
    hcp_id: UUID


class AiProductSuggestion(StrictModel):
    product_id: UUID
    name: str
    code: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class AiFollowUpSuggestion(StrictModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: FollowUpPriority = FollowUpPriority.MEDIUM
    due_in_days: int | None = Field(default=None, ge=0, le=365)


class AiErrorItem(StrictModel):
    node: str | None = None
    code: str | None = None
    message: str
    fatal: bool = False


class AiAssistResponse(StrictModel):
    ai_run_id: UUID
    status: AiRunStatus
    summary: str | None = None
    sentiment: InteractionSentiment | None = None
    sentiment_score: float | None = Field(default=None, ge=0.0, le=1.0)
    products: list[AiProductSuggestion] = Field(default_factory=list)
    medical_topics: list[str] = Field(default_factory=list)
    follow_ups: list[AiFollowUpSuggestion] = Field(default_factory=list)
    history_summary: str | None = None
    notes: str | None = None
    errors: list[AiErrorItem] = Field(default_factory=list)

    @field_validator("medical_topics")
    @classmethod
    def _normalize_topics(cls, value: list[str]) -> list[str]:
        return [t.strip() for t in value if t and t.strip()][:50]


class AiHistorySummaryResponse(StrictModel):
    ai_run_id: UUID
    history_summary: str | None = None
    interactions_considered: int = Field(ge=0, default=0)
