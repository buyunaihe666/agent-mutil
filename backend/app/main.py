"""NEXUS AI FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agents import router as agents_router
from app.api.health import router as health_router
from app.api.orchestration import router as orchestration_router
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

    # Initialize database tables on first startup
    try:
        from app.core.database import init_db
        await init_db()
        logger.info("Database tables initialized")
    except Exception:
        logger.debug("Database tables likely already exist — skipping init")

    # Start monitoring collection with WebSocket push
    from app.core.monitor_service import monitor_service
    from app.core.ws import ws_manager
    await monitor_service.start_collection(interval=5, ws_manager=ws_manager)

    # Recover any orchestration plans interrupted by a previous crash
    try:
        from app.core.orchestration_engine import orchestration_engine
        recovered = await orchestration_engine.recover_from_db()
        if recovered:
            logger.info("Orchestration crash recovery completed", recovered_plans=recovered)
        else:
            logger.debug("No crashed plans to recover")
    except Exception:
        logger.debug("Orchestration crash recovery not applicable (DB may not be ready)")

    # Initialize MetaAgentRouter
    try:
        from app.core.meta_agent_router import MetaAgentRouter, meta_agent_router as _mar_singleton
        import app.core.meta_agent_router as _mar_module
        from app.core.agent_service import agent_store as _as
        import app.core.llm_gateway as _lgw
        _mar_module.meta_agent_router = MetaAgentRouter(
            agent_store=_as,
            orchestration_engine=orchestration_engine,
            llm_gateway=_lgw,
        )
        logger.info("MetaAgentRouter initialized")
    except Exception as e:
        logger.warning("MetaAgentRouter initialization skipped", error=str(e))

    yield

    logger.info("NEXUS AI shutting down...")
    try:
        await monitor_service.stop_collection()
    except Exception:
        pass
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
    app.include_router(orchestration_router, prefix="/api", tags=["Orchestration"])
    app.include_router(ws_router, tags=["WebSocket"])

    register_exception_handlers(app)

    return app


app = create_app()
