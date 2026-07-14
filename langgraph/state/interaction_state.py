"""Typed shared state for the interaction assist graph."""

from __future__ import annotations

from typing import Annotated, Any, Literal, NotRequired, Required, TypedDict
from uuid import UUID, uuid4

from .schemas import (
    FollowUpDraft,
    GraphMode,
    HCPProfile,
    InteractionBrief,
    ModelMeta,
    NodeError,
    ProductMatch,
    RunStatus,
)


def _merge_errors(
    left: list[dict[str, Any]] | None,
    right: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    return list(left or []) + list(right or [])


def _merge_model_meta(
    left: ModelMeta | dict[str, Any] | None,
    right: ModelMeta | dict[str, Any] | None,
) -> dict[str, Any]:
    base = left if isinstance(left, ModelMeta) else ModelMeta.model_validate(left or {})
    incoming = right if isinstance(right, ModelMeta) else ModelMeta.model_validate(right or {})
    if not incoming.nodes and incoming.model_name is None:
        return base.model_dump()
    merged = base.model_copy(deep=True)
    if incoming.model_name:
        merged.model_name = incoming.model_name
    for node_name, usage in incoming.nodes.items():
        merged.record(node_name, usage)
    return merged.model_dump()


def _merge_raw_fragments(
    left: dict[str, Any] | None,
    right: dict[str, Any] | None,
) -> dict[str, Any]:
    out = dict(left or {})
    out.update(right or {})
    return out


class InteractionAssistState(TypedDict, total=False):
    """Shared graph state. Nodes merge partial updates; they do not wipe unrelated fields."""

    correlation_id: Required[str]
    ai_run_id: Required[str]
    user_id: Required[str]
    mode: Required[Literal["assist", "edit", "history_only", "persist"]]

    hcp_id: str | None
    hcp_query: str | None
    hcp_profile: dict[str, Any] | None
    interaction_id: str | None

    notes: str
    edit_instruction: str | None
    include_history: bool
    history: list[dict[str, Any]]
    history_summary: str | None

    summary: str | None
    sentiment: Literal["positive", "neutral", "negative", "mixed"] | None
    sentiment_score: float | None
    products: list[dict[str, Any]]
    medical_topics: list[str]
    follow_ups: list[dict[str, Any]]

    regenerate_derived: bool

    errors: Annotated[list[dict[str, Any]], _merge_errors]
    status: Literal["running", "succeeded", "partial", "failed"]
    model_meta: Annotated[dict[str, Any], _merge_model_meta]
    raw_llm_fragments: Annotated[dict[str, Any], _merge_raw_fragments]

    fatal: NotRequired[bool]
    skip_enrichment: NotRequired[bool]
    history_limit: NotRequired[int]


def create_initial_state(
    *,
    user_id: str | UUID,
    mode: GraphMode | str,
    notes: str = "",
    ai_run_id: str | UUID | None = None,
    correlation_id: str | UUID | None = None,
    hcp_id: str | UUID | None = None,
    hcp_query: str | None = None,
    hcp_profile: HCPProfile | dict[str, Any] | None = None,
    interaction_id: str | UUID | None = None,
    edit_instruction: str | None = None,
    include_history: bool = True,
    history_limit: int = 10,
    regenerate_derived: bool = True,
    current_ai_fields: dict[str, Any] | None = None,
    model_name: str | None = None,
) -> InteractionAssistState:
    """Build the initial running state for a graph invocation."""
    mode_value = mode.value if isinstance(mode, GraphMode) else str(mode)
    fields = current_ai_fields or {}
    if isinstance(hcp_profile, HCPProfile):
        profile = hcp_profile.model_dump(mode="json")
    else:
        profile = hcp_profile

    state: InteractionAssistState = {
        "correlation_id": str(correlation_id or uuid4()),
        "ai_run_id": str(ai_run_id or uuid4()),
        "user_id": str(user_id),
        "mode": mode_value,  # type: ignore[typeddict-item]
        "hcp_id": str(hcp_id) if hcp_id else None,
        "hcp_query": hcp_query,
        "hcp_profile": profile,
        "interaction_id": str(interaction_id) if interaction_id else None,
        "notes": (notes or "").strip(),
        "edit_instruction": edit_instruction,
        "include_history": include_history,
        "history": [],
        "history_summary": fields.get("history_summary"),
        "summary": fields.get("summary"),
        "sentiment": fields.get("sentiment"),
        "sentiment_score": fields.get("sentiment_score"),
        "products": list(fields.get("products") or []),
        "medical_topics": list(fields.get("medical_topics") or []),
        "follow_ups": list(fields.get("follow_ups") or []),
        "regenerate_derived": regenerate_derived,
        "errors": [],
        "status": RunStatus.RUNNING.value,  # type: ignore[typeddict-item]
        "model_meta": ModelMeta(model_name=model_name).model_dump(),
        "raw_llm_fragments": {},
        "fatal": False,
        "skip_enrichment": False,
        "history_limit": history_limit,
    }
    return state


def append_error(
    node: str,
    code: str,
    message: str,
    *,
    fatal: bool = False,
) -> dict[str, Any]:
    """Return a partial state update that appends a NodeError."""
    err = NodeError(node=node, code=code, message=message, fatal=fatal)
    update: dict[str, Any] = {"errors": [err.model_dump()]}
    if fatal:
        update["fatal"] = True
        update["status"] = RunStatus.FAILED.value
    return update


def finalize_status(state: InteractionAssistState) -> Literal["succeeded", "partial", "failed"]:
    """Derive terminal status from errors / fatal flag."""
    if state.get("fatal") or state.get("status") == RunStatus.FAILED.value:
        return RunStatus.FAILED.value  # type: ignore[return-value]
    errors = state.get("errors") or []
    if any(e.get("fatal") for e in errors):
        return RunStatus.FAILED.value  # type: ignore[return-value]
    if errors:
        return RunStatus.PARTIAL.value  # type: ignore[return-value]
    return RunStatus.SUCCEEDED.value  # type: ignore[return-value]


def coerce_product_matches(raw: list[dict[str, Any]] | list[ProductMatch]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, ProductMatch):
            out.append(item.model_dump(mode="json"))
        else:
            out.append(ProductMatch.model_validate(item).model_dump(mode="json"))
    return out


def coerce_follow_ups(raw: list[dict[str, Any]] | list[FollowUpDraft]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, FollowUpDraft):
            out.append(item.model_dump(mode="json"))
        else:
            out.append(FollowUpDraft.model_validate(item).model_dump(mode="json"))
    return out


def coerce_history(raw: list[dict[str, Any]] | list[InteractionBrief]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, InteractionBrief):
            out.append(item.model_dump(mode="json"))
        else:
            out.append(InteractionBrief.model_validate(item).model_dump(mode="json"))
    return out
