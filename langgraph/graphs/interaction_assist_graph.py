"""Interaction assist graph builder — nodes, edges, Groq runtime wiring."""

from __future__ import annotations

from typing import Any

from ..nodes import (
    NodeContext,
    make_edit_interaction_node,
    make_extract_medical_topics_node,
    make_extract_products_node,
    make_generate_followup_node,
    make_generate_summary_node,
    make_log_interaction_node,
    make_preprocess_node,
    make_retrieve_history_node,
    make_search_hcp_node,
    make_sentiment_analysis_node,
)
from ..engine.config import GraphConfig
from ..engine.llm_factory import LLMService, create_llm_service
from ..engine.lg_imports import get_langgraph_attr, import_retry_policy, import_state_graph
from ..engine.retry import build_node_retry_policy
from ..state.interaction_state import InteractionAssistState, create_initial_state
from ..tools.base import ToolBundle
from .routing import (
    route_after_edit,
    route_after_preprocess,
    route_after_retrieve_history,
    route_after_search_hcp,
)

GRAPH_NAME = "interaction_assist"


def build_interaction_assist_graph(
    *,
    llm: LLMService | None = None,
    tools: ToolBundle | None = None,
    config: GraphConfig | None = None,
):
    """Construct an uncompiled StateGraph for interaction assist.

    Modes:
    - ``assist``: search → history → summary → sentiment → products → topics → followup → log
    - ``history_only``: history → log
    - ``edit``: edit → (optional enrichment) → log
    - ``persist``: log only
    """
    StateGraph, START, END = import_state_graph()
    cfg = config or (llm.config if llm else GraphConfig.from_env())
    llm_service = llm or create_llm_service(cfg)
    tool_bundle = tools or ToolBundle()
    ctx = NodeContext(llm=llm_service, tools=tool_bundle)

    graph = StateGraph(InteractionAssistState)

    # Node-level retry for transient LLM failures (max 2 retries → 3 attempts)
    llm_retry = build_node_retry_policy(max_attempts=cfg.llm_max_retries + 1)

    def _add(name: str, factory, *, use_retry: bool = False) -> None:
        node_fn = factory(ctx)
        if use_retry and llm_retry is not None:
            try:
                graph.add_node(name, node_fn, retry=llm_retry)
                return
            except TypeError:
                pass
        graph.add_node(name, node_fn)

    _add("preprocess", make_preprocess_node)
    _add("search_hcp", make_search_hcp_node)
    _add("retrieve_history", make_retrieve_history_node, use_retry=True)
    _add("generate_summary", make_generate_summary_node, use_retry=True)
    _add("sentiment_analysis", make_sentiment_analysis_node, use_retry=True)
    _add("extract_products", make_extract_products_node, use_retry=True)
    _add("extract_medical_topics", make_extract_medical_topics_node, use_retry=True)
    _add("generate_followup", make_generate_followup_node, use_retry=True)
    _add("edit_interaction", make_edit_interaction_node, use_retry=True)
    _add("log_interaction", make_log_interaction_node)

    graph.add_edge(START, "preprocess")

    graph.add_conditional_edges(
        "preprocess",
        route_after_preprocess,
        {
            "search_hcp": "search_hcp",
            "retrieve_history": "retrieve_history",
            "edit_interaction": "edit_interaction",
            "log_interaction": "log_interaction",
            "__end__": END,
        },
    )

    graph.add_conditional_edges(
        "search_hcp",
        route_after_search_hcp,
        {
            "retrieve_history": "retrieve_history",
            "log_interaction": "log_interaction",
        },
    )

    graph.add_conditional_edges(
        "retrieve_history",
        route_after_retrieve_history,
        {
            "generate_summary": "generate_summary",
            "log_interaction": "log_interaction",
        },
    )

    # Enrichment spine (assist + edit regenerate)
    graph.add_edge("generate_summary", "sentiment_analysis")
    graph.add_edge("sentiment_analysis", "extract_products")
    graph.add_edge("extract_products", "extract_medical_topics")
    graph.add_edge("extract_medical_topics", "generate_followup")
    graph.add_edge("generate_followup", "log_interaction")

    graph.add_conditional_edges(
        "edit_interaction",
        route_after_edit,
        {
            "generate_summary": "generate_summary",
            "log_interaction": "log_interaction",
        },
    )

    graph.add_edge("log_interaction", END)
    return graph


def compile_interaction_assist_graph(
    *,
    llm: LLMService | None = None,
    tools: ToolBundle | None = None,
    config: GraphConfig | None = None,
    checkpointer: Any | None = None,
):
    """Build and compile the interaction assist graph."""
    graph = build_interaction_assist_graph(llm=llm, tools=tools, config=config)
    if checkpointer is not None:
        return graph.compile(checkpointer=checkpointer)
    return graph.compile()


def invoke_graph(
    compiled: Any,
    state: InteractionAssistState,
    *,
    config: dict[str, Any] | None = None,
) -> InteractionAssistState:
    """Invoke a compiled graph and return the terminal state."""
    result = compiled.invoke(state, config=config or {"configurable": {}})
    return result  # type: ignore[return-value]


def run_assist(
    *,
    user_id: str,
    notes: str,
    hcp_id: str | None = None,
    hcp_query: str | None = None,
    ai_run_id: str | None = None,
    correlation_id: str | None = None,
    interaction_id: str | None = None,
    include_history: bool = True,
    tools: ToolBundle | None = None,
    llm: LLMService | None = None,
    config: GraphConfig | None = None,
    mode: str = "assist",
    edit_instruction: str | None = None,
    regenerate_derived: bool = True,
    current_ai_fields: dict[str, Any] | None = None,
) -> InteractionAssistState:
    """Convenience entrypoint for AiAssistService."""
    cfg = config or GraphConfig.from_env()
    llm_service = llm or create_llm_service(cfg)
    compiled = compile_interaction_assist_graph(
        llm=llm_service,
        tools=tools,
        config=cfg,
    )
    initial = create_initial_state(
        user_id=user_id,
        mode=mode,
        notes=notes,
        ai_run_id=ai_run_id,
        correlation_id=correlation_id,
        hcp_id=hcp_id,
        hcp_query=hcp_query,
        interaction_id=interaction_id,
        include_history=include_history,
        history_limit=cfg.ai_history_limit,
        edit_instruction=edit_instruction,
        regenerate_derived=regenerate_derived,
        current_ai_fields=current_ai_fields,
        model_name=cfg.groq_model,
    )
    return invoke_graph(compiled, initial)


__all__ = [
    "GRAPH_NAME",
    "build_interaction_assist_graph",
    "compile_interaction_assist_graph",
    "invoke_graph",
    "run_assist",
    "create_initial_state",
    "get_langgraph_attr",
    "import_retry_policy",
]
