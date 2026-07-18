from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.job import JobPost


class JobPostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, job: JobPost) -> JobPost:
        self._session.add(job)
        await self._session.flush()
        await self._session.refresh(job)
        return job

    async def get(self, job_id: UUID) -> JobPost | None:
        return await self._session.get(JobPost, job_id)

    async def get_by_url(self, url: str) -> JobPost | None:
        if not url:
            return None
        stmt = select(JobPost).where(JobPost.url == url)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self) -> list[JobPost]:
        stmt = select(JobPost).order_by(JobPost.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, job: JobPost) -> JobPost:
        await self._session.flush()
        await self._session.refresh(job)
        return job

    async def delete(self, job: JobPost) -> None:
        await self._session.delete(job)
        await self._session.flush()
