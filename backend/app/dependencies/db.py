"""Database session dependency injection."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.database import get_session_factory


def get_db() -> Generator[Session, None, None]:
    """Provide a request-scoped SQLAlchemy session."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


__all__ = ["get_db"]
