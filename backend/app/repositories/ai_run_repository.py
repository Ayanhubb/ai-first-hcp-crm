"""AI run persistence repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.ai_run import AiRun
from app.models.enums import AiRunStatus


class AiRunRepository:
    """Data access for ``ai_runs`` provenance rows."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, ai_run_id: uuid.UUID) -> AiRun | None:
        return self._session.get(AiRun, ai_run_id)

    def create_running(
        self,
        *,
        user_id: uuid.UUID | None,
        hcp_id: uuid.UUID | None,
        interaction_id: uuid.UUID | None,
        graph_name: str,
        model_name: str,
    ) -> AiRun:
        row = AiRun(
            user_id=user_id,
            hcp_id=hcp_id,
            interaction_id=interaction_id,
            graph_name=graph_name,
            model_name=model_name,
            status=AiRunStatus.RUNNING,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def finalize(
        self,
        ai_run: AiRun,
        *,
        status: AiRunStatus,
        latency_ms: int | None = None,
        token_usage: dict[str, Any] | None = None,
        error_message: str | None = None,
        state_snapshot: dict[str, Any] | None = None,
    ) -> AiRun:
        ai_run.status = status
        ai_run.latency_ms = latency_ms
        ai_run.token_usage = token_usage
        ai_run.error_message = error_message
        ai_run.state_snapshot = state_snapshot
        ai_run.finished_at = datetime.now(UTC)
        self._session.add(ai_run)
        self._session.flush()
        return ai_run
