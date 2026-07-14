from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.profile import (
    Achievement,
    Certificate,
    Education,
    Experience,
    Language,
    Profile,
    Project,
    Publication,
    Skill,
)
from repositories.child_entity_repo import ChildEntityRepository
from repositories.profile_repo import ProfileRepository
from schemas.profile import (
    AchievementCreate,
    AchievementUpdate,
    CertificateCreate,
    CertificateUpdate,
    EducationCreate,
    EducationUpdate,
    ExperienceCreate,
    ExperienceUpdate,
    LanguageCreate,
    LanguageUpdate,
    ProfileCreate,
    ProfileUpdate,
    ProjectCreate,
    ProjectUpdate,
    PublicationCreate,
    PublicationUpdate,
    SkillCreate,
    SkillUpdate,
)


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ProfileRepository(session)

    async def create_profile(self, data: ProfileCreate) -> Profile:
        profile = Profile(
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            location=data.location,
            title=data.title,
            summary=data.summary,
            github_url=data.github_url,
            linkedin_url=data.linkedin_url,
            website=data.website,
        )
        for exp in data.experiences:
            profile.experiences.append(Experience(**exp.model_dump()))
        for proj in data.projects:
            profile.projects.append(Project(**proj.model_dump()))
        for edu in data.education:
            profile.education.append(Education(**edu.model_dump()))
        for skill in data.skills:
            profile.skills.append(Skill(**skill.model_dump()))
        for cert in data.certificates:
            profile.certificates.append(Certificate(**cert.model_dump()))
        for ach in data.achievements:
            profile.achievements.append(Achievement(**ach.model_dump()))
        for pub in data.publications:
            profile.publications.append(Publication(**pub.model_dump()))
        for lang in data.languages:
            profile.languages.append(Language(**lang.model_dump()))
        return await self._repo.create(profile)

    async def get_profile(self, profile_id: UUID) -> Profile:
        profile = await self._repo.get_by_id(profile_id)
        if profile is None:
            raise ValueError(f"Profile {profile_id} not found")
        return profile

    async def list_profiles(self, limit: int = 100, offset: int = 0) -> Sequence[Profile]:
        return await self._repo.list_all(limit=limit, offset=offset)

    async def update_profile(self, profile_id: UUID, data: ProfileUpdate) -> Profile:
        profile = await self.get_profile(profile_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)
        return await self._repo.update(profile)

    async def delete_profile(self, profile_id: UUID) -> None:
        profile = await self.get_profile(profile_id)
        await self._repo.delete(profile)


class ChildEntityService[T]:
    """Generic service for profile child entity CRUD."""

    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self._session = session
        self._repo = ChildEntityRepository(session, model)
        self._model = model

    async def create(self, profile_id: UUID, data: object) -> T:
        entity = self._model(profile_id=profile_id, **data.model_dump())
        return await self._repo.create(entity)

    async def get(self, entity_id: UUID) -> T:
        entity = await self._repo.get_by_id(entity_id)
        if entity is None:
            raise ValueError(f"{self._model.__name__} {entity_id} not found")
        return entity

    async def list_by_profile(self, profile_id: UUID) -> Sequence[T]:
        return await self._repo.list_by_profile(profile_id)

    async def update(self, entity_id: UUID, data: object) -> T:
        entity = await self.get(entity_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(entity, key, value)
        return await self._repo.update(entity)

    async def delete(self, entity_id: UUID) -> None:
        entity = await self.get(entity_id)
        await self._repo.delete(entity)
