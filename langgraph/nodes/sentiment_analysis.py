"""sentiment_analysis node."""

from __future__ import annotations

from typing import Any

from ..prompts.sentiment import build_sentiment_messages
from ..engine.structured import invoke_structured, meta_update
from ..state.interaction_state import InteractionAssistState, append_error
from ..state.schemas import SentimentOutput
from ._common import NodeContext, catch_node, require_notes


def make_sentiment_analysis_node(ctx: NodeContext):
    def sentiment_analysis(state: InteractionAssistState) -> dict[str, Any]:
        notes = require_notes(state)
        if not notes:
            return append_error(
                "sentiment_analysis",
                "EMPTY_NOTES",
                "Cannot analyze sentiment for empty notes",
                fatal=False,
            )

        messages = build_sentiment_messages(notes=notes, summary=state.get("summary"))
        try:
            parsed, usage, raw = invoke_structured(
                ctx.llm,
                node="sentiment_analysis",
                schema=SentimentOutput,
                messages=messages,
                temperature=ctx.llm.config.extraction_temperature,
                max_tokens=ctx.llm.config.max_tokens_extraction,
            )
        except Exception as exc:
            return append_error(
                "sentiment_analysis",
                "SENTIMENT_FAILED",
                str(exc),
                fatal=False,
            )

        return {
            "sentiment": parsed.sentiment.value,
            "sentiment_score": float(parsed.sentiment_score),
            **meta_update("sentiment_analysis", usage, model_name=ctx.llm.model_name),
            "raw_llm_fragments": {"sentiment_analysis": raw[:2000]},
        }

    return catch_node("sentiment_analysis", sentiment_analysis)
