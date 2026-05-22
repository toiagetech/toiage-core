"""API Security Foundation.

Provides:
- CORS configuration
- Request body size validation
- In-memory rate limiting (sliding window)
- Upload size enforcement
"""

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("app.security")

# ---- CORS ----

def setup_cors(app: FastAPI) -> None:
    """Configure CORS middleware for frontend/mobile access.

    In production, restrict origins to your frontend domain.
    """
    allowed_origins = settings.CORS_ALLOWED_ORIGINS
    if not allowed_origins or allowed_origins == ["*"]:
        logger.warning(
            "CORS configured with wildcard origin — restrict in production",
            extra={"allowed_origins": allowed_origins},
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600,  # 10 min preflight cache
    )
    logger.info("CORS middleware configured", extra={"allowed_origins": allowed_origins})


# ---- Request body size limit ----

_MAX_BODY_SIZE = settings.MAX_REQUEST_BODY_SIZE_BYTES


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with body larger than MAX_REQUEST_BODY_SIZE_BYTES.

    This catches oversized JSON payloads before they hit route handlers.
    FastAPI's default request body size is unlimited, so this is a required safety layer.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > _MAX_BODY_SIZE:
                    logger.warning(
                        "Request body too large",
                        extra={
                            "method": request.method,
                            "path": str(request.url.path),
                            "content_length": size,
                            "max_allowed": _MAX_BODY_SIZE,
                        },
                    )
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=413,
                        content={"detail": f"Request body too large. Max: {_MAX_BODY_SIZE} bytes"},
                    )
            except (ValueError, TypeError):
                pass

        return await call_next(request)


# ---- Rate limiting (in-memory sliding window) ----

@dataclass
class _RateBucket:
    """Sliding window rate limit bucket per client IP."""
    timestamps: list[float] = field(default_factory=list)


# Limits: (max_requests, window_seconds)
_RATE_LIMITS: list[tuple[int, int]] = [
    (60, 60),    # 60 requests per minute
    (200, 300),  # 200 requests per 5 minutes
]

# Per-IP buckets — in production, use Redis
_buckets: dict[str, list[_RateBucket]] = defaultdict(lambda: [_RateBucket() for _ in _RATE_LIMITS])


def _check_rate_limit(client_ip: str) -> tuple[bool, int]:
    """Check if the client IP has exceeded rate limits.

    Returns:
        (is_allowed: bool, retry_after_seconds: int)
    """
    now = time.monotonic()
    buckets = _buckets[client_ip]

    for i, (max_req, window_sec) in enumerate(_RATE_LIMITS):
        bucket = buckets[i]
        # Prune expired timestamps
        cutoff = now - window_sec
        bucket.timestamps = [t for t in bucket.timestamps if t > cutoff]

        if len(bucket.timestamps) >= max_req:
            # Client is rate limited — return seconds until oldest expires
            retry_after = int(bucket.timestamps[0] + window_sec - now) + 1
            return False, retry_after

        bucket.timestamps.append(now)

    return True, 0


def _extract_client_ip(request: Request) -> str:
    """Extract client IP from headers or connection info."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    client = request.client
    if client:
        return client.host
    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory sliding window rate limiter per client IP.

    Limits are configured in _RATE_LIMITS. The strictest limit applies first.
    Returns 429 with Retry-After header when exceeded.
    Uses X-Forwarded-For or X-Real-IP for client identity behind proxies.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # Skip rate limiting for health/static endpoints
        path = request.url.path
        if path in ("/health", "/db-health") or path.startswith("/uploads/files/"):
            return await call_next(request)

        client_ip = _extract_client_ip(request)
        allowed, retry_after = _check_rate_limit(client_ip)

        if not allowed:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "client_ip": client_ip,
                    "method": request.method,
                    "path:": path,
                    "retry_after": retry_after,
                },
            )
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"detail": f"Too many requests. Retry after {retry_after} seconds."},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)