"""Helpers to import symbols from the installed LangGraph library."""

from __future__ import annotations

from typing import Any


def import_state_graph():
    """Return ``(StateGraph, START, END)`` from the installed library."""
    from langgraph.graph import END, START, StateGraph

    return StateGraph, START, END


def import_retry_policy():
    """Return RetryPolicy class if available, else None."""
    try:
        from langgraph.types import RetryPolicy

        return RetryPolicy
    except ImportError:
        return None


def get_langgraph_attr(module_path: str, attr: str) -> Any:
    """Return an attribute from an installed langgraph submodule path."""
    import importlib

    mod = importlib.import_module(f"langgraph.{module_path}")
    return getattr(mod, attr)
