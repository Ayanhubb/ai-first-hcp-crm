"""Preprocess / validate entry node."""

from __future__ import annotations

from typing import Any

from ..state.interaction_state import InteractionAssistState, append_error
from ._common import NodeContext, catch_node


MAX_NOTES_LEN = 20000
MIN_NOTES_LEN_ASSIST = 1  # API enforces min; graph still guards empty


def make_preprocess_node(ctx: NodeContext):
    """Trim notes, apply history limit, and validate mode prerequisites."""

    def preprocess(state: InteractionAssistState) -> dict[str, Any]:
        mode = state.get("mode")
        notes = (state.get("notes") or "").strip()
        updates: dict[str, Any] = {
            "notes": notes[:MAX_NOTES_LEN],
            "status": "running",
            "history_limit": state.get("history_limit")
            or ctx.llm.config.ai_history_limit,
        }

        if mode in {"assist", "edit"} and len(notes) < MIN_NOTES_LEN_ASSIST:
            return {
                **updates,
                **append_error(
                    "preprocess",
                    "EMPTY_NOTES",
                    "Notes are required for this mode",
                    fatal=True,
                ),
            }

        if mode == "edit" and not (state.get("edit_instruction") or "").strip():
            return {
                **updates,
                **append_error(
                    "preprocess",
                    "MISSING_EDIT_INSTRUCTION",
                    "edit_instruction is required in edit mode",
                    fatal=True,
                ),
            }

        if mode == "assist" and not state.get("hcp_id") and not (state.get("hcp_query") or "").strip():
            return {
                **updates,
                **append_error(
                    "preprocess",
                    "HCP_UNRESOLVED",
                    "hcp_id or hcp_query is required for assist",
                    fatal=True,
                ),
            }

        return updates

    return catch_node("preprocess", preprocess)
