"""Database engine and session lifecycle (no ORM models)."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def init_db(settings: Settings) -> Engine:
    """Create the SQLAlchemy engine and session factory."""
    global _engine, _SessionLocal

    if _engine is not None:
        return _engine

    _engine = create_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=settings.db_pool_pre_ping,
        future=True,
    )
    _SessionLocal = sessionmaker(
        bind=_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )
    logger.info("database_initialized", pool_size=settings.db_pool_size)
    return _engine


def dispose_db() -> None:
    """Dispose the engine and clear session factory."""
    global _engine, _SessionLocal

    if _engine is not None:
        _engine.dispose()
        logger.info("database_disposed")
    _engine = None
    _SessionLocal = None


def get_engine() -> Engine:
    """Return the initialized engine."""
    if _engine is None:
        raise RuntimeError("Database engine is not initialized. Call init_db() first.")
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return the initialized session factory."""
    if _SessionLocal is None:
        raise RuntimeError("Session factory is not initialized. Call init_db() first.")
    return _SessionLocal


def session_scope() -> Generator[Session, None, None]:
    """Yield a short-lived database session."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def ping_database() -> bool:
    """Execute a trivial connectivity check."""
    engine = get_engine()
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True


def database_status() -> dict[str, Any]:
    """Return a small readiness payload."""
    try:
        ping_database()
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001 — readiness must never raise to callers
        logger.warning("database_ping_failed", error=str(exc))
        return {"status": "unavailable", "detail": str(exc)}
