"""Interaction aggregate persistence repository."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.enums import InteractionSentiment, InteractionStatus
from app.models.hcp import HealthcareProfessional
from app.models.interaction import Interaction, InteractionProduct
from app.schemas.common import SortSpec


class InteractionRepository:
    """Data access for ``interactions`` and ``interaction_products``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, interaction_id: uuid.UUID) -> Interaction | None:
        return self._session.get(Interaction, interaction_id)

    def get_detail(self, interaction_id: uuid.UUID) -> Interaction | None:
        stmt = (
            select(Interaction)
            .where(
                Interaction.id == interaction_id,
                Interaction.is_deleted.is_(False),
            )
            .options(
                selectinload(Interaction.products).joinedload(InteractionProduct.product),
                selectinload(Interaction.follow_ups),
                joinedload(Interaction.hcp),
            )
        )
        return self._session.scalars(stmt).first()

    def create(self, interaction: Interaction) -> Interaction:
        self._session.add(interaction)
        self._session.flush()
        return interaction

    def update(self, interaction: Interaction) -> Interaction:
        self._session.add(interaction)
        self._session.flush()
        return interaction

    def soft_delete(self, interaction: Interaction) -> Interaction:
        interaction.is_deleted = True
        self._session.add(interaction)
        self._session.flush()
        return interaction

    def replace_products(
        self,
        interaction: Interaction,
        links: list[InteractionProduct],
    ) -> None:
        interaction.products.clear()
        self._session.flush()
        for link in links:
            link.interaction_id = interaction.id
            interaction.products.append(link)
        self._session.flush()

    def list_filtered(
        self,
        *,
        page: int,
        page_size: int,
        sort: SortSpec,
        owner_user_id: uuid.UUID | None = None,
        hcp_id: uuid.UUID | None = None,
        visit_from: datetime | None = None,
        visit_to: datetime | None = None,
        sentiment: InteractionSentiment | None = None,
        status: InteractionStatus | None = None,
        include_deleted: bool = False,
    ) -> tuple[list[Interaction], int]:
        filters: list[object] = []
        if not include_deleted:
            filters.append(Interaction.is_deleted.is_(False))
        if owner_user_id is not None:
            filters.append(Interaction.user_id == owner_user_id)
        if hcp_id is not None:
            filters.append(Interaction.hcp_id == hcp_id)
        if visit_from is not None:
            filters.append(Interaction.visit_at >= visit_from)
        if visit_to is not None:
            filters.append(Interaction.visit_at <= visit_to)
        if sentiment is not None:
            filters.append(Interaction.sentiment == sentiment)
        if status is not None:
            filters.append(Interaction.status == status)

        count_stmt = select(func.count()).select_from(Interaction)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total = int(self._session.scalar(count_stmt) or 0)

        order_col = {
            "visit_at": Interaction.visit_at,
            "created_at": Interaction.created_at,
        }[sort.field]
        order_by = order_col.desc() if sort.is_desc else order_col.asc()

        stmt: Select[tuple[Interaction]] = (
            select(Interaction)
            .options(joinedload(Interaction.hcp))
        )
        if filters:
            stmt = stmt.where(*filters)
        stmt = (
            stmt.order_by(order_by)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self._session.scalars(stmt).unique().all()), total

    def count_for_user_since(
        self,
        *,
        user_id: uuid.UUID,
        since: datetime,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Interaction)
            .where(
                Interaction.user_id == user_id,
                Interaction.is_deleted.is_(False),
                Interaction.visit_at >= since,
            )
        )
        return int(self._session.scalar(stmt) or 0)

    def list_recent_for_user(
        self,
        *,
        user_id: uuid.UUID,
        limit: int = 5,
    ) -> list[tuple[Interaction, HealthcareProfessional]]:
        stmt = (
            select(Interaction, HealthcareProfessional)
            .join(
                HealthcareProfessional,
                HealthcareProfessional.id == Interaction.hcp_id,
            )
            .where(
                Interaction.user_id == user_id,
                Interaction.is_deleted.is_(False),
            )
            .order_by(Interaction.visit_at.desc())
            .limit(limit)
        )
        return list(self._session.execute(stmt).all())

    def clear_follow_ups(self, interaction: Interaction) -> None:
        for follow_up in list(interaction.follow_ups):
            self._session.delete(follow_up)
        self._session.flush()
