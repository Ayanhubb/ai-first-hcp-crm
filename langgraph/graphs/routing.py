"""Conditional routing / edge predicates for the interaction assist graph."""

from __future__ import annotations

from typing import Literal

from ..state.interaction_state import InteractionAssistState

RouteAfterPreprocess = Literal[
    "search_hcp",
    "retrieve_history",
    "edit_interaction",
    "log_interaction",
    "__end__",
]

RouteAfterSearch = Literal["retrieve_history", "log_interaction"]

RouteAfterHistory = Literal["generate_summary", "log_interaction"]

RouteAfterEdit = Literal["generate_summary", "log_interaction"]


def route_after_preprocess(state: InteractionAssistState) -> RouteAfterPreprocess:
    """Mode-based entry routing after validation."""
    if state.get("fatal") or state.get("status") == "failed":
        return "log_interaction"

    mode = state.get("mode")
    if mode == "persist":
        return "log_interaction"
    if mode == "edit":
        return "edit_interaction"
    if mode == "history_only":
        return "retrieve_history"
    # assist
    if state.get("hcp_id"):
        return "retrieve_history"
    return "search_hcp"


def route_after_search_hcp(state: InteractionAssistState) -> RouteAfterSearch:
    if state.get("fatal") or state.get("status") == "failed":
        return "log_interaction"
    return "retrieve_history"


def route_after_retrieve_history(state: InteractionAssistState) -> RouteAfterHistory:
    if state.get("fatal") or state.get("status") == "failed":
        return "log_interaction"
    if state.get("mode") == "history_only":
        return "log_interaction"
    return "generate_summary"


def route_after_edit(state: InteractionAssistState) -> RouteAfterEdit:
    if state.get("fatal") or state.get("status") == "failed":
        return "log_interaction"
    if state.get("regenerate_derived"):
        return "generate_summary"
    return "log_interaction"


def route_on_fatal_to_log(state: InteractionAssistState) -> Literal["continue", "log_interaction"]:
    """Optional guard used between enrichment nodes."""
    if state.get("fatal") or state.get("status") == "failed":
        return "log_interaction"
    return "continue"
