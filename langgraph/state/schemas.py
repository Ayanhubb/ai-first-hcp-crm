"""Nested Pydantic models for graph state and structured LLM outputs."""

from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class GraphMode(str, Enum):
    ASSIST = "assist"
    EDIT = "edit"
    HISTORY_ONLY = "history_only"
    PERSIST = "persist"


class RunStatus(str, Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class FollowUpPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InteractionBrief(BaseModel):
    id: UUID | None = None
    visit_at: str | None = None
    summary: str | None = None
    notes_excerpt: str | None = None
    sentiment: SentimentLabel | None = None
    channel: str | None = None


class ProductMatch(BaseModel):
    product_id: UUID
    code: str | None = None
    name: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class FollowUpDraft(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: FollowUpPriority = FollowUpPriority.MEDIUM
    due_in_days: int | None = Field(default=None, ge=0, le=365)


class NodeError(BaseModel):
    node: str
    code: str
    message: str
    fatal: bool = False


class HCPProfile(BaseModel):
    id: UUID
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    specialty: str | None = None
    city: str | None = None
    institution: str | None = None


class HCPCandidate(BaseModel):
    id: UUID
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    specialty: str | None = None
    city: str | None = None
    institution: str | None = None


class CatalogProduct(BaseModel):
    product_id: UUID
    code: str
    name: str
    therapeutic_area: str | None = None


class NodeTokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0


class ModelMeta(BaseModel):
    model_name: str | None = None
    nodes: dict[str, NodeTokenUsage] = Field(default_factory=dict)
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_latency_ms: int = 0

    def record(self, node: str, usage: NodeTokenUsage) -> None:
        self.nodes[node] = usage
        self.total_prompt_tokens = sum(n.prompt_tokens for n in self.nodes.values())
        self.total_completion_tokens = sum(n.completion_tokens for n in self.nodes.values())
        self.total_latency_ms = sum(n.latency_ms for n in self.nodes.values())


class SummaryOutput(BaseModel):
    summary: str = Field(min_length=1, max_length=4000)


class SentimentOutput(BaseModel):
    sentiment: SentimentLabel
    sentiment_score: float = Field(ge=0.0, le=1.0)


class ProductCandidatesOutput(BaseModel):
    """LLM proposes names only; IDs are grounded via catalog tool."""

    candidates: list[str] = Field(default_factory=list)

    @field_validator("candidates")
    @classmethod
    def _trim(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for v in values:
            name = (v or "").strip()
            if name and name not in cleaned:
                cleaned.append(name)
        return cleaned[:20]


class TopicsOutput(BaseModel):
    medical_topics: list[str] = Field(default_factory=list)

    @field_validator("medical_topics")
    @classmethod
    def _normalize(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for v in values:
            topic = " ".join((v or "").strip().split())
            key = topic.lower()
            if topic and key not in seen:
                seen.add(key)
                cleaned.append(topic)
        return cleaned[:50]


class FollowUpsOutput(BaseModel):
    follow_ups: list[FollowUpDraft] = Field(default_factory=list)

    @field_validator("follow_ups")
    @classmethod
    def _limit(cls, values: list[FollowUpDraft]) -> list[FollowUpDraft]:
        return values[:5]


class EditOutput(BaseModel):
    notes: str = Field(min_length=1)
    summary: str | None = None
    regenerate_derived: bool = True


class HistorySummaryOutput(BaseModel):
    history_summary: str = Field(min_length=1, max_length=4000)


def dump_model(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")
