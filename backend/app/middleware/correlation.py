"""Correlation ID middleware."""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.constants import REQUEST_ID_HEADER
from app.core.logging import bind_request_context, clear_request_context


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Read or generate ``X-Request-ID`` and bind it to logging context."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        correlation_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        bind_request_context(
            correlation_id=correlation_id,
            method=request.method,
            route=request.url.path,
        )
        try:
            response = await call_next(request)
        finally:
            clear_request_context()

        response.headers[REQUEST_ID_HEADER] = correlation_id
        return response
