"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.router import api_router
from app.core.constants import APP_NAME, APP_VERSION
from app.core.database import dispose_db, init_db
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.dependencies.settings import get_settings
from app.middleware import register_middleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown hooks."""
    settings = get_settings()
    configure_logging(settings.log_level)
    init_db(settings)
    logger.info(
        "application_startup",
        app=APP_NAME,
        version=APP_VERSION,
        environment=settings.environment,
    )
    try:
        yield
    finally:
        dispose_db()
        logger.info("application_shutdown")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        lifespan=lifespan,
    )

    register_middleware(application, settings)
    register_exception_handlers(application)
    application.include_router(api_router)

    return application


app = create_app()
