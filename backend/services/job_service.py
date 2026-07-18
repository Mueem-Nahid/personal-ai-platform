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

    async def parse_from_url(self, url: str) -> JobPost:
        existing = await self._repo.get_by_url(url)
        if existing:
            return existing

        job = JobPost(url=url, source="url", status="parsing")
        job = await self._repo.create(job)

        raw_text = await fetch_url_text(url)
        job.raw_text = raw_text

        if not raw_text.strip():
            job.status = "failed"
            return await self._repo.update(job)

        return await self._complete_parse(job, raw_text)

    async def parse_from_text(self, text: str, url: str | None = None) -> JobPost:
        if url:
            existing = await self._repo.get_by_url(url)
            if existing:
                return existing

        job = JobPost(url=url, source="text", status="parsing", raw_text=text)
        job = await self._repo.create(job)

        return await self._complete_parse(job, text)

    async def parse_from_pdf(self, data: bytes, filename: str) -> JobPost:
        text = ExtractionService.extract(data, "pdf")
        job = JobPost(source="pdf", status="parsing", raw_text=text)
        job = await self._repo.create(job)
        return await self._complete_parse(job, text)

    async def _complete_parse(self, job: JobPost, raw_text: str) -> JobPost:
        try:
            _, fields, status = await parse_job_text(raw_text)
            job.status = status
            if fields:
                job.title = fields.title
                job.company = fields.company
                job.location = fields.location
                job.parsed_fields = fields.model_dump()
        except Exception:
            logger.exception("Processing failed for job %s", job.id)
            job.status = "failed"

        return await self._repo.update(job)

    async def get(self, job_id: uuid.UUID) -> JobPost | None:
        return await self._repo.get(job_id)

    async def list_jobs(self) -> list[JobPost]:
        return await self._repo.list()

    async def delete(self, job_id: uuid.UUID) -> None:
        job = await self._repo.get(job_id)
        if job is None:
            raise ValueError(f"JobPost {job_id} not found")
        await self._repo.delete(job)
