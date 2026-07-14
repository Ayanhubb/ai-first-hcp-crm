"""log_interaction node — finalize ai_runs + audit (never CRM interaction save)."""

from __future__ import annotations

from typing import Any

from ..state.interaction_state import InteractionAssistState, append_error, finalize_status
from ..tools.persistence_tool import log_interaction as persistence_log
from ._common import NodeContext, catch_node


def make_log_interaction_node(ctx: NodeContext):
    def log_interaction_node(state: InteractionAssistState) -> dict[str, Any]:
        status = finalize_status(state)
        updates: dict[str, Any] = {"status": status}

        port = ctx.tools.persistence
        if port is None:
            # Non-blocking for local/dev when backend has not wired persistence yet
            return {
                **updates,
                **append_error(
                    "log_interaction",
                    "TOOL_NOT_CONFIGURED",
                    "Persistence port not configured; skipped ai_run finalization",
                    fatal=False,
                ),
            }

        meta = state.get("model_meta") or {}
        errors = state.get("errors") or []
        fatal_msgs = [e.get("message") for e in errors if e.get("fatal")]
        error_message = "; ".join(m for m in fatal_msgs if m) or None
        if status == "failed" and not error_message and errors:
            error_message = errors[-1].get("message")

        mode = state.get("mode")
        audit_action = "AI_EDIT" if mode == "edit" else "AI_ASSIST"
        if mode == "history_only":
            audit_action = "AI_HISTORY_SUMMARY"
        elif mode == "persist":
            audit_action = "AI_PERSIST"

        snapshot = {
            "mode": mode,
            "hcp_id": state.get("hcp_id"),
            "interaction_id": state.get("interaction_id"),
            "notes": state.get("notes"),
            "summary": state.get("summary"),
            "sentiment": state.get("sentiment"),
            "sentiment_score": state.get("sentiment_score"),
            "products": state.get("products"),
            "medical_topics": state.get("medical_topics"),
            "follow_ups": state.get("follow_ups"),
            "history_summary": state.get("history_summary"),
            "errors": errors,
            "status": status,
        }

        try:
            persistence_log(
                port,
                ai_run_id=state["ai_run_id"],
                status=status,
                model_name=meta.get("model_name") or ctx.llm.model_name,
                latency_ms=meta.get("total_latency_ms"),
                token_usage={
                    "prompt_tokens": meta.get("total_prompt_tokens"),
                    "completion_tokens": meta.get("total_completion_tokens"),
                    "nodes": meta.get("nodes"),
                },
                error_message=error_message,
                state_snapshot=snapshot,
                user_id=state["user_id"],
                correlation_id=state.get("correlation_id"),
                audit_action=audit_action,
            )
        except Exception as exc:
            return {
                **updates,
                **append_error(
                    "log_interaction",
                    "PERSISTENCE_ERROR",
                    str(exc),
                    fatal=True,
                ),
            }

        return updates

    return catch_node("log_interaction", log_interaction_node)
