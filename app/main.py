
from fastapi import FastAPI
app = FastAPI(title="Toiage Core API")


@app.get("/health")
def health():
    return {"status": "ok"}
