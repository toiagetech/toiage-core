from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlmodel import text

from app.api.activities import router as activities_router
from app.api.children import router as children_router
from app.api.parents import router as parents_router
from app.api.stories import router as stories_router
from app.api.uploads import router as uploads_router
from app.api.science_projects import router as science_projects_router
from app.api.teacher_assistant import router as teacher_assistant_router
from app.api.prototype_management import router as prototype_router
from app.core.config import settings
from app.db.session import engine
from app.utils.exceptions import global_exception_handler, http_exception_handler
from app.utils.observability import ObservabilityMiddleware
from app.utils.security import (
    RateLimitMiddleware,
    RequestSizeLimitMiddleware,
    setup_cors,
)


def _normalize_prefix(prefix: str) -> str:
    """Normalize the API prefix to a non-empty, slash-prefixed, no-trailing-slash form.

    Returns "" when the app should be served at the root (no prefix).
    """
    p = (prefix or "").strip()
    if p in ("", "/"):
        return ""
    if not p.startswith("/"):
        p = "/" + p
    return p.rstrip("/")


# --- API app (routers, middleware, docs) ---
app = FastAPI(
    title="Toiage Core — Educational Intelligence Platform",
    description="API for generating curriculum-aligned science projects, assessments, and educational content for CBSE classes 6-8.",
    version="2.0.0",
)

# --- CORS (allows frontend/mobile access) ---
setup_cors(app)

# --- Security middleware chain (order matters: auth → rate limit → size → observability) ---
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(ObservabilityMiddleware)

# --- Exception handlers ---
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

app.include_router(children_router)
app.include_router(parents_router)
app.include_router(stories_router)
app.include_router(activities_router)
app.include_router(uploads_router)
app.include_router(science_projects_router)
app.include_router(teacher_assistant_router)
app.include_router(prototype_router)

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


# --- Root app: mounts the API app under a configurable path prefix ---
# Default: http://localhost:8000/toiage-core/  (docs at /toiage-core/docs)
# To serve at the root instead, set API_PREFIX="" (or "/") in .env and run
# `uvicorn app.main:app` (or keep using root_app — it falls back to `app`).
API_PREFIX = _normalize_prefix(settings.API_PREFIX)

if API_PREFIX:
    root_app = FastAPI(
        title="Toiage Core — Root",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    # Mount the full API app (with its own /docs, /openapi.json) under the prefix.
    root_app.mount(API_PREFIX, app)

    @root_app.get("/", include_in_schema=False)
    def _root_index():
        """Redirect browser hits to the root over to the prefixed docs."""
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url=f"{API_PREFIX}/docs")

    @root_app.get("/health", include_in_schema=False)
    def _root_health():
        return {"status": "ok", "api_prefix": API_PREFIX}
else:
    # No prefix configured — serve the API app directly at the root.
    root_app = app
