from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.health import router as health_router
from api.routes.jobs import router as jobs_router
from api.routes.knowledge import router as knowledge_router
from api.routes.profile_entities import router as profile_entities_router
from api.routes.profiles import router as profiles_router
from core.config import settings

logger = logging.getLogger(__name__)

_STALE_MINUTES = 5
_MAX_FAILED_HOURS = 1


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await _sweep_stale_parsing_jobs()
    try:
        yield
    finally:
        from workers.redis_pool import close_redis

        await close_redis()


async def _sweep_stale_parsing_jobs() -> None:
    from datetime import datetime, timedelta

    from sqlalchemy import update

    from core.database import SessionLocal
    from models.job import JobPost

    now = datetime.now(UTC)
    stale_cutoff = now - timedelta(minutes=_STALE_MINUTES)
    dead_cutoff = now - timedelta(hours=_MAX_FAILED_HOURS)

    async with SessionLocal() as session:
        result = await session.execute(
            update(JobPost)
            .where(
                JobPost.status == "parsing",
                JobPost.updated_at < stale_cutoff,
            )
            .values(
                status="failed",
                parsed_fields={"error": "Stranded parse — backend restarted while job was parsing"},
                updated_at=now,
            )
        )
        if result.rowcount:
            logger.info("Marked %d stale 'parsing' jobs as failed", result.rowcount)

        result = await session.execute(
            update(JobPost)
            .where(
                JobPost.status == "parsing",
                JobPost.updated_at < dead_cutoff,
            )
            .values(
                status="failed",
                parsed_fields={"error": "Parse timed out definitively"},
                updated_at=now,
            )
        )
        if result.rowcount:
            logger.info("Marked %d dead 'parsing' jobs as failed", result.rowcount)

        await session.commit()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url=f"{settings.api_v1_prefix}/docs",
        redoc_url=f"{settings.api_v1_prefix}/redoc",
    )

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(health_router, prefix=settings.api_v1_prefix, tags=["health"])
    app.include_router(profiles_router, prefix=f"{settings.api_v1_prefix}/profiles", tags=["profiles"])
    app.include_router(
        profile_entities_router,
        prefix=f"{settings.api_v1_prefix}/profiles",
        tags=["profile-entities"],
    )
    app.include_router(
        knowledge_router,
        prefix=f"{settings.api_v1_prefix}/profiles",
        tags=["knowledge"],
    )
    app.include_router(
        jobs_router,
        prefix=f"{settings.api_v1_prefix}/jobs",
        tags=["jobs"],
    )
    return app


app = create_app()


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": settings.app_name, "version": settings.app_version, "docs": f"{settings.api_v1_prefix}/docs"}
