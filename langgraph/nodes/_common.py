"""Shared node helpers."""

from __future__ import annotations

from typing import Any

from ..engine.error_policy import error_state_update
from ..engine.llm_factory import LLMService
from ..state.interaction_state import InteractionAssistState
from ..tools.base import ToolBundle


class NodeContext:
    """Dependency bag closed over by node callables."""

    def __init__(
        self,
        *,
        llm: LLMService,
        tools: ToolBundle,
    ) -> None:
        self.llm = llm
        self.tools = tools


def require_notes(state: InteractionAssistState) -> str:
    return (state.get("notes") or "").strip()


def merge_updates(*parts: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []
    for part in parts:
        if not part:
            continue
        part_errors = part.get("errors")
        if part_errors:
            errors.extend(part_errors)
            part = {k: v for k, v in part.items() if k != "errors"}
        out.update(part)
    if errors:
        out["errors"] = errors
    return out


def catch_node(node_name: str, fn):
    """Decorator-style wrapper used by node factories."""

    def _wrapped(state: InteractionAssistState) -> dict[str, Any]:
        try:
            return fn(state)
        except Exception as exc:
            return error_state_update(node_name, exc)

    _wrapped.__name__ = node_name
    return _wrapped
