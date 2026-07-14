"""Groq + LangChain LLM factory for the interaction assist graph."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import GraphConfig
from .exceptions import ConfigurationError, LLMFatalError, LLMTransientError


@dataclass(slots=True)
class LLMService:
    """Thin adapter around ChatGroq used by nodes (architecture ILLMService port)."""

    config: GraphConfig
    _model_cache: dict[tuple[float, int], Any] | None = None

    def __post_init__(self) -> None:
        self._model_cache = {}

    @property
    def model_name(self) -> str:
        return self.config.groq_model

    def get_chat_model(self, *, temperature: float, max_tokens: int):
        """Return a ChatGroq instance configured for this call profile."""
        key = (temperature, max_tokens)
        assert self._model_cache is not None
        if key in self._model_cache:
            return self._model_cache[key]

        api_key = self.config.require_api_key()
        try:
            from langchain_groq import ChatGroq
        except ImportError as exc:
            raise ConfigurationError(
                "langchain-groq is required for Groq integration"
            ) from exc

        model = ChatGroq(
            model=self.config.groq_model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=self.config.ai_timeout_seconds,
            max_retries=0,  # retries owned by runtime.retry / error policy
        )
        self._model_cache[key] = model
        return model

    def for_summary(self):
        return self.get_chat_model(
            temperature=self.config.summary_temperature,
            max_tokens=self.config.max_tokens_summary,
        )

    def for_extraction(self):
        return self.get_chat_model(
            temperature=self.config.extraction_temperature,
            max_tokens=self.config.max_tokens_extraction,
        )

    def for_edit(self):
        return self.get_chat_model(
            temperature=self.config.edit_temperature,
            max_tokens=self.config.max_tokens_edit,
        )


def create_llm_service(config: GraphConfig | None = None) -> LLMService:
    """Factory used by the graph builder / AiAssistService."""
    return LLMService(config=config or GraphConfig.from_env())


def map_provider_exception(exc: BaseException) -> BaseException:
    """Normalize Groq/LangChain exceptions into runtime LLM errors."""
    name = type(exc).__name__
    msg = str(exc)
    lower = msg.lower()

    if name in {"AuthenticationError", "PermissionDeniedError"} or "invalid api key" in lower:
        return LLMFatalError(msg, code="LLM_AUTH")
    if name in {"APITimeoutError", "TimeoutError", "ReadTimeout"} or "timeout" in lower:
        return LLMTransientError(msg, code="LLM_TIMEOUT")
    if name in {"RateLimitError"} or "429" in lower or "rate limit" in lower:
        return LLMTransientError(msg, code="LLM_RATE_LIMIT")
    if name in {"APIConnectionError", "InternalServerError", "ServiceUnavailableError"}:
        return LLMTransientError(msg, code="LLM_TRANSIENT")
    if "503" in lower or "502" in lower or "overloaded" in lower:
        return LLMTransientError(msg, code="LLM_TRANSIENT")
    return LLMTransientError(msg, code="LLM_PROVIDER")
