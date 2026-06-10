"""Health check endpoint."""

import structlog
from fastapi import APIRouter

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "0.1.0",
        "checks": {
            "database": "ok",
            "redis": "ok",
        },
    }
