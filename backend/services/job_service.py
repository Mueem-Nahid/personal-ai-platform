from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from models.job import JobPost
from parsers.fetcher import fetch_url_text
from parsers.job_parser import parse_job_text
from repositories.job_repo import JobPostRepository
from services.extraction_service import ExtractionService

logger = logging.getLogger(__name__)


class JobService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = JobPostRepository(session)

    async def create_pending(
        self, text: str | None, url: str | None = None, source: str = "text"
    ) -> JobPost:
        if url:
            existing = await self._repo.get_by_url(url)
            if existing:
                return existing
        job = JobPost(url=url, source=source, status="parsing", raw_text=text)
        job = await self._repo.create(job)
        await self._session.commit()
        return job

    async def process_url_background(self, job_id: uuid.UUID, url: str) -> None:
        raw_text = await fetch_url_text(url)
        await self._complete_parse(job_id, raw_text, url)
        await self._session.commit()

    async def process_text_background(self, job_id: uuid.UUID, text: str) -> None:
        await self._complete_parse(job_id, text, None)
        await self._session.commit()

    async def process_pdf_background(self, job_id: uuid.UUID, data: bytes) -> None:
        text = ExtractionService.extract(data, "pdf")
        await self._complete_parse(job_id, text, None)
        await self._session.commit()

    async def _complete_parse(
        self, job_id: uuid.UUID, raw_text: str, url: str | None
    ) -> None:
        job = await self._repo.get(job_id)
        if not job:
            logger.error("JobPost %s not found for background processing", job_id)
            return
        if job.url is None and url:
            job.url = url
        if job.raw_text is None:
            job.raw_text = raw_text

        try:
            _, fields, status = await parse_job_text(raw_text)
            job.status = status
            if fields:
                job.title = fields.title
                job.company = fields.company
                job.location = fields.location
                job.parsed_fields = fields.model_dump()
            else:
                job.parsed_fields = {"error": "LLM parsing returned no fields"}
        except Exception as e:
            logger.exception("Processing failed for job %s", job_id)
            job.status = "failed"
            job.parsed_fields = {"error": str(e)[:500]}

        await self._repo.update(job)

    async def get(self, job_id: uuid.UUID) -> JobPost | None:
        return await self._repo.get(job_id)

    async def list_jobs(self) -> list[JobPost]:
        return await self._repo.list()

    async def delete(self, job_id: uuid.UUID) -> None:
        job = await self._repo.get(job_id)
        if job is None:
            raise ValueError(f"JobPost {job_id} not found")
        await self._repo.delete(job)
