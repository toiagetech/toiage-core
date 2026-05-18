from fastapi import FastAPI
from sqlmodel import text

from app.api.llm import router as llm_router
from app.db.session import engine

app = FastAPI(title="Toiage Core API")

app.include_router(llm_router)


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