from __future__ import annotations

import logging

from arq.connections import RedisSettings

from core.config import settings

logger = logging.getLogger(__name__)


async def startup(ctx: dict) -> None:
    logger.info(
        "ARQ worker starting (provider=%s model=%s)", settings.llm_provider, settings.llm_model
    )


async def shutdown(ctx: dict) -> None:
    logger.info("ARQ worker shutting down")


async def parse_url(ctx: dict, job_id: str, url: str) -> dict:
    import uuid

    from core.database import SessionLocal
    from services.job_service import JobService

    async with SessionLocal() as session:
        service = JobService(session)
        await service.process_url_background(uuid.UUID(job_id), url)
        await session.commit()
    return {"job_id": job_id, "status": "completed", "type": "url"}


async def parse_text(ctx: dict, job_id: str, text: str) -> dict:
    import uuid

    from core.database import SessionLocal
    from services.job_service import JobService

    async with SessionLocal() as session:
        service = JobService(session)
        await service.process_text_background(uuid.UUID(job_id), text)
        await session.commit()
    return {"job_id": job_id, "status": "completed", "type": "text"}


async def parse_pdf(ctx: dict, job_id: str, data_b64: str) -> dict:
    import base64
    import uuid

    from core.database import SessionLocal
    from services.job_service import JobService

    decoded = base64.b64decode(data_b64)
    async with SessionLocal() as session:
        service = JobService(session)
        await service.process_pdf_background(uuid.UUID(job_id), decoded)
        await session.commit()
    return {"job_id": job_id, "status": "completed", "type": "pdf"}


async def analyze_job(ctx: dict, analysis_id: str) -> dict:
    import uuid

    from core.database import SessionLocal
    from services.job_analysis_service import JobAnalysisService

    async with SessionLocal() as session:
        service = JobAnalysisService(session)
        await service.run_background(uuid.UUID(analysis_id))
        await session.commit()
    return {"analysis_id": analysis_id, "status": "completed", "type": "analysis"}


async def build_resume(ctx: dict, version_id: str) -> dict:
    import uuid

    from core.database import SessionLocal
    from services.resume_service import ResumeService

    async with SessionLocal() as session:
        service = ResumeService(session)
        await service.run_background(uuid.UUID(version_id))
        await session.commit()
    return {"version_id": version_id, "status": "completed", "type": "resume"}


class WorkerSettings:
    functions = [parse_url, parse_text, parse_pdf, analyze_job, build_resume]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 3
    max_tries = 3
    poll_delay = 1.0
    keep_result = 3600
    log_results = False
