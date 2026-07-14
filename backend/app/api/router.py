"""Root API router registration."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1 import ai, auth, dashboard, hcps, interactions, products, users
from app.core.constants import API_V1_PREFIX
from app.core.logging import get_logger
from app.dependencies.db import get_db

logger = get_logger(__name__)

health_router = APIRouter(tags=["Health"])
api_v1_router = APIRouter(prefix=API_V1_PREFIX)


@health_router.get("/health/live", summary="Liveness probe")
def health_live() -> dict[str, str]:
    """Return process liveness status."""
    return {"status": "ok"}


@health_router.get("/health/ready", summary="Readiness probe")
def health_ready(
    response: Response,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Return readiness based on database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001 — probe should return 503, not raise 500
        logger.warning("readiness_check_failed", error=str(exc))
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable"}


def build_api_router() -> APIRouter:
    """Compose the application router tree."""
    router = APIRouter()
    router.include_router(health_router)

    api_v1_router.include_router(auth.router)
    api_v1_router.include_router(users.router)
    api_v1_router.include_router(hcps.router)
    api_v1_router.include_router(interactions.router)
    api_v1_router.include_router(products.router)
    api_v1_router.include_router(dashboard.router)
    api_v1_router.include_router(ai.router)

    router.include_router(api_v1_router)
    return router


api_router = build_api_router()
