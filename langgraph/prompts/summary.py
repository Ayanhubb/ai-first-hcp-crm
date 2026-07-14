"""Summary prompt templates (v1)."""

from __future__ import annotations

from typing import Any

from .system import SYSTEM_CRM_ASSIST

PROMPT_VERSION = "v1"

SUMMARY_INSTRUCTIONS = """Produce a concise factual summary of the MR–HCP interaction notes.
- 1–3 sentences
- No invented facts
- Include discussed therapies only if mentioned
- Return JSON: {{"summary": "..."}}
"""


def build_summary_messages(
    *,
    notes: str,
    history_summary: str | None = None,
    hcp_profile: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    hcp_bits: list[str] = []
    if hcp_profile:
        name = hcp_profile.get("full_name") or " ".join(
            filter(None, [hcp_profile.get("first_name"), hcp_profile.get("last_name")])
        )
        if name:
            hcp_bits.append(f"HCP: {name}")
        if hcp_profile.get("specialty"):
            hcp_bits.append(f"Specialty: {hcp_profile['specialty']}")
        if hcp_profile.get("institution"):
            hcp_bits.append(f"Institution: {hcp_profile['institution']}")

    user_parts = [
        SUMMARY_INSTRUCTIONS,
        "",
        "HCP context:",
        "\n".join(hcp_bits) if hcp_bits else "(none)",
        "",
        "Prior history summary:",
        history_summary or "(none)",
        "",
        "Current visit notes:",
        notes,
    ]
    return [
        {"role": "system", "content": SYSTEM_CRM_ASSIST},
        {"role": "user", "content": "\n".join(user_parts)},
    ]
