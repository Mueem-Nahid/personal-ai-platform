from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.profile import Profile


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, profile: Profile) -> Profile:
        self._session.add(profile)
        await self._session.flush()
        await self._session.refresh(profile)
        return await self.get_by_id(profile.id)

    async def get_by_id(self, profile_id: UUID) -> Profile | None:
        stmt = (
            select(Profile)
            .where(Profile.id == profile_id)
            .options(
                selectinload(Profile.experiences),
                selectinload(Profile.projects),
                selectinload(Profile.education),
                selectinload(Profile.skills),
                selectinload(Profile.certificates),
                selectinload(Profile.achievements),
                selectinload(Profile.publications),
                selectinload(Profile.languages),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 100, offset: int = 0) -> Sequence[Profile]:
        stmt = (
            select(Profile)
            .options(
                selectinload(Profile.experiences),
                selectinload(Profile.projects),
                selectinload(Profile.education),
                selectinload(Profile.skills),
                selectinload(Profile.certificates),
                selectinload(Profile.achievements),
                selectinload(Profile.publications),
                selectinload(Profile.languages),
            )
            .limit(limit)
            .offset(offset)
            .order_by(Profile.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def update(self, profile: Profile) -> Profile:
        await self._session.flush()
        await self._session.refresh(profile)
        return profile

    async def delete(self, profile: Profile) -> None:
        await self._session.delete(profile)
        await self._session.flush()
