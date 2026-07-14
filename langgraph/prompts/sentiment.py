"""Sentiment analysis prompt templates (v1)."""

from __future__ import annotations

from .system import SYSTEM_CRM_ASSIST

PROMPT_VERSION = "v1"

SENTIMENT_INSTRUCTIONS = """Classify the overall interaction sentiment.
Allowed sentiment values ONLY: positive | neutral | negative | mixed
sentiment_score must be a float from 0.0 to 1.0 (confidence).
Return JSON: {{"sentiment": "...", "sentiment_score": 0.0}}
"""


def build_sentiment_messages(*, notes: str, summary: str | None = None) -> list[dict[str, str]]:
    user = "\n".join(
        [
            SENTIMENT_INSTRUCTIONS,
            "",
            "Summary (optional):",
            summary or "(none)",
            "",
            "Notes:",
            notes,
        ]
    )
    return [
        {"role": "system", "content": SYSTEM_CRM_ASSIST},
        {"role": "user", "content": user},
    ]
