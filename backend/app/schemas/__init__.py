"""Pydantic schemas package."""

from app.schemas.ai import (
    AiAssistRequest,
    AiAssistResponse,
    AiEditRequest,
    AiHistorySummaryRequest,
    AiHistorySummaryResponse,
)
from app.schemas.auth import LoginRequest, LoginResponse, LogoutRequest, RefreshRequest, TokenResponse
from app.schemas.common import Page, PaginationParams, parse_sort
from app.schemas.dashboard import DashboardSummaryResponse
from app.schemas.hcp import HcpPage, HcpResponse, HcpSearchParams, HcpSummary
from app.schemas.interaction import (
    InteractionCreate,
    InteractionDetail,
    InteractionPage,
    InteractionSummary,
    InteractionUpdate,
)
from app.schemas.product import ProductPage, ProductResponse
from app.schemas.user import UserMeResponse, UserPage, UserResponse

__all__ = [
    "AiAssistRequest",
    "AiAssistResponse",
    "AiEditRequest",
    "AiHistorySummaryRequest",
    "AiHistorySummaryResponse",
    "DashboardSummaryResponse",
    "HcpPage",
    "HcpResponse",
    "HcpSearchParams",
    "HcpSummary",
    "InteractionCreate",
    "InteractionDetail",
    "InteractionPage",
    "InteractionSummary",
    "InteractionUpdate",
    "LoginRequest",
    "LoginResponse",
    "LogoutRequest",
    "Page",
    "PaginationParams",
    "ProductPage",
    "ProductResponse",
    "RefreshRequest",
    "TokenResponse",
    "UserMeResponse",
    "UserPage",
    "UserResponse",
    "parse_sort",
]
