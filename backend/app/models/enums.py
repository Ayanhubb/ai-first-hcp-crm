"""PostgreSQL-backed domain enums (mirrored in Alembic CREATE TYPE)."""

from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    MR = "mr"
    ADMIN = "admin"


class VisitChannel(str, enum.Enum):
    IN_PERSON = "in_person"
    VIRTUAL = "virtual"
    PHONE = "phone"


class InteractionSentiment(str, enum.Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class InteractionStatus(str, enum.Enum):
    DRAFT = "draft"
    SAVED = "saved"


class RecordSource(str, enum.Enum):
    AI = "ai"
    MANUAL = "manual"


class FollowUpPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FollowUpStatus(str, enum.Enum):
    OPEN = "open"
    DONE = "done"
    CANCELLED = "cancelled"


class AiRunStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PARTIAL = "partial"
