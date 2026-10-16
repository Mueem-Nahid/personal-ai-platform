from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.resume import MasterResume, ResumeVersion


class MasterResumeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, master: MasterResume) -> MasterResume:
        self._session.add(master)
        await self._session.flush()
        await self._session.refresh(master)
        return master

    async def get(self, master_id: UUID) -> MasterResume | None:
        return await self._session.get(MasterResume, master_id)

    async def get_by_profile_and_document(
        self, profile_id: UUID, document_id: UUID
    ) -> MasterResume | None:
        stmt = select(MasterResume).where(
            MasterResume.profile_id == profile_id,
            MasterResume.document_id == document_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_default(self, profile_id: UUID) -> MasterResume | None:
        stmt = select(MasterResume).where(
            MasterResume.profile_id == profile_id,
            MasterResume.is_default.is_(True),
            MasterResume.status == "active",
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_profile(self, profile_id: UUID) -> list[MasterResume]:
        stmt = (
            select(MasterResume)
            .where(MasterResume.profile_id == profile_id)
            .order_by(MasterResume.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, master: MasterResume) -> MasterResume:
        await self._session.flush()
        await self._session.refresh(master)
        return master

    async def delete(self, master: MasterResume) -> None:
        await self._session.delete(master)
        await self._session.flush()


class ResumeVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, version: ResumeVersion) -> ResumeVersion:
        self._session.add(version)
        await self._session.flush()
        await self._session.refresh(version)
        return version

    async def get(self, version_id: UUID) -> ResumeVersion | None:
        return await self._session.get(ResumeVersion, version_id)

    async def next_version_no(self, profile_id: UUID, job_id: UUID) -> int:
        stmt = select(func.coalesce(func.max(ResumeVersion.version_no), 0)).where(
            ResumeVersion.profile_id == profile_id,
            ResumeVersion.job_id == job_id,
        )
        result = await self._session.execute(stmt)
        return (result.scalar_one() or 0) + 1

    async def list_by_job_and_profile(
        self, profile_id: UUID, job_id: UUID
    ) -> list[ResumeVersion]:
        stmt = (
            select(ResumeVersion)
            .where(
                ResumeVersion.profile_id == profile_id,
                ResumeVersion.job_id == job_id,
            )
            .order_by(ResumeVersion.version_no.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self) -> list[ResumeVersion]:
        stmt = select(ResumeVersion).order_by(ResumeVersion.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, version: ResumeVersion) -> ResumeVersion:
        await self._session.flush()
        await self._session.refresh(version)
        return version

    async def delete(self, version: ResumeVersion) -> None:
        await self._session.delete(version)
        await self._session.flush()
