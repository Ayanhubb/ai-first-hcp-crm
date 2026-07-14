"""History summary prompt templates (v1)."""

from __future__ import annotations

from typing import Any

from .system import SYSTEM_CRM_ASSIST

PROMPT_VERSION = "v1"

HISTORY_SUMMARY_INSTRUCTIONS = """Condense prior HCP visit briefs into a short timeline summary for MR context.
- 2–5 sentences
- Chronological themes only; no invention
- Return JSON: {{"history_summary": "..."}}
"""


def build_history_summary_messages(*, history: list[dict[str, Any]]) -> list[dict[str, str]]:
    lines: list[str] = []
    for item in history:
        visit = item.get("visit_at") or "?"
        sent = item.get("sentiment") or ""
        text = item.get("summary") or item.get("notes_excerpt") or ""
        channel = item.get("channel") or ""
        lines.append(f"- {visit} [{channel}] ({sent}): {text}")
    body = "\n".join(lines) if lines else "(no prior interactions)"
    user = "\n".join(
        [
            HISTORY_SUMMARY_INSTRUCTIONS,
            "",
            "Prior interactions (newest first):",
            body,
        ]
    )
    return [
        {"role": "system", "content": SYSTEM_CRM_ASSIST},
        {"role": "user", "content": user},
    ]
