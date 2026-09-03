from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.analyses import router as analyses_router
from api.routes.health import router as health_router
from api.routes.jobs import router as jobs_router
from api.routes.knowledge import router as knowledge_router
from api.routes.profile_entities import router as profile_entities_router
from api.routes.profiles import router as profiles_router
from api.routes.renders import router as renders_router
from api.routes.resumes import router as resumes_router
from api.routes.templates import router as templates_router
from core.config import settings

logger = logging.getLogger(__name__)

_STALE_MINUTES = 5
_MAX_FAILED_HOURS = 1


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await _sweep_stale_parsing_jobs()
    await _sweep_stale_analyses()
    await _sweep_stale_resume_builds()
    await _sweep_stale_renders()
    await _seed_builtin_templates()
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


async def _sweep_stale_analyses() -> None:
    from datetime import datetime, timedelta

    from sqlalchemy import update

    from core.database import SessionLocal
    from models.job_analysis import JobAnalysis

    now = datetime.now(UTC)
    stale_cutoff = now - timedelta(minutes=10)

    async with SessionLocal() as session:
        result = await session.execute(
            update(JobAnalysis)
            .where(
                JobAnalysis.status == "analyzing",
                JobAnalysis.updated_at < stale_cutoff,
            )
            .values(
                status="failed",
                error="Stranded analysis — backend restarted while analysis was running",
                updated_at=now,
            )
        )
        if result.rowcount:
            logger.info("Marked %d stale 'analyzing' rows as failed", result.rowcount)

        await session.commit()


async def _sweep_stale_resume_builds() -> None:
    try:
        from datetime import datetime, timedelta

        from sqlalchemy import update

        from core.database import SessionLocal
        from models.resume import ResumeVersion

        now = datetime.now(UTC)
        stale_cutoff = now - timedelta(minutes=10)

        async with SessionLocal() as session:
            result = await session.execute(
                update(ResumeVersion)
                .where(
                    ResumeVersion.status == "building",
                    ResumeVersion.updated_at < stale_cutoff,
                )
                .values(
                    status="failed",
                    error="Stranded build — backend restarted while build was running",
                    updated_at=now,
                )
            )
            if result.rowcount:
                logger.info("Marked %d stale 'building' resume versions as failed", result.rowcount)

            await session.commit()
    except Exception:
        logger.warning(
            "Resume stale-build sweeper skipped (migration 0006 may not be applied yet)"
        )


async def _sweep_stale_renders() -> None:
    try:
        from datetime import datetime, timedelta

        from sqlalchemy import update

        from core.database import SessionLocal
        from models.rendering import RenderJob

        now = datetime.now(UTC)
        stale_cutoff = now - timedelta(minutes=10)

        async with SessionLocal() as session:
            result = await session.execute(
                update(RenderJob)
                .where(
                    RenderJob.status.in_(["queued", "rendering"]),
                    RenderJob.updated_at < stale_cutoff,
                )
                .values(
                    status="failed",
                    error="Stranded render — backend restarted while render was pending",
                    updated_at=now,
                )
            )
            if result.rowcount:
                logger.info("Marked %d stale render jobs as failed", result.rowcount)

            await session.commit()
    except Exception:
        logger.warning(
            "Render stale-job sweeper skipped (migration 0007 may not be applied yet)"
        )


async def _seed_builtin_templates() -> None:
    try:
        from core.database import SessionLocal
        from services.template_service import TemplateService

        async with SessionLocal() as session:
            service = TemplateService(session)
            await service.seed_builtins()
    except Exception:
        logger.warning("Built-in template seeding skipped (database unavailable or unmigrated)")


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
    app.include_router(
        analyses_router,
        prefix=f"{settings.api_v1_prefix}/analyses",
        tags=["analyses"],
    )
    app.include_router(
        resumes_router,
        prefix=f"{settings.api_v1_prefix}/resumes",
        tags=["resumes"],
    )
    app.include_router(
        templates_router,
        prefix=f"{settings.api_v1_prefix}/templates",
        tags=["templates"],
    )
    app.include_router(
        renders_router,
        prefix=f"{settings.api_v1_prefix}/renders",
        tags=["renders"],
    )
    return app


app = create_app()


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": settings.app_name, "version": settings.app_version, "docs": f"{settings.api_v1_prefix}/docs"}
