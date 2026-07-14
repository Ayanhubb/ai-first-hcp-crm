"""Interaction aggregate schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.common import ORMModel, Page, StrictModel
from app.schemas.enums import (
    FollowUpPriority,
    FollowUpStatus,
    InteractionSentiment,
    InteractionStatus,
    RecordSource,
    VisitChannel,
)
from app.schemas.product import ProductResponse


class FollowUpCreate(StrictModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10000)
    priority: FollowUpPriority = FollowUpPriority.MEDIUM
    due_at: datetime | None = None


class FollowUpResponse(ORMModel):
    id: UUID
    interaction_id: UUID
    user_id: UUID
    title: str
    description: str | None = None
    priority: FollowUpPriority
    due_at: datetime | None = None
    status: FollowUpStatus
    source: RecordSource
    created_at: datetime
    updated_at: datetime


class InteractionProductResponse(ORMModel):
    product_id: UUID
    confidence: Decimal | None = None
    source: RecordSource
    product: ProductResponse | None = None


class InteractionCreate(StrictModel):
    hcp_id: UUID
    visit_at: datetime
    channel: VisitChannel
    notes: str = Field(min_length=1, max_length=20000)
    status: InteractionStatus = InteractionStatus.SAVED
    summary: str | None = Field(default=None, max_length=10000)
    sentiment: InteractionSentiment | None = None
    sentiment_score: Decimal | None = Field(default=None, ge=0, le=1)
    medical_topics: list[str] = Field(default_factory=list, max_length=50)
    product_ids: list[UUID] = Field(default_factory=list)
    follow_ups: list[FollowUpCreate] = Field(default_factory=list)
    ai_run_id: UUID | None = None

    @field_validator("medical_topics")
    @classmethod
    def topic_item_length(cls, value: list[str]) -> list[str]:
        for topic in value:
            if not topic or len(topic) > 200:
                raise ValueError("each medical topic must be 1–200 characters")
        return value

    @model_validator(mode="after")
    def notes_required_when_saved(self) -> InteractionCreate:
        if self.status is InteractionStatus.SAVED and not self.notes.strip():
            raise ValueError("notes are required when status is saved")
        return self


class InteractionUpdate(StrictModel):
    visit_at: datetime | None = None
    channel: VisitChannel | None = None
    notes: str | None = Field(default=None, min_length=1, max_length=20000)
    status: InteractionStatus | None = None
    summary: str | None = Field(default=None, max_length=10000)
    sentiment: InteractionSentiment | None = None
    sentiment_score: Decimal | None = Field(default=None, ge=0, le=1)
    medical_topics: list[str] | None = Field(default=None, max_length=50)
    product_ids: list[UUID] | None = None
    follow_ups: list[FollowUpCreate] | None = None

    @field_validator("medical_topics")
    @classmethod
    def topic_item_length(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        for topic in value:
            if not topic or len(topic) > 200:
                raise ValueError("each medical topic must be 1–200 characters")
        return value


class InteractionSummary(ORMModel):
    id: UUID
    hcp_id: UUID
    user_id: UUID
    visit_at: datetime
    channel: VisitChannel
    status: InteractionStatus
    sentiment: InteractionSentiment | None = None
    summary: str | None = None
    created_at: datetime
    updated_at: datetime
    hcp_name: str | None = None


class InteractionDetail(ORMModel):
    id: UUID
    user_id: UUID
    hcp_id: UUID
    visit_at: datetime
    channel: VisitChannel
    notes: str
    summary: str | None = None
    sentiment: InteractionSentiment | None = None
    sentiment_score: Decimal | None = None
    medical_topics: list[str] = Field(default_factory=list)
    ai_run_id: UUID | None = None
    status: InteractionStatus
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    products: list[InteractionProductResponse] = Field(default_factory=list)
    follow_ups: list[FollowUpResponse] = Field(default_factory=list)
    hcp: dict[str, object] | None = None


class InteractionListParams(ORMModel):
    hcp_id: UUID | None = None
    visit_from: datetime | None = None
    visit_to: datetime | None = None
    sentiment: InteractionSentiment | None = None
    status: InteractionStatus | None = None
    user_id: UUID | None = None
    sort: str | None = None


InteractionPage = Page[InteractionSummary]
