"""AiAssistService — application façade for LangGraph AI use cases."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.auth.principals import AuthenticatedUser
from app.core.config import Settings, get_settings
from app.core.exceptions import AiProviderError, AiTimeoutError, NotFoundError
from app.models.enums import AiRunStatus as OrmAiRunStatus
from app.repositories.ai_run_repository import AiRunRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.hcp_repository import HcpRepository
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.ai import (
    AiAssistRequest,
    AiAssistResponse,
    AiEditRequest,
    AiErrorItem,
    AiFollowUpSuggestion,
    AiHistorySummaryRequest,
    AiHistorySummaryResponse,
    AiProductSuggestion,
)
from app.schemas.common import SortSpec
from app.schemas.enums import AiRunStatus, FollowUpPriority, InteractionSentiment
from app.services.llm_service import GraphConfig, create_llm_service

# CRM langgraph package (shadow-finder routes official langgraph.* submodules).
from langgraph import (  # noqa: E402
    GRAPH_NAME,
    ToolBundle,
    run_assist,
)
from langgraph.engine.exceptions import (  # noqa: E402
    ConfigurationError,
    LLMFatalError,
    LLMTransientError,
)
from langgraph.state.schemas import (  # noqa: E402
    CatalogProduct,
    HCPCandidate,
    HCPProfile,
    InteractionBrief,
    SentimentLabel,
)


class _HcpSearchAdapter:
    def __init__(self, repo: HcpRepository) -> None:
        self._repo = repo

    def search(
        self,
        query: str,
        *,
        specialty: str | None = None,
        city: str | None = None,
        limit: int = 10,
    ) -> list[HCPCandidate]:
        rows, _ = self._repo.search(
            page=1,
            page_size=max(1, min(limit, 50)),
            sort=SortSpec(field="last_name", direction="asc"),
            query=query or None,
            specialty=specialty,
            city=city,
        )
        return [
            HCPCandidate(
                id=row.id,
                first_name=row.first_name,
                last_name=row.last_name,
                full_name=f"{row.first_name} {row.last_name}".strip(),
                specialty=row.specialty,
                city=row.city,
                institution=row.institution,
            )
            for row in rows
        ]

    def get_by_id(self, hcp_id: str | UUID) -> HCPProfile | None:
        row = self._repo.get_by_id(UUID(str(hcp_id)))
        if row is None:
            return None
        return HCPProfile(
            id=row.id,
            first_name=row.first_name,
            last_name=row.last_name,
            full_name=f"{row.first_name} {row.last_name}".strip(),
            specialty=row.specialty,
            city=row.city,
            institution=row.institution,
        )


class _HistoryAdapter:
    def __init__(self, repo: InteractionRepository) -> None:
        self._repo = repo

    def list_for_hcp(
        self,
        hcp_id: str | UUID,
        *,
        limit: int,
        exclude_deleted: bool = True,
    ) -> list[InteractionBrief]:
        rows, _ = self._repo.list_filtered(
            page=1,
            page_size=max(1, min(limit, 50)),
            sort=SortSpec(field="visit_at", direction="desc"),
            hcp_id=UUID(str(hcp_id)),
            include_deleted=not exclude_deleted,
        )
        briefs: list[InteractionBrief] = []
        for row in rows:
            notes_excerpt = (row.notes or "")[:400] or None
            sentiment: SentimentLabel | None = None
            if row.sentiment is not None:
                try:
                    sentiment = SentimentLabel(row.sentiment.value)
                except ValueError:
                    sentiment = None
            briefs.append(
                InteractionBrief(
                    id=row.id,
                    visit_at=row.visit_at.isoformat() if row.visit_at else None,
                    summary=row.summary,
                    notes_excerpt=notes_excerpt,
                    sentiment=sentiment,
                    channel=row.channel.value if row.channel else None,
                )
            )
        return briefs


class _ProductCatalogAdapter:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    def lookup(self, names_or_keywords: list[str], *, limit: int = 25) -> list[CatalogProduct]:
        matches = self._repo.match_by_names(names_or_keywords)
        # Also search by keyword fragments when exact name miss.
        if len(matches) < limit:
            for keyword in names_or_keywords:
                if not keyword or not keyword.strip():
                    continue
                rows, _ = self._repo.list(
                    page=1,
                    page_size=min(10, limit),
                    sort=SortSpec(field="name", direction="asc"),
                    query=keyword.strip(),
                    is_active=True,
                )
                existing = {m.id for m in matches}
                for row in rows:
                    if row.id not in existing:
                        matches.append(row)
                        existing.add(row.id)
                if len(matches) >= limit:
                    break
        return [
            CatalogProduct(
                product_id=row.id,
                code=row.code,
                name=row.name,
                therapeutic_area=row.therapeutic_area,
            )
            for row in matches[:limit]
        ]

    def list_names(self, *, limit: int = 100) -> list[str]:
        rows, _ = self._repo.list(
            page=1,
            page_size=max(1, min(limit, 100)),
            sort=SortSpec(field="name", direction="asc"),
            is_active=True,
        )
        return [row.name for row in rows]


class _PersistenceAdapter:
    def __init__(
        self,
        *,
        ai_runs: AiRunRepository,
        audits: AuditRepository,
    ) -> None:
        self._ai_runs = ai_runs
        self._audits = audits

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
    ) -> None:
        run = self._ai_runs.get_by_id(UUID(str(ai_run_id)))
        if run is None:
            return
        if model_name:
            run.model_name = model_name
        try:
            orm_status = OrmAiRunStatus(status)
        except ValueError:
            orm_status = OrmAiRunStatus.FAILED
        self._ai_runs.finalize(
            run,
            status=orm_status,
            latency_ms=latency_ms,
            token_usage=token_usage,
            error_message=error_message,
            state_snapshot=state_snapshot,
        )

    def write_audit(
        self,
        *,
        action: str,
        user_id: str | UUID,
        correlation_id: str | UUID | None,
        entity_type: str,
        entity_id: str | UUID | None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        try:
            corr = UUID(str(correlation_id)) if correlation_id else UUID(int=0)
        except ValueError:
            corr = UUID(int=0)
        try:
            eid = UUID(str(entity_id)) if entity_id else UUID(int=0)
        except ValueError:
            eid = UUID(int=0)
        try:
            actor = UUID(str(user_id))
        except ValueError:
            actor = None
        self._audits.append(
            actor_user_id=actor,
            entity_type=entity_type,
            entity_id=eid,
            action=action,
            correlation_id=corr,
            after_state=metadata,
        )


class AiAssistService:
    """Validate inputs; create AI run; invoke LangGraph; map state → response DTO."""

    def __init__(
        self,
        session: Session,
        *,
        settings: Settings | None = None,
        hcp_repo: HcpRepository | None = None,
        interaction_repo: InteractionRepository | None = None,
        product_repo: ProductRepository | None = None,
        ai_run_repo: AiRunRepository | None = None,
        audit_repo: AuditRepository | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._hcps = hcp_repo or HcpRepository(session)
        self._interactions = interaction_repo or InteractionRepository(session)
        self._products = product_repo or ProductRepository(session)
        self._ai_runs = ai_run_repo or AiRunRepository(session)
        self._audits = audit_repo or AuditRepository(session)

    def assist(
        self,
        payload: AiAssistRequest,
        *,
        actor: AuthenticatedUser,
        correlation_id: UUID,
    ) -> AiAssistResponse:
        self._require_hcp(payload.hcp_id)
        return self._invoke(
            mode="assist",
            actor=actor,
            correlation_id=correlation_id,
            hcp_id=payload.hcp_id,
            notes=payload.notes,
            interaction_id=payload.interaction_id,
            include_history=payload.include_history,
        )

    def edit(
        self,
        payload: AiEditRequest,
        *,
        actor: AuthenticatedUser,
        correlation_id: UUID,
    ) -> AiAssistResponse:
        self._require_hcp(payload.hcp_id)
        return self._invoke(
            mode="edit",
            actor=actor,
            correlation_id=correlation_id,
            hcp_id=payload.hcp_id,
            notes=payload.notes,
            edit_instruction=payload.edit_instruction,
            include_history=True,
            regenerate_derived=payload.regenerate_derived,
            current_ai_fields=payload.current_ai_fields,
        )

    def history_summary(
        self,
        payload: AiHistorySummaryRequest,
        *,
        actor: AuthenticatedUser,
        correlation_id: UUID,
    ) -> AiHistorySummaryResponse:
        self._require_hcp(payload.hcp_id)
        state = self._invoke(
            mode="history_only",
            actor=actor,
            correlation_id=correlation_id,
            hcp_id=payload.hcp_id,
            notes="Summarize prior interactions for clinical context.",
            include_history=True,
            return_raw=True,
        )
        assert isinstance(state, dict)
        history = state.get("history") or []
        return AiHistorySummaryResponse(
            ai_run_id=UUID(str(state["ai_run_id"])),
            history_summary=state.get("history_summary"),
            interactions_considered=len(history),
        )

    def _require_hcp(self, hcp_id: UUID) -> None:
        if self._hcps.get_by_id(hcp_id) is None:
            raise NotFoundError("HCP not found")

    def _build_tools(self) -> ToolBundle:
        return ToolBundle(
            hcp=_HcpSearchAdapter(self._hcps),
            history=_HistoryAdapter(self._interactions),
            catalog=_ProductCatalogAdapter(self._products),
            persistence=_PersistenceAdapter(ai_runs=self._ai_runs, audits=self._audits),
        )

    def _graph_config(self) -> GraphConfig:
        return GraphConfig.from_env(
            groq_api_key=self._settings.GROQ_API_KEY or None,
            groq_model=self._settings.GROQ_MODEL or None,
            ai_timeout_seconds=self._settings.AI_TIMEOUT_SECONDS or None,
            ai_history_limit=self._settings.AI_HISTORY_LIMIT or None,
        )

    def _invoke(
        self,
        *,
        mode: str,
        actor: AuthenticatedUser,
        correlation_id: UUID,
        hcp_id: UUID,
        notes: str,
        interaction_id: UUID | None = None,
        include_history: bool = True,
        edit_instruction: str | None = None,
        regenerate_derived: bool = True,
        current_ai_fields: dict[str, Any] | None = None,
        return_raw: bool = False,
    ) -> AiAssistResponse | dict[str, Any]:
        cfg = self._graph_config()
        try:
            cfg.require_api_key()
        except ConfigurationError as exc:
            raise AiProviderError(str(exc)) from exc

        run = self._ai_runs.create_running(
            user_id=actor.id,
            hcp_id=hcp_id,
            interaction_id=interaction_id,
            graph_name=GRAPH_NAME,
            model_name=cfg.groq_model,
        )
        self._session.flush()

        tools = self._build_tools()
        llm = create_llm_service(cfg)

        try:
            state = run_assist(
                user_id=str(actor.id),
                notes=notes,
                hcp_id=str(hcp_id),
                ai_run_id=str(run.id),
                correlation_id=str(correlation_id),
                interaction_id=str(interaction_id) if interaction_id else None,
                include_history=include_history,
                tools=tools,
                llm=llm,
                config=cfg,
                mode=mode,
                edit_instruction=edit_instruction,
                regenerate_derived=regenerate_derived,
                current_ai_fields=current_ai_fields,
            )
        except LLMTransientError as exc:
            self._fail_run(run.id, str(exc))
            self._session.commit()
            raise AiTimeoutError(str(exc)) from exc
        except (LLMFatalError, ConfigurationError) as exc:
            self._fail_run(run.id, str(exc))
            self._session.commit()
            raise AiProviderError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001 — map unknown graph failures to 502
            self._fail_run(run.id, str(exc))
            self._session.commit()
            raise AiProviderError(f"AI graph failed: {exc}") from exc

        self._session.commit()
        if return_raw:
            return dict(state)
        return self._map_response(state)

    def _fail_run(self, ai_run_id: UUID, message: str) -> None:
        run = self._ai_runs.get_by_id(ai_run_id)
        if run is None or run.status is not OrmAiRunStatus.RUNNING:
            return
        self._ai_runs.finalize(
            run,
            status=OrmAiRunStatus.FAILED,
            error_message=message[:2000],
        )

    def _map_response(self, state: dict[str, Any]) -> AiAssistResponse:
        status_raw = state.get("status") or "failed"
        try:
            status = AiRunStatus(status_raw)
        except ValueError:
            status = AiRunStatus.FAILED

        sentiment = None
        if state.get("sentiment"):
            try:
                sentiment = InteractionSentiment(str(state["sentiment"]))
            except ValueError:
                sentiment = None

        products: list[AiProductSuggestion] = []
        for item in state.get("products") or []:
            if not isinstance(item, dict):
                continue
            pid = item.get("product_id")
            if not pid:
                continue
            products.append(
                AiProductSuggestion(
                    product_id=UUID(str(pid)),
                    name=str(item.get("name") or ""),
                    code=item.get("code"),
                    confidence=float(item.get("confidence") or 0.5),
                )
            )

        follow_ups: list[AiFollowUpSuggestion] = []
        for item in state.get("follow_ups") or []:
            if not isinstance(item, dict):
                continue
            title = (item.get("title") or "").strip()
            if not title:
                continue
            priority_raw = item.get("priority") or "medium"
            try:
                priority = FollowUpPriority(str(priority_raw))
            except ValueError:
                priority = FollowUpPriority.MEDIUM
            follow_ups.append(
                AiFollowUpSuggestion(
                    title=title,
                    description=item.get("description"),
                    priority=priority,
                    due_in_days=item.get("due_in_days"),
                )
            )

        errors: list[AiErrorItem] = []
        for err in state.get("errors") or []:
            if isinstance(err, dict):
                errors.append(
                    AiErrorItem(
                        node=err.get("node"),
                        code=err.get("code"),
                        message=str(err.get("message") or "Unknown error"),
                        fatal=bool(err.get("fatal")),
                    )
                )
            else:
                errors.append(AiErrorItem(message=str(err)))

        return AiAssistResponse(
            ai_run_id=UUID(str(state["ai_run_id"])),
            status=status,
            summary=state.get("summary"),
            sentiment=sentiment,
            sentiment_score=state.get("sentiment_score"),
            products=products,
            medical_topics=list(state.get("medical_topics") or []),
            follow_ups=follow_ups,
            history_summary=state.get("history_summary"),
            notes=state.get("notes"),
            errors=errors,
        )
