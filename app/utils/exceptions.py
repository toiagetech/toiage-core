from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.utils.logger import get_logger

logger = get_logger("app.exceptions")


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "N/A")


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch all unhandled exceptions and return a 500."""
    rid = _request_id(request)
    logger.error(
        "Unhandled exception",
        extra={
            "request_id": rid,
            "path": str(request.url),
            "method": request.method,
            "error": str(exc),
        },
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Log HTTP exceptions and return standard error response."""
    rid = _request_id(request)
    extra = {
        "request_id": rid,
        "path": str(request.url),
        "method": request.method,
        "status_code": exc.status_code,
        "detail": str(exc.detail),
    }
    if exc.status_code >= 500:
        logger.error("HTTP 5xx error", extra=extra)
    else:
        logger.warning("HTTP 4xx error", extra=extra)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
