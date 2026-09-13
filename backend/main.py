"""
ResearchPilot AI — FastAPI Application Entry Point

Run with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Or from the backend/ directory:
    python -m uvicorn main:app --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.utils.logging_config import setup_logging

# ── Logging must be set up before importing anything else that logs ───
setup_logging(log_level=settings.LOG_LEVEL)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan event handler (replaces deprecated on_event)."""
    logger.info("=" * 60)
    logger.info("ResearchPilot AI — Backend Starting")
    logger.info("=" * 60)
    logger.info("LLM model     : {}", settings.GEMINI_MODEL)
    logger.info("Embedding     : {}", settings.EMBEDDING_MODEL)
    logger.info("Upload dir    : {}", settings.UPLOAD_DIR.resolve())
    logger.info("Chroma dir    : {}", settings.CHROMA_PERSIST_DIRECTORY.resolve())
    logger.info("Max upload    : {} MB", settings.MAX_UPLOAD_SIZE_MB)
    logger.info("CORS origins  : {}", settings.CORS_ORIGINS)
    # NOTE: GEMINI_API_KEY is intentionally NOT logged — security requirement
    logger.info("GEMINI_API_KEY: [SET — value redacted]")
    logger.info("=" * 60)
    logger.info("Backend ready. Visit http://localhost:{}/docs", settings.PORT)
    yield
    logger.info("ResearchPilot AI — Backend Shutting Down")


# ── Application factory ───────────────────────────────────────────────
app = FastAPI(
    title="ResearchPilot AI",
    description=(
        "Agentic Research Intelligence & Literature Analysis Platform. "
        "Upload a research paper and engage in grounded Q&A, structured summary, "
        "and paper insights — all powered by Gemini and local RAG."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization"],
)


# ── Health endpoint ───────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """
    Health check endpoint.
    Returns service status and active provider configuration.
    Does NOT expose the API key value.
    """
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "providers": {
            "llm": "gemini",
            "llm_model": settings.GEMINI_MODEL,
            "embeddings": "local-huggingface",
            "embedding_model": settings.EMBEDDING_MODEL,
            "vector_store": "chromadb",
        },
    }


# ── API routers ───────────────────────────────────────────────────────
from app.api.router import api_router  # noqa: E402
app.include_router(api_router, prefix="/api")
