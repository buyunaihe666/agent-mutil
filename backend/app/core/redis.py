"""Redis connection pool and client configuration."""

from typing import Optional

import redis.asyncio as aioredis
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)

redis_pool: Optional[aioredis.ConnectionPool] = None


async def init_redis() -> None:
    global redis_pool
    settings = get_settings()
    redis_pool = aioredis.ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=20,
        decode_responses=True,
    )
    logger.info("Redis connection pool created")


async def get_redis() -> aioredis.Redis:
    global redis_pool
    if redis_pool is None:
        await init_redis()
    return aioredis.Redis(connection_pool=redis_pool)


async def close_redis() -> None:
    global redis_pool
    if redis_pool:
        await redis_pool.disconnect()
        redis_pool = None
        logger.info("Redis connection pool closed")
