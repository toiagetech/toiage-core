"""Observability helpers: request ID, latency tracking, structured logging."""

import json
import time
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import get_logger

logger = get_logger("app.observability")

# Context variable for request_id - set by middleware, available app-wide.
# Previously imported from app.services.llm.manager, now defined locally
# since the LLM layer moved to the education engine.
request_id_var: ContextVar[str] = ContextVar("request_id", default="N/A")

_BODY_METHODS = {"POST", "PUT", "PATCH"}
_MAX_BODY_CAPTURE = 4096


async def _capture_request_body(request: Request) -> str | None:
    if request.method not in _BODY_METHODS:
        return None
    body_bytes = await request.body()
    if not body_bytes:
        return None
    if len(body_bytes) > _MAX_BODY_CAPTURE:
        body_str = body_bytes[:_MAX_BODY_CAPTURE].decode("utf-8", errors="replace") + "...[truncated]"
    else:
        body_str = body_bytes.decode("utf-8", errors="replace")
    async def receive() -> dict:
        return {"type": "http.request", "body": body_bytes, "more_body": False}
    request._receive = receive
    try:
        parsed = json.loads(body_str)
        return json.dumps(parsed, ensure_ascii=False)
    except (json.JSONDecodeError, ValueError):
        return body_str


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        request_body = await _capture_request_body(request)
        token = request_id_var.set(request_id)
        start = time.monotonic()
        try:
            response = await call_next(request)
            elapsed = time.monotonic() - start
            _log_request(request, response, elapsed, request_id, request_body=request_body)
            return response
        except Exception as exc:
            elapsed = time.monotonic() - start
            _log_request(request, None, elapsed, request_id, error=str(exc), request_body=request_body)
            raise
        finally:
            request_id_var.reset(token)


def _latency_bucket(ms):
    if ms < 100: return "<100ms"
    elif ms < 300: return "<300ms"
    elif ms < 1000: return "<1s"
    elif ms < 3000: return "<3s"
    elif ms < 10000: return "<10s"
    else: return ">=10s"


def _log_request(request, response, elapsed_s, request_id, error=None, request_body=None):
    elapsed_ms = round(elapsed_s * 1000, 2)
    extra = {"request_id": request_id, "method": request.method, "path": str(request.url.path), "query": str(request.url.query) if request.url.query else "", "elapsed_ms": elapsed_ms, "latency_bucket": _latency_bucket(elapsed_ms), "user_agent": request.headers.get("user-agent", ""), "content_type": request.headers.get("content-type", "")}
    if request_body: extra["request_body"] = request_body
    if response is not None:
        extra["status"] = response.status_code
        if response.status_code >= 500: logger.error("API request 5xx", extra=extra)
        elif response.status_code >= 400: logger.warning("API request 4xx", extra=extra)
        else: logger.info("API request", extra=extra)
    elif error is not None:
        extra["error"] = error
        logger.error("API request failed", extra=extra, exc_info=True)
