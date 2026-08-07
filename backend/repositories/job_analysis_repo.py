from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.job_analysis import JobAnalysis


class JobAnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, analysis: JobAnalysis) -> JobAnalysis:
        self._session.add(analysis)
        await self._session.flush()
        await self._session.refresh(analysis)
        return analysis

    async def get(self, analysis_id: UUID) -> JobAnalysis | None:
        return await self._session.get(JobAnalysis, analysis_id)

    async def get_by_job_and_profile(
        self, job_id: UUID, profile_id: UUID
    ) -> JobAnalysis | None:
        stmt = select(JobAnalysis).where(
            JobAnalysis.job_id == job_id,
            JobAnalysis.profile_id == profile_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_job(self, job_id: UUID) -> list[JobAnalysis]:
        stmt = (
            select(JobAnalysis)
            .where(JobAnalysis.job_id == job_id)
            .order_by(JobAnalysis.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_profile(self, profile_id: UUID) -> list[JobAnalysis]:
        stmt = (
            select(JobAnalysis)
            .where(JobAnalysis.profile_id == profile_id)
            .order_by(JobAnalysis.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self) -> list[JobAnalysis]:
        stmt = select(JobAnalysis).order_by(JobAnalysis.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, analysis: JobAnalysis) -> JobAnalysis:
        await self._session.flush()
        await self._session.refresh(analysis)
        return analysis

    async def delete(self, analysis: JobAnalysis) -> None:
        await self._session.delete(analysis)
        await self._session.flush()
