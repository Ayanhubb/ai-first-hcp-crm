"""CRM graph engine: Groq LLM factory, retry, and error policy.

Named ``engine`` (not ``runtime``) to avoid colliding with the official
library module ``langgraph.runtime``.
"""

from .config import GraphConfig
from .error_policy import classify_exception, error_state_update, safe_error_message
from .exceptions import (
    ConfigurationError,
    GraphError,
    LLMError,
    LLMFatalError,
    LLMTransientError,
    LLMValidationError,
    ToolError,
)
from .llm_factory import LLMService, create_llm_service
from .retry import RetrySettings, build_node_retry_policy, call_with_retry
from .structured import invoke_structured, meta_update

__all__ = [
    "GraphConfig",
    "classify_exception",
    "error_state_update",
    "safe_error_message",
    "ConfigurationError",
    "GraphError",
    "LLMError",
    "LLMFatalError",
    "LLMTransientError",
    "LLMValidationError",
    "ToolError",
    "LLMService",
    "create_llm_service",
    "RetrySettings",
    "build_node_retry_policy",
    "call_with_retry",
    "invoke_structured",
    "meta_update",
]
