"""extract_medical_topics node."""

from __future__ import annotations

from typing import Any

from ..prompts.topics import build_topics_messages
from ..engine.structured import invoke_structured, meta_update
from ..state.interaction_state import InteractionAssistState, append_error
from ..state.schemas import TopicsOutput
from ._common import NodeContext, catch_node, require_notes


def make_extract_medical_topics_node(ctx: NodeContext):
    def extract_medical_topics(state: InteractionAssistState) -> dict[str, Any]:
        notes = require_notes(state)
        if not notes:
            return {"medical_topics": []}

        messages = build_topics_messages(notes=notes, summary=state.get("summary"))
        try:
            parsed, usage, raw = invoke_structured(
                ctx.llm,
                node="extract_medical_topics",
                schema=TopicsOutput,
                messages=messages,
                temperature=ctx.llm.config.extraction_temperature,
                max_tokens=ctx.llm.config.max_tokens_extraction,
            )
        except Exception as exc:
            return append_error(
                "extract_medical_topics",
                "TOPICS_FAILED",
                str(exc),
                fatal=False,
            )

        return {
            "medical_topics": parsed.medical_topics,
            **meta_update("extract_medical_topics", usage, model_name=ctx.llm.model_name),
            "raw_llm_fragments": {"extract_medical_topics": raw[:2000]},
        }

    return catch_node("extract_medical_topics", extract_medical_topics)
