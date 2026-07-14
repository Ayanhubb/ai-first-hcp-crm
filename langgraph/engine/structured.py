"""Structured LLM invocation with retry + one repair pass."""

from __future__ import annotations

import json
import time
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from ..state.schemas import ModelMeta, NodeTokenUsage
from .config import GraphConfig
from .exceptions import LLMValidationError
from .llm_factory import LLMService, map_provider_exception
from .retry import RetrySettings, call_with_retry

T = TypeVar("T", bound=BaseModel)


def _usage_from_response(response: Any, latency_ms: int) -> NodeTokenUsage:
    meta = getattr(response, "response_metadata", None) or {}
    token_usage = meta.get("token_usage") or meta.get("usage") or {}
    # langchain-groq may expose usage_metadata
    usage_metadata = getattr(response, "usage_metadata", None) or {}
    prompt = int(
        token_usage.get("prompt_tokens")
        or usage_metadata.get("input_tokens")
        or 0
    )
    completion = int(
        token_usage.get("completion_tokens")
        or usage_metadata.get("output_tokens")
        or 0
    )
    return NodeTokenUsage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        latency_ms=latency_ms,
    )


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(str(block["text"]))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # drop fence first/last
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        data = json.loads(text[start : end + 1])
        if isinstance(data, dict):
            return data
    raise LLMValidationError("Model did not return a JSON object", raw=text)


def invoke_structured(
    llm_service: LLMService,
    *,
    node: str,
    schema: type[T],
    messages: list[Any],
    temperature: float,
    max_tokens: int,
    config: GraphConfig | None = None,
    repair_messages_factory: Any | None = None,
) -> tuple[T, NodeTokenUsage, str]:
    """Invoke ChatGroq and parse into ``schema``.

    Policy:
    - Max 2 transient retries (RetrySettings.llm_max_retries)
    - Prefer ``with_structured_output``; fall back to JSON parse
    - One repair pass on validation failure
    """
    cfg = config or llm_service.config
    settings = RetrySettings(llm_max_retries=cfg.llm_max_retries)
    model = llm_service.get_chat_model(temperature=temperature, max_tokens=max_tokens)

    def _invoke_once(msgs: list[Any]) -> tuple[T, NodeTokenUsage, str]:
        started = time.perf_counter()
        try:
            structured = None
            try:
                structured = model.with_structured_output(schema)
            except Exception:
                structured = None

            if structured is not None:
                try:
                    result = structured.invoke(msgs)
                    latency_ms = int((time.perf_counter() - started) * 1000)
                    if isinstance(result, schema):
                        usage = NodeTokenUsage(latency_ms=latency_ms)
                        return result, usage, result.model_dump_json()
                    parsed = schema.model_validate(result)
                    usage = NodeTokenUsage(latency_ms=latency_ms)
                    return parsed, usage, parsed.model_dump_json()
                except ValidationError as exc:
                    raise LLMValidationError(str(exc)) from exc
                except Exception as exc:
                    # Fall through to JSON mode for providers with weak structured support
                    if "structured" in str(exc).lower() or "tool" in str(exc).lower():
                        pass
                    else:
                        mapped = map_provider_exception(exc)
                        if not isinstance(mapped, LLMValidationError):
                            raise mapped from exc

            response = model.invoke(msgs)
            latency_ms = int((time.perf_counter() - started) * 1000)
            raw = _content_to_text(getattr(response, "content", response))
            try:
                data = _extract_json_object(raw)
                parsed = schema.model_validate(data)
            except (ValidationError, LLMValidationError, json.JSONDecodeError) as exc:
                raise LLMValidationError(str(exc), raw=raw) from exc
            usage = _usage_from_response(response, latency_ms)
            return parsed, usage, raw
        except LLMValidationError:
            raise
        except Exception as exc:
            raise map_provider_exception(exc) from exc

    try:
        return call_with_retry(
            lambda: _invoke_once(messages),
            max_retries=cfg.llm_max_retries,
            settings=settings,
        )
    except LLMValidationError as first_exc:
        if cfg.llm_repair_passes < 1:
            raise
        from ..prompts.repair import build_repair_messages

        repair_msgs = (
            repair_messages_factory(first_exc)
            if repair_messages_factory
            else build_repair_messages(
                schema=schema,
                original_messages=messages,
                error=str(first_exc),
                raw=first_exc.raw,
            )
        )
        return call_with_retry(
            lambda: _invoke_once(repair_msgs),
            max_retries=0,
            settings=settings,
        )


def meta_update(node: str, usage: NodeTokenUsage, *, model_name: str | None = None) -> dict[str, Any]:
    meta = ModelMeta(model_name=model_name)
    meta.record(node, usage)
    return {"model_meta": meta.model_dump()}
