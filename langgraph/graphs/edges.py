"""Edge catalog for the interaction assist graph.

Conditional predicates live in ``routing.py``. This module documents the static
and conditional edge map aligned with ``docs/langgraph_design.md`` §§6–7.
"""

from __future__ import annotations

from .routing import (
    route_after_edit,
    route_after_preprocess,
    route_after_retrieve_history,
    route_after_search_hcp,
    route_on_fatal_to_log,
)

# Static enrichment spine (assist + edit regenerate path)
ENRICHMENT_EDGES: list[tuple[str, str]] = [
    ("generate_summary", "sentiment_analysis"),
    ("sentiment_analysis", "extract_products"),
    ("extract_products", "extract_medical_topics"),
    ("extract_medical_topics", "generate_followup"),
    ("generate_followup", "log_interaction"),
]

# Always terminal
TERMINAL_EDGES: list[tuple[str, str]] = [
    ("log_interaction", "__end__"),
]

CONDITIONAL_EDGE_MAP = {
    "preprocess": route_after_preprocess,
    "search_hcp": route_after_search_hcp,
    "retrieve_history": route_after_retrieve_history,
    "edit_interaction": route_after_edit,
}

__all__ = [
    "ENRICHMENT_EDGES",
    "TERMINAL_EDGES",
    "CONDITIONAL_EDGE_MAP",
    "route_after_preprocess",
    "route_after_search_hcp",
    "route_after_retrieve_history",
    "route_after_edit",
    "route_on_fatal_to_log",
]
