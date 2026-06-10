"""arq task queue configuration."""

from arq.connections import RedisSettings

from app.core.config import get_settings

settings = get_settings()


async def _heartbeat(ctx: dict) -> str:
    """Placeholder heartbeat task — keeps the worker alive until real jobs are registered."""
    return "ok"


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    functions = [_heartbeat]
    max_jobs = 20
    job_timeout = 3600
    keep_result = 3600
    poll_delay = 0.5
    allow_abort_jobs = True
    queue_name = "arq:queue"
    high_priority_queue = "arq:queue:high"


DEFAULT_QUEUE = "arq:queue"
HIGH_PRIORITY_QUEUE = "arq:queue:high"
