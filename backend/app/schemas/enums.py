"""API-facing enums (snake_case strings matching PostgreSQL types)."""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    MR = "mr"
    ADMIN = "admin"


class VisitChannel(StrEnum):
    IN_PERSON = "in_person"
    VIRTUAL = "virtual"
    PHONE = "phone"


class InteractionSentiment(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class InteractionStatus(StrEnum):
    DRAFT = "draft"
    SAVED = "saved"


class FollowUpPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FollowUpStatus(StrEnum):
    OPEN = "open"
    DONE = "done"
    CANCELLED = "cancelled"


class RecordSource(StrEnum):
    AI = "ai"
    MANUAL = "manual"


class AiRunStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PARTIAL = "partial"
