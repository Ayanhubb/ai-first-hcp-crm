"""Dependency providers for repositories and services."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth import (
    RequireAdmin,
    RequireAnyRole,
    RequireAuthenticated,
    RequireMR,
    get_access_token_payload,
    get_current_user,
    require_roles,
)
from app.core.config import Settings, get_settings
from app.dependencies.db import get_db
from app.repositories.ai_run_repository import AiRunRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.follow_up_repository import FollowUpRepository
from app.repositories.hcp_repository import HcpRepository
from app.repositories.interaction_repository import InteractionRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.ai_assist_service import AiAssistService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService
from app.services.follow_up_service import FollowUpService
from app.services.hcp_service import HcpService
from app.services.interaction_service import InteractionService
from app.services.product_service import ProductService
from app.services.user_service import UserService

DbSession = Annotated[Session, Depends(get_db)]


def get_user_repository(db: DbSession) -> UserRepository:
    return UserRepository(db)


def get_hcp_repository(db: DbSession) -> HcpRepository:
    return HcpRepository(db)


def get_product_repository(db: DbSession) -> ProductRepository:
    return ProductRepository(db)


def get_interaction_repository(db: DbSession) -> InteractionRepository:
    return InteractionRepository(db)


def get_follow_up_repository(db: DbSession) -> FollowUpRepository:
    return FollowUpRepository(db)


def get_ai_run_repository(db: DbSession) -> AiRunRepository:
    return AiRunRepository(db)


def get_audit_repository(db: DbSession) -> AuditRepository:
    return AuditRepository(db)


def get_refresh_token_repository(db: DbSession) -> RefreshTokenRepository:
    return RefreshTokenRepository(db)


def get_audit_service(db: DbSession) -> AuditService:
    return AuditService(db)


def get_auth_service(db: DbSession) -> AuthService:
    return AuthService(db)


def get_ai_assist_service(db: DbSession) -> AiAssistService:
    return AiAssistService(db)


def get_user_service(db: DbSession) -> UserService:
    return UserService(db)


def get_hcp_service(db: DbSession) -> HcpService:
    return HcpService(db)


def get_product_service(db: DbSession) -> ProductService:
    return ProductService(db)


def get_follow_up_service(db: DbSession) -> FollowUpService:
    return FollowUpService(db)


def get_dashboard_service(db: DbSession) -> DashboardService:
    return DashboardService(db)


def get_interaction_service(db: DbSession) -> InteractionService:
    return InteractionService(db)


__all__ = [
    "DbSession",
    "RequireAdmin",
    "RequireAnyRole",
    "RequireAuthenticated",
    "RequireMR",
    "Settings",
    "get_access_token_payload",
    "get_ai_assist_service",
    "get_ai_run_repository",
    "get_audit_repository",
    "get_audit_service",
    "get_auth_service",
    "get_current_user",
    "get_dashboard_service",
    "get_follow_up_repository",
    "get_follow_up_service",
    "get_hcp_repository",
    "get_hcp_service",
    "get_interaction_repository",
    "get_interaction_service",
    "get_product_repository",
    "get_product_service",
    "get_refresh_token_repository",
    "get_settings",
    "get_user_repository",
    "get_user_service",
    "require_roles",
]
