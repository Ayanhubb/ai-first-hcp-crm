"""Runtime configuration for the interaction assist graph."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GraphConfig:
    """Settings consumed by the LangGraph runtime (injected by backend or env)."""

    groq_api_key: str
    groq_model: str = "llama-3.1-8b-instant"
    ai_timeout_seconds: float = 60.0
    ai_history_limit: int = 10
    llm_max_retries: int = 2
    llm_repair_passes: int = 1
    tool_max_retries: int = 1
    summary_temperature: float = 0.3
    extraction_temperature: float = 0.1
    edit_temperature: float = 0.2
    max_tokens_summary: int = 512
    max_tokens_extraction: int = 384
    max_tokens_edit: int = 1024
    prompt_version: str = "v1"

    @classmethod
    def from_env(cls, **overrides: object) -> GraphConfig:
        """Load from environment variables used by the CRM scaffold."""
        data: dict[str, object] = {
            "groq_api_key": os.getenv("GROQ_API_KEY", ""),
            "groq_model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            "ai_timeout_seconds": float(os.getenv("AI_TIMEOUT_SECONDS", "60")),
            "ai_history_limit": int(os.getenv("AI_HISTORY_LIMIT", "10")),
        }
        data.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**data)  # type: ignore[arg-type]

    def require_api_key(self) -> str:
        from .exceptions import ConfigurationError

        if not (self.groq_api_key or "").strip():
            raise ConfigurationError("GROQ_API_KEY is required for AI assist")
        return self.groq_api_key.strip()
