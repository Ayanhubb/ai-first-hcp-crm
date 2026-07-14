"""Repair prompt for invalid structured LLM output."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from .system import SYSTEM_CRM_ASSIST


def build_repair_messages(
    *,
    schema: type[BaseModel],
    original_messages: list[dict[str, str]] | list[Any],
    error: str,
    raw: str | None = None,
) -> list[dict[str, str]]:
    """One-shot repair pass: ask the model to fix JSON to match the schema."""
    schema_json = json.dumps(schema.model_json_schema(), indent=2)
    # Keep prior user intent if available
    prior_user = ""
    for msg in reversed(list(original_messages)):
        if isinstance(msg, dict) and msg.get("role") == "user":
            prior_user = str(msg.get("content") or "")
            break
        content = getattr(msg, "content", None)
        if content and getattr(msg, "type", None) == "human":
            prior_user = str(content)
            break

    repair_user = "\n".join(
        [
            "Your previous answer was not valid for the required JSON schema.",
            f"Validation error: {error}",
            "",
            "Required JSON schema:",
            schema_json,
            "",
            "Previous raw output:",
            raw or "(empty)",
            "",
            "Original task:",
            prior_user[:4000] or "(unavailable)",
            "",
            "Return ONLY a corrected JSON object matching the schema.",
        ]
    )
    return [
        {"role": "system", "content": SYSTEM_CRM_ASSIST},
        {"role": "user", "content": repair_user},
    ]
