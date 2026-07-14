"""Append-only audit log persistence repository."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditRepository:
    """Data access for ``audit_logs`` (append-only)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def append(
        self,
        *,
        actor_user_id: uuid.UUID | None,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        correlation_id: uuid.UUID,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        row = AuditLog(
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            correlation_id=correlation_id,
        )
        self._session.add(row)
        self._session.flush()
        return row
