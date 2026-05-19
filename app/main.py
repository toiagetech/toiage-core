import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from sqlmodel import text

from app.api.activities import router as activities_router
from app.api.llm import router as llm_router
from app.api.stories import router as stories_router
from app.api.uploads import router as uploads_router
from app.core.config import settings
from app.db.session import engine
from app.utils.exceptions import global_exception_handler, http_exception_handler
from app.utils.logger import get_logger

logger = get_logger("app", level=settings.LOG_LEVEL)

app = FastAPI(title="Toiage Core API")

# --- Exception handlers ---
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# --- Request logging middleware ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    elapsed = time.monotonic() - start
    logger.info(
        "API request",
        extra={
            "method": request.method,
            "path": str(request.url.path),
            "status": response.status_code,
            "elapsed_ms": round(elapsed * 1000, 2),
        },
    )
    return response


app.include_router(llm_router)
app.include_router(stories_router)
app.include_router(activities_router)
app.include_router(uploads_router)

# Mount uploads directory for serving uploaded files
uploads_path = Path(settings.UPLOAD_DIR)
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads/files", StaticFiles(directory=str(uploads_path)), name="uploads")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-health")
def db_health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"database": "connected"}
    except Exception:
        return {"database": "disconnected"}