"""Interaction aggregate create / read / update / soft-delete use cases."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.auth.principals import AuthenticatedUser
from app.auth.roles import UserRole
from app.core.exceptions import NotFoundError, ValidationAppError
from app.domain.policies import assert_interaction_access, assert_visit_at_sane
from app.models.enums import (
    FollowUpPriority as OrmFollowUpPriority,
)
from app.models.enums import (
    FollowUpStatus as OrmFollowUpStatus,
)
from app.models.enums import (
    InteractionSentiment as OrmSentiment,
)
from app.models.enums import (
    InteractionStatus as OrmStatus,
)
from app.models.enums import (
    RecordSource as OrmRecordSource,
)
from app.models.enums import (
    VisitChannel as OrmChannel,
)
from app.models.follow_up import FollowUp
from app.models.interaction import Interaction, InteractionProduct
from app.repositories.ai_run_repository import AiRunRepository
from app.repositories.follow_up_repository import FollowUpRepository
from app.repositories.hcp_repository import HcpRepository
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.common import Page, PaginationParams, parse_sort
from app.schemas.enums import InteractionSentiment, InteractionStatus
from app.schemas.hcp import HcpSummary
from app.schemas.interaction import (
    FollowUpCreate,
    FollowUpResponse,
    InteractionCreate,
    InteractionDetail,
    InteractionProductResponse,
    InteractionSummary,
    InteractionUpdate,
)
from app.schemas.product import ProductResponse
from app.services.audit_service import AuditService


_INTERACTION_SORT = frozenset({"visit_at", "created_at"})


class InteractionService:
    """Owns interaction aggregate writes/reads and ownership checks."""

    def __init__(
        self,
        session: Session,
        *,
        interaction_repo: InteractionRepository | None = None,
        hcp_repo: HcpRepository | None = None,
        product_repo: ProductRepository | None = None,
        follow_up_repo: FollowUpRepository | None = None,
        ai_run_repo: AiRunRepository | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self._session = session
        self._interactions = interaction_repo or InteractionRepository(session)
        self._hcps = hcp_repo or HcpRepository(session)
        self._products = product_repo or ProductRepository(session)
        self._follow_ups = follow_up_repo or FollowUpRepository(session)
        self._ai_runs = ai_run_repo or AiRunRepository(session)
        self._audits = audit_service or AuditService(session)

    def create(
        self,
        payload: InteractionCreate,
        *,
        actor: AuthenticatedUser,
        correlation_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> InteractionDetail:
        assert_visit_at_sane(payload.visit_at)
        hcp = self._hcps.get_by_id(payload.hcp_id)
        if hcp is None:
            raise NotFoundError("Healthcare professional not found")

        products = self._resolve_products(payload.product_ids)
        if payload.ai_run_id is not None:
            ai_run = self._ai_runs.get_by_id(payload.ai_run_id)
            if ai_run is None:
                raise NotFoundError("AI run not found")

        interaction = Interaction(
            user_id=actor.id,
            hcp_id=payload.hcp_id,
            visit_at=payload.visit_at,
            channel=OrmChannel(payload.channel.value),
            notes=payload.notes,
            summary=payload.summary,
            sentiment=(
                OrmSentiment(payload.sentiment.value) if payload.sentiment is not None else None
            ),
            sentiment_score=payload.sentiment_score,
            medical_topics=list(payload.medical_topics),
            ai_run_id=payload.ai_run_id,
            status=OrmStatus(payload.status.value),
        )
        self._interactions.create(interaction)
        self._attach_products(interaction, products)
        self._attach_follow_ups(interaction, actor.id, payload.follow_ups)

        self._audits.append(
            actor_user_id=actor.id,
            entity_type="interaction",
            entity_id=interaction.id,
            action="INTERACTION_CREATE",
            correlation_id=correlation_id,
            after_state=self._snapshot(interaction),
            ip_address=ip_address,
        )
        self._session.commit()

        detail = self._interactions.get_detail(interaction.id)
        assert detail is not None
        return self._to_detail(detail)

    def list_interactions(
        self,
        *,
        actor: AuthenticatedUser,
        pagination: PaginationParams,
        hcp_id: uuid.UUID | None = None,
        visit_from: datetime | None = None,
        visit_to: datetime | None = None,
        sentiment: InteractionSentiment | None = None,
        status: InteractionStatus | None = None,
        user_id: uuid.UUID | None = None,
        sort: str | None = None,
    ) -> Page[InteractionSummary]:
        try:
            sort_spec = parse_sort(sort, whitelist=_INTERACTION_SORT, default="visit_at:desc")
        except ValueError as exc:
            raise ValidationAppError(str(exc), details=[{"field": "sort", "issue": str(exc)}]) from exc

        owner: uuid.UUID | None
        if actor.role is UserRole.ADMIN:
            owner = user_id
        else:
            owner = actor.id

        orm_sentiment = OrmSentiment(sentiment.value) if sentiment is not None else None
        orm_status = OrmStatus(status.value) if status is not None else None

        rows, total = self._interactions.list_filtered(
            page=pagination.page,
            page_size=pagination.page_size,
            sort=sort_spec,
            owner_user_id=owner,
            hcp_id=hcp_id,
            visit_from=visit_from,
            visit_to=visit_to,
            sentiment=orm_sentiment,
            status=orm_status,
        )
        return Page[InteractionSummary](
            items=[self._to_summary(row) for row in rows],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    def get_by_id(
        self,
        interaction_id: uuid.UUID,
        *,
        actor: AuthenticatedUser,
    ) -> InteractionDetail:
        interaction = self._interactions.get_detail(interaction_id)
        if interaction is None:
            raise NotFoundError("Interaction not found")
        assert_interaction_access(actor, interaction)
        return self._to_detail(interaction)

    def update(
        self,
        interaction_id: uuid.UUID,
        payload: InteractionUpdate,
        *,
        actor: AuthenticatedUser,
        correlation_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> InteractionDetail:
        interaction = self._interactions.get_detail(interaction_id)
        if interaction is None:
            raise NotFoundError("Interaction not found")
        assert_interaction_access(actor, interaction)

        before = self._snapshot(interaction)

        if payload.visit_at is not None:
            assert_visit_at_sane(payload.visit_at)
            interaction.visit_at = payload.visit_at
        if payload.channel is not None:
            interaction.channel = OrmChannel(payload.channel.value)
        if payload.notes is not None:
            interaction.notes = payload.notes
        if payload.status is not None:
            interaction.status = OrmStatus(payload.status.value)
        if payload.summary is not None:
            interaction.summary = payload.summary
        if payload.sentiment is not None:
            interaction.sentiment = OrmSentiment(payload.sentiment.value)
        if payload.sentiment_score is not None:
            interaction.sentiment_score = payload.sentiment_score
        if payload.medical_topics is not None:
            interaction.medical_topics = list(payload.medical_topics)

        if interaction.status is OrmStatus.SAVED and not (interaction.notes or "").strip():
            raise ValidationAppError(
                "notes are required when status is saved",
                details=[{"field": "notes", "issue": "required for saved interactions"}],
            )

        if payload.product_ids is not None:
            products = self._resolve_products(payload.product_ids)
            self._interactions.replace_products(
                interaction,
                [
                    InteractionProduct(
                        product_id=p.id,
                        source=OrmRecordSource.MANUAL,
                    )
                    for p in products
                ],
            )

        if payload.follow_ups is not None:
            self._interactions.clear_follow_ups(interaction)
            self._attach_follow_ups(interaction, interaction.user_id, payload.follow_ups)

        self._interactions.update(interaction)
        self._audits.append(
            actor_user_id=actor.id,
            entity_type="interaction",
            entity_id=interaction.id,
            action="INTERACTION_UPDATE",
            correlation_id=correlation_id,
            before_state=before,
            after_state=self._snapshot(interaction),
            ip_address=ip_address,
        )
        self._session.commit()

        detail = self._interactions.get_detail(interaction.id)
        assert detail is not None
        return self._to_detail(detail)

    def soft_delete(
        self,
        interaction_id: uuid.UUID,
        *,
        actor: AuthenticatedUser,
        correlation_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> None:
        interaction = self._interactions.get_by_id(interaction_id)
        if interaction is None or interaction.is_deleted:
            raise NotFoundError("Interaction not found")
        assert_interaction_access(actor, interaction)

        before = self._snapshot(interaction)
        self._interactions.soft_delete(interaction)
        self._audits.append(
            actor_user_id=actor.id,
            entity_type="interaction",
            entity_id=interaction.id,
            action="INTERACTION_DELETE",
            correlation_id=correlation_id,
            before_state=before,
            after_state={"is_deleted": True},
            ip_address=ip_address,
        )
        self._session.commit()

    def list_for_hcp(
        self,
        hcp_id: uuid.UUID,
        *,
        actor: AuthenticatedUser,
        pagination: PaginationParams,
        visit_from: datetime | None = None,
        visit_to: datetime | None = None,
        sort: str | None = None,
    ) -> Page[InteractionSummary]:
        if self._hcps.get_by_id(hcp_id) is None:
            raise NotFoundError("Healthcare professional not found")
        return self.list_interactions(
            actor=actor,
            pagination=pagination,
            hcp_id=hcp_id,
            visit_from=visit_from,
            visit_to=visit_to,
            sort=sort,
        )

    def _resolve_products(self, product_ids: list[uuid.UUID]) -> list[Any]:
        if not product_ids:
            return []
        products = self._products.get_by_ids(product_ids)
        found = {p.id for p in products}
        missing = [str(pid) for pid in product_ids if pid not in found]
        if missing:
            raise NotFoundError(f"Product(s) not found: {', '.join(missing)}")
        return products

    def _attach_products(self, interaction: Interaction, products: list[Any]) -> None:
        links = [
            InteractionProduct(
                interaction_id=interaction.id,
                product_id=product.id,
                source=OrmRecordSource.MANUAL,
            )
            for product in products
        ]
        for link in links:
            self._session.add(link)
        self._session.flush()

    def _attach_follow_ups(
        self,
        interaction: Interaction,
        user_id: uuid.UUID,
        follow_ups: list[FollowUpCreate],
    ) -> None:
        rows = [
            FollowUp(
                interaction_id=interaction.id,
                user_id=user_id,
                title=item.title,
                description=item.description,
                priority=OrmFollowUpPriority(item.priority.value),
                due_at=item.due_at,
                status=OrmFollowUpStatus.OPEN,
                source=OrmRecordSource.MANUAL,
            )
            for item in follow_ups
        ]
        self._follow_ups.bulk_create(rows)

    def _to_summary(self, interaction: Interaction) -> InteractionSummary:
        hcp_name = None
        if interaction.hcp is not None:
            hcp_name = f"{interaction.hcp.first_name} {interaction.hcp.last_name}".strip()
        return InteractionSummary(
            id=interaction.id,
            hcp_id=interaction.hcp_id,
            user_id=interaction.user_id,
            visit_at=interaction.visit_at,
            channel=interaction.channel,  # type: ignore[arg-type]
            status=interaction.status,  # type: ignore[arg-type]
            sentiment=interaction.sentiment,  # type: ignore[arg-type]
            summary=interaction.summary,
            created_at=interaction.created_at,
            updated_at=interaction.updated_at,
            hcp_name=hcp_name,
        )

    def _to_detail(self, interaction: Interaction) -> InteractionDetail:
        product_rows: list[InteractionProductResponse] = []
        for link in interaction.products:
            product_rows.append(
                InteractionProductResponse(
                    product_id=link.product_id,
                    confidence=link.confidence,
                    source=link.source,  # type: ignore[arg-type]
                    product=(
                        ProductResponse.model_validate(link.product)
                        if link.product is not None
                        else None
                    ),
                )
            )

        hcp_payload = None
        if interaction.hcp is not None:
            hcp_payload = HcpSummary.model_validate(interaction.hcp).model_dump()

        topics = interaction.medical_topics if isinstance(interaction.medical_topics, list) else []

        return InteractionDetail(
            id=interaction.id,
            user_id=interaction.user_id,
            hcp_id=interaction.hcp_id,
            visit_at=interaction.visit_at,
            channel=interaction.channel,  # type: ignore[arg-type]
            notes=interaction.notes,
            summary=interaction.summary,
            sentiment=interaction.sentiment,  # type: ignore[arg-type]
            sentiment_score=interaction.sentiment_score,
            medical_topics=[str(t) for t in topics],
            ai_run_id=interaction.ai_run_id,
            status=interaction.status,  # type: ignore[arg-type]
            is_deleted=interaction.is_deleted,
            created_at=interaction.created_at,
            updated_at=interaction.updated_at,
            products=product_rows,
            follow_ups=[FollowUpResponse.model_validate(fu) for fu in interaction.follow_ups],
            hcp=hcp_payload,
        )

    @staticmethod
    def _snapshot(interaction: Interaction) -> dict[str, Any]:
        return {
            "id": str(interaction.id),
            "user_id": str(interaction.user_id),
            "hcp_id": str(interaction.hcp_id),
            "visit_at": interaction.visit_at.isoformat() if interaction.visit_at else None,
            "channel": interaction.channel.value if interaction.channel else None,
            "status": interaction.status.value if interaction.status else None,
            "sentiment": interaction.sentiment.value if interaction.sentiment else None,
            "notes": interaction.notes,
            "summary": interaction.summary,
            "is_deleted": interaction.is_deleted,
        }
