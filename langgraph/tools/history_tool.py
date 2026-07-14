"""Retrieve interaction history domain tool (read-only)."""

from __future__ import annotations

from uuid import UUID

from ..engine.exceptions import ToolError
from ..engine.retry import RetrySettings, call_with_retry
from ..state.schemas import InteractionBrief
from .base import HistoryPort


def retrieve_interaction_history(
    port: HistoryPort,
    *,
    hcp_id: str | UUID,
    limit: int,
    exclude_deleted: bool = True,
    retry_settings: RetrySettings | None = None,
) -> list[InteractionBrief]:
    """Load prior interactions for HCP context (bounded by AI_HISTORY_LIMIT)."""

    def _call() -> list[InteractionBrief]:
        try:
            return port.list_for_hcp(
                hcp_id,
                limit=limit,
                exclude_deleted=exclude_deleted,
            )
        except ToolError:
            raise
        except Exception as exc:
            transient = "connection" in str(exc).lower() or "timeout" in str(exc).lower()
            raise ToolError(
                f"History retrieval failed: {exc}",
                code="HISTORY_DB_ERROR",
                fatal=True,
                transient=transient,
            ) from exc

    settings = retry_settings or RetrySettings()
    return call_with_retry(
        _call,
        max_retries=settings.tool_max_retries,
        settings=settings,
        retry_on=lambda e: isinstance(e, ToolError) and e.transient,
    )
