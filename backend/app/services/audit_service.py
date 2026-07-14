"""Central audit append API."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.audit_repository import AuditRepository


class AuditService:
    """Application façade for append-only audit writes."""

    def __init__(self, session: Session, audit_repo: AuditRepository | None = None) -> None:
        self._session = session
        self._audits = audit_repo or AuditRepository(session)

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
    ) -> None:
        self._audits.append(
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            correlation_id=correlation_id,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
        )
