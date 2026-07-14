"""Follow-up suggestion prompt templates (v1)."""

from __future__ import annotations

from typing import Any

from .system import SYSTEM_CRM_ASSIST

PROMPT_VERSION = "v1"

FOLLOWUP_INSTRUCTIONS = """Suggest 1–3 actionable follow-up tasks for the Medical Representative.
Each item: title (required), description, priority (low|medium|high), due_in_days (integer).
Tasks must be grounded in the notes/enrichment — do not invent unrelated campaigns.
Return JSON: {{"follow_ups": [{{"title": "...", "description": "...", "priority": "medium", "due_in_days": 7}}]}}
"""


def build_followup_messages(
    *,
    notes: str,
    summary: str | None = None,
    sentiment: str | None = None,
    products: list[dict[str, Any]] | None = None,
    medical_topics: list[str] | None = None,
) -> list[dict[str, str]]:
    product_names = ", ".join(
        p.get("name") or "" for p in (products or []) if p.get("name")
    ) or "(none)"
    topics = ", ".join(medical_topics or []) or "(none)"
    user = "\n".join(
        [
            FOLLOWUP_INSTRUCTIONS,
            "",
            f"Sentiment: {sentiment or '(unknown)'}",
            f"Products: {product_names}",
            f"Topics: {topics}",
            "",
            "Summary:",
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
