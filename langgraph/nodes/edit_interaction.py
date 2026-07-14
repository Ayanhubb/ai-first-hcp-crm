"""edit_interaction node — guided rewrite of notes/summary."""

from __future__ import annotations

from typing import Any

from ..prompts.edit_notes import build_edit_messages
from ..engine.structured import invoke_structured, meta_update
from ..state.interaction_state import InteractionAssistState, append_error
from ..state.schemas import EditOutput
from ._common import NodeContext, catch_node, require_notes


def make_edit_interaction_node(ctx: NodeContext):
    def edit_interaction(state: InteractionAssistState) -> dict[str, Any]:
        notes = require_notes(state)
        instruction = (state.get("edit_instruction") or "").strip()
        if not instruction:
            return append_error(
                "edit_interaction",
                "MISSING_EDIT_INSTRUCTION",
                "edit_instruction is required",
                fatal=True,
            )

        current_fields = {
            "summary": state.get("summary"),
            "sentiment": state.get("sentiment"),
            "sentiment_score": state.get("sentiment_score"),
            "medical_topics": state.get("medical_topics"),
            "products": state.get("products"),
            "follow_ups": state.get("follow_ups"),
        }
        messages = build_edit_messages(
            notes=notes,
            edit_instruction=instruction,
            current_ai_fields=current_fields,
        )
        try:
            parsed, usage, raw = invoke_structured(
                ctx.llm,
                node="edit_interaction",
                schema=EditOutput,
                messages=messages,
                temperature=ctx.llm.config.edit_temperature,
                max_tokens=ctx.llm.config.max_tokens_edit,
            )
        except Exception as exc:
            return append_error(
                "edit_interaction",
                "EDIT_FAILED",
                str(exc),
                fatal=False,
            )

        regenerate = bool(parsed.regenerate_derived)
        if state.get("regenerate_derived") is False:
            regenerate = False

        updates: dict[str, Any] = {
            "notes": parsed.notes.strip(),
            "regenerate_derived": regenerate,
            **meta_update("edit_interaction", usage, model_name=ctx.llm.model_name),
            "raw_llm_fragments": {"edit_interaction": raw[:2000]},
        }
        if parsed.summary:
            updates["summary"] = parsed.summary.strip()
        return updates

    return catch_node("edit_interaction", edit_interaction)
