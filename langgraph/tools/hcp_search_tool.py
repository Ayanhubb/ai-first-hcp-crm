"""Search HCP domain tool (read-only)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from ..engine.exceptions import ToolError
from ..engine.retry import RetrySettings, call_with_retry
from ..state.schemas import HCPCandidate, HCPProfile
from .base import HCPSearchPort


def search_hcp(
    port: HCPSearchPort,
    *,
    query: str,
    specialty: str | None = None,
    city: str | None = None,
    limit: int = 10,
    retry_settings: RetrySettings | None = None,
) -> list[HCPCandidate]:
    """Find healthcare professionals by free-text query."""

    def _call() -> list[HCPCandidate]:
        try:
            return port.search(query, specialty=specialty, city=city, limit=limit)
        except ToolError:
            raise
        except Exception as exc:
            transient = "connection" in str(exc).lower() or "timeout" in str(exc).lower()
            raise ToolError(
                f"HCP search failed: {exc}",
                code="HCP_SEARCH_ERROR",
                fatal=True,
                transient=transient,
            ) from exc

    settings = retry_settings or RetrySettings()
    return call_with_retry(
        _call,
        max_retries=settings.tool_max_retries,
        settings=settings,
        retry_on=lambda e: isinstance(e, ToolError) and e.transient,
    )


def get_hcp_by_id(
    port: HCPSearchPort,
    hcp_id: str | UUID,
    *,
    retry_settings: RetrySettings | None = None,
) -> HCPProfile | None:
    """Verify / load an HCP by id."""

    def _call() -> HCPProfile | None:
        try:
            return port.get_by_id(hcp_id)
        except ToolError:
            raise
        except Exception as exc:
            transient = "connection" in str(exc).lower() or "timeout" in str(exc).lower()
            raise ToolError(
                f"HCP lookup failed: {exc}",
                code="HCP_LOOKUP_ERROR",
                fatal=True,
                transient=transient,
            ) from exc

    settings = retry_settings or RetrySettings()
    return call_with_retry(
        _call,
        max_retries=settings.tool_max_retries,
        settings=settings,
        retry_on=lambda e: isinstance(e, ToolError) and e.transient,
    )


def hcp_profile_to_dict(profile: HCPProfile) -> dict[str, Any]:
    return profile.model_dump(mode="json")
