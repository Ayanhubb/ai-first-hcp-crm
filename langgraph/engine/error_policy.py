"""Error classification and node failure policies (design §14–§15)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .exceptions import (
    GraphError,
    LLMError,
    LLMFatalError,
    LLMTransientError,
    LLMValidationError,
    ToolError,
)


ErrorClass = Literal[
    "fatal",
    "non_fatal",
    "transient",
    "validation",
]


@dataclass(frozen=True, slots=True)
class ClassifiedError:
    classification: ErrorClass
    code: str
    message: str
    fatal: bool


def classify_exception(exc: BaseException, *, node: str) -> ClassifiedError:
    """Map an exception to the design error policy."""
    if isinstance(exc, LLMValidationError):
        return ClassifiedError("validation", exc.code, exc.message, fatal=False)
    if isinstance(exc, LLMTransientError):
        return ClassifiedError("transient", exc.code, exc.message, fatal=False)
    if isinstance(exc, LLMFatalError):
        return ClassifiedError("fatal", exc.code, exc.message, fatal=True)
    if isinstance(exc, LLMError):
        return ClassifiedError("non_fatal", exc.code, exc.message, fatal=exc.fatal)
    if isinstance(exc, ToolError):
        if exc.transient:
            return ClassifiedError("transient", exc.code, exc.message, fatal=False)
        return ClassifiedError(
            "fatal" if exc.fatal else "non_fatal",
            exc.code,
            exc.message,
            fatal=exc.fatal,
        )
    if isinstance(exc, GraphError):
        return ClassifiedError(
            "fatal" if exc.fatal else "non_fatal",
            exc.code,
            exc.message,
            fatal=exc.fatal,
        )

    # Heuristics for wrapped provider errors
    msg = str(exc) or type(exc).__name__
    lower = msg.lower()
    if "timeout" in lower:
        return ClassifiedError("transient", "LLM_TIMEOUT", msg, fatal=False)
    if "401" in lower or "invalid api key" in lower or "authentication" in lower:
        return ClassifiedError("fatal", "LLM_AUTH", msg, fatal=True)
    if any(x in lower for x in ("429", "rate limit", "503", "502", "overloaded")):
        return ClassifiedError("transient", "LLM_TRANSIENT", msg, fatal=False)

    return ClassifiedError("fatal", "UNEXPECTED", f"{node}: {msg}", fatal=True)


# Nodes where LLM failure is non-fatal (continue with partial status)
NON_FATAL_LLM_NODES = frozenset(
    {
        "generate_summary",
        "sentiment_analysis",
        "extract_products",
        "extract_medical_topics",
        "generate_followup",
        "edit_interaction",
        "retrieve_history",  # history_summary LLM portion only
    }
)

# Nodes where failure fails the whole run
FATAL_NODES = frozenset(
    {
        "search_hcp",
        "preprocess",
    }
)


def node_error_is_fatal(node: str, classified: ClassifiedError) -> bool:
    """Apply design rules for fatal vs partial continuation."""
    if classified.fatal:
        return True
    if node in FATAL_NODES:
        return True
    if node == "retrieve_history" and classified.code.startswith("TOOL"):
        return True
    if node == "extract_products" and classified.code in {"CATALOG_DB_ERROR"}:
        return True
    if classified.classification == "transient" and node in NON_FATAL_LLM_NODES:
        return False
    if node in NON_FATAL_LLM_NODES:
        return False
    return classified.fatal


def error_state_update(node: str, exc: BaseException) -> dict[str, Any]:
    """Build a state patch for a captured node exception."""
    classified = classify_exception(exc, node=node)
    fatal = node_error_is_fatal(node, classified)
    update: dict[str, Any] = {
        "errors": [
            {
                "node": node,
                "code": classified.code,
                "message": classified.message,
                "fatal": fatal,
            }
        ]
    }
    if fatal:
        update["fatal"] = True
        update["status"] = "failed"
    return update


def safe_error_message(exc: BaseException) -> str:
    """Return a user-safe error message (no secrets / stack internals)."""
    if isinstance(exc, GraphError):
        return exc.message
    name = type(exc).__name__
    if name in {"APIConnectionError", "APITimeoutError", "RateLimitError", "APIStatusError"}:
        return f"AI provider error ({name})"
    return "An unexpected AI processing error occurred"
