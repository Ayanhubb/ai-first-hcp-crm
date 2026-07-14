"""generate_summary node."""

from __future__ import annotations

from typing import Any

from ..prompts.summary import build_summary_messages
from ..engine.structured import invoke_structured, meta_update
from ..state.interaction_state import InteractionAssistState, append_error
from ..state.schemas import SummaryOutput
from ._common import NodeContext, catch_node, require_notes


def make_generate_summary_node(ctx: NodeContext):
    def generate_summary(state: InteractionAssistState) -> dict[str, Any]:
        notes = require_notes(state)
        if not notes:
            return append_error(
                "generate_summary",
                "EMPTY_NOTES",
                "Cannot summarize empty notes",
                fatal=False,
            )

        messages = build_summary_messages(
            notes=notes,
            history_summary=state.get("history_summary"),
            hcp_profile=state.get("hcp_profile"),
        )
        try:
            parsed, usage, raw = invoke_structured(
                ctx.llm,
                node="generate_summary",
                schema=SummaryOutput,
                messages=messages,
                temperature=ctx.llm.config.summary_temperature,
                max_tokens=ctx.llm.config.max_tokens_summary,
            )
        except Exception as exc:
            return append_error(
                "generate_summary",
                "SUMMARY_FAILED",
                str(exc),
                fatal=False,
            )

        return {
            "summary": parsed.summary.strip(),
            **meta_update("generate_summary", usage, model_name=ctx.llm.model_name),
            "raw_llm_fragments": {"generate_summary": raw[:2000]},
        }

    return catch_node("generate_summary", generate_summary)
