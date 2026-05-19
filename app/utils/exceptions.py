from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.utils.logger import get_logger

logger = get_logger("app.exceptions")


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch all unhandled exceptions and return a 500."""
    logger.error(
        "Unhandled exception",
        extra={
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
    if exc.status_code >= 500:
        logger.error(
            "HTTP 5xx error",
            extra={
                "path": str(request.url),
                "method": request.method,
                "status_code": exc.status_code,
                "detail": str(exc.detail),
            },
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )