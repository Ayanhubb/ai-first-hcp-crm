"""Package-local exceptions for LLM and graph runtime failures."""

from __future__ import annotations


class GraphError(Exception):
    """Base error for the interaction assist graph."""

    def __init__(self, message: str, *, code: str = "GRAPH_ERROR", fatal: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.fatal = fatal


class LLMError(GraphError):
    """Base LLM failure."""

    def __init__(self, message: str, *, code: str = "LLM_ERROR", fatal: bool = False) -> None:
        super().__init__(message, code=code, fatal=fatal)


class LLMTransientError(LLMError):
    """Timeouts, 429, 5xx — eligible for retry."""

    def __init__(self, message: str, *, code: str = "LLM_TRANSIENT") -> None:
        super().__init__(message, code=code, fatal=False)


class LLMValidationError(LLMError):
    """Structured output failed schema validation — eligible for one repair pass."""

    def __init__(self, message: str, *, raw: str | None = None) -> None:
        super().__init__(message, code="LLM_VALIDATION", fatal=False)
        self.raw = raw


class LLMFatalError(LLMError):
    """Auth / budget exhausted / non-recoverable provider error."""

    def __init__(self, message: str, *, code: str = "LLM_FATAL") -> None:
        super().__init__(message, code=code, fatal=True)


class ToolError(GraphError):
    """Domain tool failure (DB, catalog, persistence)."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "TOOL_ERROR",
        fatal: bool = True,
        transient: bool = False,
    ) -> None:
        super().__init__(message, code=code, fatal=fatal)
        self.transient = transient


class ConfigurationError(GraphError):
    """Missing or invalid runtime configuration (e.g. GROQ_API_KEY)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="CONFIG_ERROR", fatal=True)
