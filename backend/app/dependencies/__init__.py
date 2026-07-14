"""FastAPI dependency providers."""

from app.dependencies.db import get_db
from app.dependencies.settings import get_settings

__all__ = ["get_db", "get_settings"]
