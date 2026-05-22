"""Observability helpers: request ID, latency tracking, structured logging."""

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.llm.manager import request_id_var
from app.utils.logger import get_logger

logger = get_logger("app.observability")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware that adds request_id and enriches request logging."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Propagate request_id to LLM manager via contextvar
        token = request_id_var.set(request_id)
        start = time.monotonic()
        try:
            response = await call_next(request)
            elapsed = time.monotonic() - start
            _log_request(request, response, elapsed, request_id)
            return response
        except Exception as exc:
            elapsed = time.monotonic() - start
            _log_request(request, None, elapsed, request_id, error=str(exc))
            raise
        finally:
            request_id_var.reset(token)


def _latency_bucket(ms: float) -> str:
    if ms < 100:
        return "<100ms"
    elif ms < 300:
        return "<300ms"
    elif ms < 1000:
        return "<1s"
    elif ms < 3000:
        return "<3s"
    elif ms < 10000:
        return "<10s"
    else:
        return ">=10s"


def _log_request(
    request: Request,
    response: Response | None,
    elapsed_s: float,
    request_id: str,
    error: str | None = None,
) -> None:
    elapsed_ms = round(elapsed_s * 1000, 2)
    extra = {
        "request_id": request_id,
        "method": request.method,
        "path": str(request.url.path),
        "query": str(request.url.query) if request.url.query else "",
        "elapsed_ms": elapsed_ms,
        "latency_bucket": _latency_bucket(elapsed_ms),
        "user_agent": request.headers.get("user-agent", ""),
        "content_type": request.headers.get("content-type", ""),
    }

    if response is not None:
        extra["status"] = response.status_code
        if response.status_code >= 500:
            logger.error("API request 5xx", extra=extra)
        elif response.status_code >= 400:
            logger.warning("API request 4xx", extra=extra)
        else:
            logger.info("API request", extra=extra)
    elif error is not None:
        extra["error"] = error
        logger.error("API request failed", extra=extra, exc_info=True)