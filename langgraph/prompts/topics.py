"""Medical topics prompt templates (v1)."""

from __future__ import annotations

from .system import SYSTEM_CRM_ASSIST

PROMPT_VERSION = "v1"

TOPICS_INSTRUCTIONS = """Extract short medical / clinical topic phrases discussed in the visit.
- Prefer normalized lowercase clinical phrases (e.g. "dyslipidemia", "medication adherence")
- Deduplicate
- Max 15 topics
- Return JSON: {{"medical_topics": ["...", "..."]}}
"""


def build_topics_messages(*, notes: str, summary: str | None = None) -> list[dict[str, str]]:
    user = "\n".join(
        [
            TOPICS_INSTRUCTIONS,
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
