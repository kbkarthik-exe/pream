import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from backend.app.api.v1.router import api_router
from backend.app.core.config import settings
from backend.app.db.init_db import init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("aicf")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context for initialization and teardown."""
    try:
        await init_db()
        logger.info("Database schemas initialized.")
    except Exception as exc:
        logger.warning("Database auto-init deferred or failed: %s", exc)

    try:
        from backend.app.ml.text import text_detector
        text_detector.load_model()
    except Exception as exc:
        logger.warning("Text detector preloading deferred: %s", exc)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Backend API for forensic verification across text, image, audio, and video content."
    ),
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "platform": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "status": "operational",
        "version": settings.VERSION,
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
    }
