"""AI-First HCP CRM — LangGraph interaction assist package.

Public surface used by backend ``AiAssistService``:

- ``compile_interaction_assist_graph`` / ``run_assist``
- ``create_initial_state`` / ``InteractionAssistState``
- ``ToolBundle`` ports for HCP / history / catalog / persistence
- ``GraphConfig`` / ``LLMService`` (Groq via langchain-groq)

Durable CRM writes (interactions / products / follow-ups) are **not** performed
here. The graph finalizes ``ai_runs`` only after enrichment.

Note: this package shares the top-level name ``langgraph`` with the official
library. A shadow finder routes ``langgraph.graph`` / ``langgraph.types`` /
``langgraph.runtime`` / etc. to site-packages. CRM runtime helpers live under
``engine/`` (not ``runtime/``) to avoid that collision.
"""

from __future__ import annotations

from ._shadow_fix import install_shadow_finder

install_shadow_finder()

from .graphs.interaction_assist_graph import (  # noqa: E402
    GRAPH_NAME,
    build_interaction_assist_graph,
    compile_interaction_assist_graph,
    invoke_graph,
    run_assist,
)
from .engine.config import GraphConfig  # noqa: E402
from .engine.llm_factory import LLMService, create_llm_service  # noqa: E402
from .state.interaction_state import (  # noqa: E402
    InteractionAssistState,
    create_initial_state,
    finalize_status,
)
from .state.schemas import GraphMode, RunStatus  # noqa: E402
from .tools.base import ToolBundle  # noqa: E402

__all__ = [
    "GRAPH_NAME",
    "GraphConfig",
    "GraphMode",
    "InteractionAssistState",
    "LLMService",
    "RunStatus",
    "ToolBundle",
    "build_interaction_assist_graph",
    "compile_interaction_assist_graph",
    "create_initial_state",
    "create_llm_service",
    "finalize_status",
    "invoke_graph",
    "run_assist",
]

__version__ = "1.0.0"
