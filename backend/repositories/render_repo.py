from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.rendering import RenderJob, ResumeTemplate


class ResumeTemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, template: ResumeTemplate) -> ResumeTemplate:
        self._session.add(template)
        await self._session.flush()
        await self._session.refresh(template)
        return template

    async def get(self, template_id: UUID) -> ResumeTemplate | None:
        return await self._session.get(ResumeTemplate, template_id)

    async def get_by_builtin_key(self, builtin_key: str) -> ResumeTemplate | None:
        stmt = select(ResumeTemplate).where(ResumeTemplate.builtin_key == builtin_key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_visible(self, profile_id: UUID | None) -> list[ResumeTemplate]:
        """Built-in templates plus the profile's own templates."""
        stmt = (
            select(ResumeTemplate)
            .where(ResumeTemplate.status == "active")
            .order_by(ResumeTemplate.created_at.asc())
        )
        if profile_id is not None:
            from sqlalchemy import or_

            stmt = stmt.where(
                or_(
                    ResumeTemplate.profile_id == profile_id,
                    ResumeTemplate.profile_id.is_(None),
                )
            )
        else:
            stmt = stmt.where(ResumeTemplate.profile_id.is_(None))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def clear_defaults(self, profile_id: UUID | None) -> None:
        """Clear the default flag within one scope only.

        profile_id=None clears the global (built-in) default; a concrete
        profile_id clears that profile's own default and leaves the global
        fallback intact.
        """
        from sqlalchemy import update
        from sqlalchemy.sql.elements import ColumnElement

        conditions: list[ColumnElement[bool]] = [ResumeTemplate.is_default.is_(True)]
        if profile_id is None:
            conditions.append(ResumeTemplate.profile_id.is_(None))
        else:
            conditions.append(ResumeTemplate.profile_id == profile_id)
        await self._session.execute(
            update(ResumeTemplate).where(*conditions).values(is_default=False)
        )

    async def get_default(self, profile_id: UUID) -> ResumeTemplate | None:
        """Profile-specific default wins over the global built-in default."""
        stmt = select(ResumeTemplate).where(
            ResumeTemplate.is_default.is_(True),
            ResumeTemplate.status == "active",
            or_(
                ResumeTemplate.profile_id == profile_id,
                ResumeTemplate.profile_id.is_(None),
            ),
        )
        result = await self._session.execute(stmt)
        templates = list(result.scalars().all())
        for template in templates:
            if template.profile_id == profile_id:
                return template
        for template in templates:
            if template.profile_id is None:
                return template
        return None

    async def update(self, template: ResumeTemplate) -> ResumeTemplate:
        await self._session.flush()
        await self._session.refresh(template)
        return template

    async def delete(self, template: ResumeTemplate) -> None:
        await self._session.delete(template)
        await self._session.flush()


class RenderJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, job: RenderJob) -> RenderJob:
        self._session.add(job)
        await self._session.flush()
        await self._session.refresh(job)
        return job

    async def get(self, job_id: UUID) -> RenderJob | None:
        return await self._session.get(RenderJob, job_id)

    async def list_by_profile(self, profile_id: UUID, limit: int = 50) -> list[RenderJob]:
        stmt = (
            select(RenderJob)
            .where(RenderJob.profile_id == profile_id)
            .order_by(RenderJob.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, job: RenderJob) -> RenderJob:
        await self._session.flush()
        await self._session.refresh(job)
        return job

    async def delete(self, job: RenderJob) -> None:
        await self._session.delete(job)
        await self._session.flush()
