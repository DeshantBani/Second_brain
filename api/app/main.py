import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.db import owner_engine
from app.routers import addin, admin, auth, documents, matters, query

logging.basicConfig(level=logging.INFO)

settings = get_settings()

app = FastAPI(title="Second Brain API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # single self-hosted deployment for this pass - see build plan Section 2
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(matters.router)
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(admin.router)
app.include_router(addin.router)


@app.get("/health")
def health():
    """Unauthenticated - the frontend polls this before login to decide whether to
    show the degraded-mode banner (no Gemini key configured / not reachable)."""
    db_ok = True
    try:
        with owner_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "llm_configured": settings.llm_configured,
        "llm_provider": "gemini",
        "case_law_provider": settings.case_law_provider,
        "db_ok": db_ok,
    }
