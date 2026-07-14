"""search_hcp node — resolve or verify HCP context."""

from __future__ import annotations

from typing import Any

from ..state.interaction_state import InteractionAssistState, append_error
from ..tools.hcp_search_tool import get_hcp_by_id, hcp_profile_to_dict, search_hcp
from ._common import NodeContext, catch_node


def make_search_hcp_node(ctx: NodeContext):
    def search_hcp_node(state: InteractionAssistState) -> dict[str, Any]:
        port = ctx.tools.hcp
        if port is None:
            return append_error(
                "search_hcp",
                "TOOL_NOT_CONFIGURED",
                "HCP search port is not configured",
                fatal=True,
            )

        hcp_id = state.get("hcp_id")
        if hcp_id:
            profile = get_hcp_by_id(port, hcp_id)
            if profile is None:
                return append_error(
                    "search_hcp",
                    "HCP_NOT_FOUND",
                    f"HCP not found for id={hcp_id}",
                    fatal=True,
                )
            return {
                "hcp_id": str(profile.id),
                "hcp_profile": hcp_profile_to_dict(profile),
            }

        query = (state.get("hcp_query") or "").strip()
        if not query:
            return append_error(
                "search_hcp",
                "HCP_UNRESOLVED",
                "No hcp_id or hcp_query provided",
                fatal=True,
            )

        candidates = search_hcp(port, query=query, limit=5)
        if not candidates:
            return append_error(
                "search_hcp",
                "HCP_NOT_FOUND",
                f"No HCP matched query={query!r}",
                fatal=True,
            )

        top = candidates[0]
        profile = get_hcp_by_id(port, top.id) or top
        data = (
            hcp_profile_to_dict(profile)
            if hasattr(profile, "model_dump")
            else top.model_dump(mode="json")
        )
        return {
            "hcp_id": str(top.id),
            "hcp_profile": data,
        }

    return catch_node("search_hcp", search_hcp_node)
