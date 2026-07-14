from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.profile import Achievement, Certificate, Education, Experience, Language, Project, Publication, Skill

type ModelT = Experience | Project | Education | Skill | Certificate | Achievement | Publication | Language


class ChildEntityRepository[T: ModelT]:
    """Generic repository for profile child entities (experience, education, etc.)."""

    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self._session = session
        self._model = model

    async def create(self, entity: T) -> T:
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def get_by_id(self, entity_id: UUID) -> T | None:
        stmt = select(self._model).where(self._model.id == entity_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_profile(self, profile_id: UUID) -> Sequence[T]:
        stmt = select(self._model).where(self._model.profile_id == profile_id)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def update(self, entity: T) -> T:
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity: T) -> None:
        await self._session.delete(entity)
        await self._session.flush()
