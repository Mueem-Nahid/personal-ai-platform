from __future__ import annotations

import logging

from arq.connections import ArqRedis, RedisSettings, create_pool

from core.config import settings

logger = logging.getLogger(__name__)

_arq_redis: ArqRedis | None = None


async def get_redis() -> ArqRedis:
    global _arq_redis
    if _arq_redis is None:
        redis_settings = RedisSettings.from_dsn(settings.redis_url)
        _arq_redis = await create_pool(redis_settings)
        logger.info("ARQ Redis pool connected to %s", settings.redis_url)
    return _arq_redis


async def close_redis() -> None:
    global _arq_redis
    if _arq_redis is not None:
        await _arq_redis.close()
        _arq_redis = None
        logger.info("ARQ Redis pool closed")
