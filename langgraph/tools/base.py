"""Domain tool ports bound by AiAssistService (request-scoped repositories)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import UUID

from ..state.schemas import CatalogProduct, HCPCandidate, HCPProfile, InteractionBrief


class HCPSearchPort(Protocol):
    def search(
        self,
        query: str,
        *,
        specialty: str | None = None,
        city: str | None = None,
        limit: int = 10,
    ) -> list[HCPCandidate]: ...

    def get_by_id(self, hcp_id: str | UUID) -> HCPProfile | None: ...


class HistoryPort(Protocol):
    def list_for_hcp(
        self,
        hcp_id: str | UUID,
        *,
        limit: int,
        exclude_deleted: bool = True,
    ) -> list[InteractionBrief]: ...


class ProductCatalogPort(Protocol):
    def lookup(self, names_or_keywords: list[str], *, limit: int = 25) -> list[CatalogProduct]: ...

    def list_names(self, *, limit: int = 100) -> list[str]: ...


class PersistencePort(Protocol):
    def finalize_ai_run(
        self,
        ai_run_id: str | UUID,
        *,
        status: str,
        model_name: str | None,
        latency_ms: int | None,
        token_usage: dict[str, Any] | None,
        error_message: str | None,
        state_snapshot: dict[str, Any] | None,
    ) -> None: ...

    def write_audit(
        self,
        *,
        action: str,
        user_id: str | UUID,
        correlation_id: str | UUID | None,
        entity_type: str,
        entity_id: str | UUID | None,
        metadata: dict[str, Any] | None = None,
    ) -> None: ...


@dataclass
class ToolBundle:
    """Request-scoped tool ports injected by the backend AiAssistService."""

    hcp: HCPSearchPort | None = None
    history: HistoryPort | None = None
    catalog: ProductCatalogPort | None = None
    persistence: PersistencePort | None = None
    extras: dict[str, Any] = field(default_factory=dict)
