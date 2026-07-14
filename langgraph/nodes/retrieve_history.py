"""retrieve_history node — load prior interactions and optional history summary."""

from __future__ import annotations

from typing import Any

from ..prompts.history_summary import build_history_summary_messages
from ..engine.structured import invoke_structured, meta_update
from ..state.interaction_state import InteractionAssistState, append_error, coerce_history
from ..state.schemas import HistorySummaryOutput
from ..tools.history_tool import retrieve_interaction_history
from ._common import NodeContext, catch_node, merge_updates


def make_retrieve_history_node(ctx: NodeContext):
    def retrieve_history(state: InteractionAssistState) -> dict[str, Any]:
        if state.get("include_history") is False:
            return {"history": [], "history_summary": state.get("history_summary")}

        hcp_id = state.get("hcp_id")
        if not hcp_id:
            # history_only / assist without HCP is fatal for history path
            if state.get("mode") in {"history_only", "assist"}:
                return append_error(
                    "retrieve_history",
                    "HCP_REQUIRED",
                    "hcp_id is required to retrieve history",
                    fatal=True,
                )
            return {"history": []}

        port = ctx.tools.history
        if port is None:
            return append_error(
                "retrieve_history",
                "TOOL_NOT_CONFIGURED",
                "History port is not configured",
                fatal=True,
            )

        limit = int(state.get("history_limit") or ctx.llm.config.ai_history_limit)
        briefs = retrieve_interaction_history(port, hcp_id=hcp_id, limit=limit)
        history = coerce_history(briefs)
        updates: dict[str, Any] = {"history": history}

        # Produce history_summary for history_only, or when assisting with history
        need_summary = state.get("mode") == "history_only" or (
            state.get("mode") == "assist" and bool(history)
        )
        if need_summary and history:
            try:
                messages = build_history_summary_messages(history=history)
                parsed, usage, raw = invoke_structured(
                    ctx.llm,
                    node="retrieve_history",
                    schema=HistorySummaryOutput,
                    messages=messages,
                    temperature=ctx.llm.config.summary_temperature,
                    max_tokens=ctx.llm.config.max_tokens_summary,
                )
                updates["history_summary"] = parsed.history_summary
                updates.update(meta_update("retrieve_history", usage, model_name=ctx.llm.model_name))
                updates["raw_llm_fragments"] = {"retrieve_history": raw[:2000]}
            except Exception as exc:
                # Templated fallback (non-fatal for assist; useful for history_only too)
                fallback = _template_history_summary(history)
                updates["history_summary"] = fallback
                updates = merge_updates(
                    updates,
                    append_error(
                        "retrieve_history",
                        "HISTORY_SUMMARY_LLM",
                        f"Falling back to templated history summary: {exc}",
                        fatal=False,
                    ),
                )
        elif need_summary and not history:
            updates["history_summary"] = "No prior interactions on record."

        return updates

    return catch_node("retrieve_history", retrieve_history)


def _template_history_summary(history: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for item in history[:5]:
        visit = item.get("visit_at") or "unknown date"
        text = item.get("summary") or item.get("notes_excerpt") or ""
        parts.append(f"{visit}: {text}".strip())
    return " | ".join(parts) if parts else "No prior interactions on record."
