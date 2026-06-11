"""NEXUS AI FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agents import router as agents_router
from app.api.health import router as health_router
from app.api.ws import router as ws_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.middleware.error_handler import register_exception_handlers

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    setup_logging()
    settings = get_settings()
    logger.info("NEXUS AI starting...", env=settings.APP_ENV)

    yield

    logger.info("NEXUS AI shutting down...")
    try:
        from app.core.database import engine
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception:
        pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="NEXUS AI",
        description="Multi-Agent AI Collaboration Platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api", tags=["Health"])
    app.include_router(agents_router, prefix="/api", tags=["Agents"])
    app.include_router(ws_router, tags=["WebSocket"])

    register_exception_handlers(app)

    return app


app = create_app()
