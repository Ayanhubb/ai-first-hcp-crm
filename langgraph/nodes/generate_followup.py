"""generate_followup node."""

from __future__ import annotations

from typing import Any

from ..prompts.followup import build_followup_messages
from ..engine.structured import invoke_structured, meta_update
from ..state.interaction_state import InteractionAssistState, append_error, coerce_follow_ups
from ..state.schemas import FollowUpsOutput
from ._common import NodeContext, catch_node, require_notes


def make_generate_followup_node(ctx: NodeContext):
    def generate_followup(state: InteractionAssistState) -> dict[str, Any]:
        notes = require_notes(state)
        if not notes:
            return {"follow_ups": []}

        messages = build_followup_messages(
            notes=notes,
            summary=state.get("summary"),
            sentiment=state.get("sentiment"),
            products=state.get("products"),
            medical_topics=state.get("medical_topics"),
        )
        try:
            parsed, usage, raw = invoke_structured(
                ctx.llm,
                node="generate_followup",
                schema=FollowUpsOutput,
                messages=messages,
                temperature=ctx.llm.config.summary_temperature,
                max_tokens=ctx.llm.config.max_tokens_extraction,
            )
        except Exception as exc:
            return append_error(
                "generate_followup",
                "FOLLOWUP_FAILED",
                str(exc),
                fatal=False,
            )

        return {
            "follow_ups": coerce_follow_ups(parsed.follow_ups),
            **meta_update("generate_followup", usage, model_name=ctx.llm.model_name),
            "raw_llm_fragments": {"generate_followup": raw[:2000]},
        }

    return catch_node("generate_followup", generate_followup)
