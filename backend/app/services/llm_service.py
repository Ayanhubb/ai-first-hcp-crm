"""LLM provider façade used by AiAssistService / LangGraph.

The concrete Groq adapter lives in the sibling ``langgraph`` package
(``langgraph.engine.llm_factory``). This module re-exports it so backend
imports follow ``backend_design.md`` (``services.llm_service``).
"""

from __future__ import annotations

from langgraph import GraphConfig, LLMService, create_llm_service

__all__ = [
    "GraphConfig",
    "LLMService",
    "create_llm_service",
]
