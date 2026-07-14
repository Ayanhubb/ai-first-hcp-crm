"""Edit notes prompt templates (v1)."""

from __future__ import annotations

from typing import Any

from .system import SYSTEM_CRM_ASSIST

PROMPT_VERSION = "v1"

EDIT_INSTRUCTIONS = """Rewrite the MR notes according to the edit instruction.
- Preserve clinical meaning; do not fabricate visit content
- Apply only the requested changes
- Optionally refresh the summary if notes materially changed
- Set regenerate_derived=true if summary/sentiment/products/topics/follow-ups should be recomputed
- Return JSON: {{"notes": "...", "summary": "..." or null, "regenerate_derived": true}}
"""


def build_edit_messages(
    *,
    notes: str,
    edit_instruction: str,
    current_ai_fields: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    fields = current_ai_fields or {}
    user = "\n".join(
        [
            EDIT_INSTRUCTIONS,
            "",
            "Edit instruction:",
            edit_instruction,
            "",
            "Current notes:",
            notes,
            "",
            "Current summary:",
            str(fields.get("summary") or "(none)"),
        ]
    )
    return [
        {"role": "system", "content": SYSTEM_CRM_ASSIST},
        {"role": "user", "content": user},
    ]
