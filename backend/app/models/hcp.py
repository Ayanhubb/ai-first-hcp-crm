"""Healthcare professional master data."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.ai_run import AiRun
    from app.models.interaction import Interaction


class HealthcareProfessional(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "healthcare_professionals"
    __table_args__ = (
        UniqueConstraint("registration_number", name="uq_hcps_registration_number"),
        Index("ix_hcps_last_name_first_name", "last_name", "first_name"),
        Index("ix_hcps_specialty_city", "specialty", "city"),
    )

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    specialty: Mapped[str] = mapped_column(String(150), nullable=False)
    institution: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    interactions: Mapped[list[Interaction]] = relationship(
        back_populates="hcp",
        foreign_keys="Interaction.hcp_id",
    )
    ai_runs: Mapped[list[AiRun]] = relationship(
        back_populates="hcp",
        foreign_keys="AiRun.hcp_id",
    )

    def __repr__(self) -> str:
        return (
            f"<HealthcareProfessional id={self.id!s} "
            f"name={self.last_name!r},{self.first_name!r}>"
        )
