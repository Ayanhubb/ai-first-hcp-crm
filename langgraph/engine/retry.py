"""Retry helpers for LLM and tool calls."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from .exceptions import LLMTransientError, ToolError

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class RetrySettings:
    """Operational retry policy (design §15)."""

    llm_max_retries: int = 2
    tool_max_retries: int = 1
    base_delay_seconds: float = 0.4
    max_delay_seconds: float = 4.0
    jitter_ratio: float = 0.25


def compute_backoff(attempt: int, settings: RetrySettings) -> float:
    """Exponential backoff with jitter. ``attempt`` is 0-based retry index."""
    delay = min(settings.max_delay_seconds, settings.base_delay_seconds * (2**attempt))
    jitter = delay * settings.jitter_ratio * random.random()
    return delay + jitter


def call_with_retry(
    fn: Callable[[], T],
    *,
    max_retries: int,
    settings: RetrySettings | None = None,
    retry_on: Callable[[BaseException], bool] | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Execute ``fn`` with retries on transient failures.

    ``max_retries`` is the number of *retries* after the first attempt
    (design: LLM transient → max 2 retries).
    """
    settings = settings or RetrySettings()
    predicate = retry_on or default_is_retryable
    attempts = max_retries + 1
    last_exc: BaseException | None = None

    for attempt in range(attempts):
        try:
            return fn()
        except BaseException as exc:
            last_exc = exc
            if attempt >= max_retries or not predicate(exc):
                raise
            sleep(compute_backoff(attempt, settings))

    assert last_exc is not None
    raise last_exc


def default_is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, LLMTransientError):
        return True
    if isinstance(exc, ToolError) and exc.transient:
        return True
    # Common provider / HTTP signals without importing httpx/groq types tightly
    name = type(exc).__name__.lower()
    msg = str(exc).lower()
    if any(tok in name for tok in ("timeout", "rate", "unavailable", "connection")):
        return True
    if any(tok in msg for tok in ("timeout", "429", "rate limit", "503", "502", "overloaded")):
        return True
    return False


def build_node_retry_policy(max_attempts: int = 3):
    """Build a LangGraph ``RetryPolicy`` for node-level retries when available."""
    from .lg_imports import import_retry_policy

    retry_cls = import_retry_policy()
    if retry_cls is None:
        return None
    return retry_cls(max_attempts=max_attempts)
