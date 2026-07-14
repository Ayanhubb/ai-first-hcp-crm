"""User identity ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Enum, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.ai_run import AiRun
    from app.models.audit_log import AuditLog
    from app.models.auth_refresh_token import AuthRefreshToken
    from app.models.follow_up import FollowUp
    from app.models.interaction import Interaction


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint(
            "length(trim(email)) > 0",
            name="ck_users_email_nonempty",
        ),
        Index("ix_users_role", "role"),
        Index("ix_users_is_active", "is_active"),
    )

    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
            create_type=False,
            create_constraint=False,
        ),
        nullable=False,
        server_default=text("'mr'::user_role"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    refresh_tokens: Mapped[list[AuthRefreshToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    interactions: Mapped[list[Interaction]] = relationship(
        back_populates="user",
        foreign_keys="Interaction.user_id",
    )
    follow_ups: Mapped[list[FollowUp]] = relationship(
        back_populates="user",
        foreign_keys="FollowUp.user_id",
    )
    ai_runs: Mapped[list[AiRun]] = relationship(
        back_populates="user",
        foreign_keys="AiRun.user_id",
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        back_populates="actor",
        foreign_keys="AuditLog.actor_user_id",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!s} email={self.email!r}>"
