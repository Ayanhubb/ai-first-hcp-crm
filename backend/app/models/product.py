"""Product catalog ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.interaction import InteractionProduct


class Product(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("code", name="uq_products_code"),
        CheckConstraint(
            "length(trim(code)) > 0",
            name="ck_products_code_nonempty",
        ),
        Index("ix_products_name", "name"),
        Index(
            "ix_products_is_active",
            "is_active",
            postgresql_where=text("is_active = TRUE"),
        ),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    therapeutic_area: Mapped[str | None] = mapped_column(String(150), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    interaction_products: Mapped[list[InteractionProduct]] = relationship(
        back_populates="product",
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id!s} code={self.code!r}>"
