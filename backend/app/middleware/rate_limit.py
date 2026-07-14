"""Simple in-memory rate limiting middleware."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import Settings
from app.core.constants import ErrorCode, REQUEST_ID_HEADER
from app.core.exceptions import error_envelope


class RateLimitMiddleware(BaseHTTPMiddleware):
    """IP-based sliding-window limits for login, AI, and general API traffic."""

    def __init__(self, app: object, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Health probes must remain reachable under load.
        if request.url.path.startswith("/health"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        method = request.method.upper()

        limit, window_seconds = self._resolve_limit(method=method, path=path)
        key = f"{client_ip}:{method}:{self._bucket(path)}"
        retry_after = self._consume(key=key, limit=limit, window_seconds=window_seconds)
        if retry_after is not None:
            correlation_id = getattr(request.state, "correlation_id", None) or request.headers.get(
                REQUEST_ID_HEADER
            )
            return JSONResponse(
                status_code=429,
                content=error_envelope(
                    code=ErrorCode.RATE_LIMITED,
                    message="Rate limit exceeded",
                    correlation_id=correlation_id,
                ),
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)

    def _resolve_limit(self, *, method: str, path: str) -> tuple[int, int]:
        if method == "POST" and path.startswith("/api/v1/auth/login"):
            return self._settings.rate_limit_login_per_15min, 15 * 60
        if path.startswith("/api/v1/ai"):
            return self._settings.rate_limit_ai_per_hour, 60 * 60
        return self._settings.rate_limit_api_per_hour, 60 * 60

    @staticmethod
    def _bucket(path: str) -> str:
        if path.startswith("/api/v1/auth/login"):
            return "auth_login"
        if path.startswith("/api/v1/ai"):
            return "ai"
        return "api"

    def _consume(self, *, key: str, limit: int, window_seconds: int) -> int | None:
        now = time.monotonic()
        threshold = now - window_seconds
        with self._lock:
            bucket = self._events[key]
            while bucket and bucket[0] <= threshold:
                bucket.popleft()
            if len(bucket) >= limit:
                retry_after = int(max(1, window_seconds - (now - bucket[0])))
                return retry_after
            bucket.append(now)
        return None
