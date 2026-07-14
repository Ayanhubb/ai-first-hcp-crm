"""Product extraction prompt templates (v1)."""

from __future__ import annotations

from .system import SYSTEM_CRM_ASSIST

PROMPT_VERSION = "v1"

PRODUCTS_INSTRUCTIONS = """Extract pharmaceutical product / brand / SKU names discussed in the notes.
- List candidate names only (no UUIDs, no invented catalog codes)
- Omit vague class-only mentions unless a specific product is named
- Return JSON: {{"candidates": ["Name1", "Name2"]}}
- If none, return {{"candidates": []}}

Few-shot:
Notes: "Discussed AtorvaCare 10mg adherence and titration."
Output: {{"candidates": ["AtorvaCare 10mg"]}}
"""


def build_products_messages(*, notes: str, catalog_hint: list[str] | None = None) -> list[dict[str, str]]:
    hint = ""
    if catalog_hint:
        hint = "Known catalog names (prefer matching these phrasing):\n- " + "\n- ".join(catalog_hint[:40])
    user = "\n".join(
        [
            PRODUCTS_INSTRUCTIONS,
            "",
            hint,
            "",
            "Notes:",
            notes,
        ]
    )
    return [
        {"role": "system", "content": SYSTEM_CRM_ASSIST},
        {"role": "user", "content": user},
    ]
