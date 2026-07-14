"""AI run persistence tool — writes ai_runs / audit only (never CRM interactions)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from ..engine.exceptions import ToolError
from ..engine.retry import RetrySettings, call_with_retry
from .base import PersistencePort


def _redact_snapshot(snapshot: dict[str, Any] | None) -> dict[str, Any] | None:
    """Drop likely PII and oversized raw LLM fragments from state snapshots."""
    if snapshot is None:
        return None
    redacted = dict(snapshot)
    redacted.pop("raw_llm_fragments", None)
    notes = redacted.get("notes")
    if isinstance(notes, str) and len(notes) > 4000:
        redacted["notes"] = notes[:4000] + "…"
    # Strip common PII patterns from free text fields lightly
    for key in ("notes", "summary", "history_summary", "edit_instruction"):
        val = redacted.get(key)
        if isinstance(val, str):
            redacted[key] = _mask_contact_info(val)
    return redacted


def _mask_contact_info(text: str) -> str:
    import re

    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[redacted-email]", text)
    text = re.sub(r"\b(?:\+?\d[\d\-\s]{8,}\d)\b", "[redacted-phone]", text)
    return text


def log_interaction(
    port: PersistencePort,
    *,
    ai_run_id: str | UUID,
    status: str,
    model_name: str | None,
    latency_ms: int | None,
    token_usage: dict[str, Any] | None,
    error_message: str | None,
    state_snapshot: dict[str, Any] | None,
    user_id: str | UUID,
    correlation_id: str | UUID | None,
    audit_action: str = "AI_ASSIST",
    retry_settings: RetrySettings | None = None,
) -> dict[str, str]:
    """Finalize ai_runs + emit audit. Must not write CRM ``interactions`` rows."""

    snapshot = _redact_snapshot(state_snapshot)

    def _call() -> dict[str, str]:
        try:
            port.finalize_ai_run(
                ai_run_id,
                status=status,
                model_name=model_name,
                latency_ms=latency_ms,
                token_usage=token_usage,
                error_message=error_message,
                state_snapshot=snapshot,
            )
            port.write_audit(
                action=audit_action,
                user_id=user_id,
                correlation_id=correlation_id,
                entity_type="ai_run",
                entity_id=ai_run_id,
                metadata={"status": status},
            )
            return {"ack": "ok"}
        except ToolError:
            raise
        except Exception as exc:
            transient = "connection" in str(exc).lower() or "timeout" in str(exc).lower()
            raise ToolError(
                f"AI run persistence failed: {exc}",
                code="PERSISTENCE_ERROR",
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
