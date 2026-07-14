from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_session
from models.profile import Achievement, Certificate, Education, Experience, Language, Project, Publication, Skill
from schemas.profile import (
    AchievementCreate,
    AchievementOut,
    AchievementUpdate,
    CertificateCreate,
    CertificateOut,
    CertificateUpdate,
    EducationCreate,
    EducationOut,
    EducationUpdate,
    ExperienceCreate,
    ExperienceOut,
    ExperienceUpdate,
    LanguageCreate,
    LanguageOut,
    LanguageUpdate,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    PublicationCreate,
    PublicationOut,
    PublicationUpdate,
    SkillCreate,
    SkillOut,
    SkillUpdate,
)
from services.profile_service import ChildEntityService

router = APIRouter()

type EntityServiceMap = dict[str, type]

_ENTITY_MODELS: dict[str, type] = {
    "experiences": Experience,
    "projects": Project,
    "education": Education,
    "skills": Skill,
    "certificates": Certificate,
    "achievements": Achievement,
    "publications": Publication,
    "languages": Language,
}


def _service_for(session: AsyncSession, model: type) -> ChildEntityService:
    return ChildEntityService(session, model)


async def _get_profile_or_404(profile_id: UUID, session: AsyncSession) -> None:
    from services.profile_service import ProfileService

    service = ProfileService(session)
    try:
        await service.get_profile(profile_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")


async def _get_entity_or_404(session: AsyncSession, model: type, entity_id: UUID):
    service = _service_for(session, model)
    try:
        return await service.get(entity_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__} not found",
        )


def _make_create_endpoint(model: type, create_schema: type, out_schema: type, path: str):
    async def endpoint(profile_id: UUID, data: create_schema, session: AsyncSession = Depends(get_session)):  # type: ignore[valid-type]
        await _get_profile_or_404(profile_id, session)
        service = _service_for(session, model)
        entity = await service.create(profile_id, data)
        return out_schema.model_validate(entity)

    endpoint.__name__ = f"create_{path}"
    return endpoint


def _make_list_endpoint(model: type, out_schema: type, path: str):
    async def endpoint(profile_id: UUID, session: AsyncSession = Depends(get_session)) -> list[out_schema]:  # type: ignore[valid-type]
        await _get_profile_or_404(profile_id, session)
        service = _service_for(session, model)
        entities = await service.list_by_profile(profile_id)
        return [out_schema.model_validate(e) for e in entities]

    endpoint.__name__ = f"list_{path}"
    return endpoint


def _make_get_endpoint(model: type, out_schema: type, path: str):
    async def endpoint(profile_id: UUID, entity_id: UUID, session: AsyncSession = Depends(get_session)):  # type: ignore[valid-type]
        await _get_profile_or_404(profile_id, session)
        entity = await _get_entity_or_404(session, model, entity_id)
        return out_schema.model_validate(entity)

    endpoint.__name__ = f"get_{path}"
    return endpoint


def _make_update_endpoint(model: type, update_schema: type, out_schema: type, path: str):
    async def endpoint(  # type: ignore[valid-type]
        profile_id: UUID, entity_id: UUID, data: update_schema, session: AsyncSession = Depends(get_session)
    ):
        await _get_profile_or_404(profile_id, session)
        service = _service_for(session, model)
        try:
            entity = await service.update(entity_id, data)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found")
        return out_schema.model_validate(entity)

    endpoint.__name__ = f"update_{path}"
    return endpoint


def _make_delete_endpoint(model: type, path: str):
    async def endpoint(profile_id: UUID, entity_id: UUID, session: AsyncSession = Depends(get_session)) -> None:
        await _get_profile_or_404(profile_id, session)
        service = _service_for(session, model)
        try:
            await service.delete(entity_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found")

    endpoint.__name__ = f"delete_{path}"
    return endpoint


_ENTITY_CONFIG = {
    "experiences": (Experience, ExperienceCreate, ExperienceUpdate, ExperienceOut),
    "projects": (Project, ProjectCreate, ProjectUpdate, ProjectOut),
    "education": (Education, EducationCreate, EducationUpdate, EducationOut),
    "skills": (Skill, SkillCreate, SkillUpdate, SkillOut),
    "certificates": (Certificate, CertificateCreate, CertificateUpdate, CertificateOut),
    "achievements": (Achievement, AchievementCreate, AchievementUpdate, AchievementOut),
    "publications": (Publication, PublicationCreate, PublicationUpdate, PublicationOut),
    "languages": (Language, LanguageCreate, LanguageUpdate, LanguageOut),
}

for _path, (_model, _create, _update, _out) in _ENTITY_CONFIG.items():
    router.add_api_route(
        f"/{{profile_id}}/{_path}",
        _make_create_endpoint(_model, _create, _out, _path),
        methods=["POST"],
        response_model=_out,
        status_code=status.HTTP_201_CREATED,
        summary=f"Create {_path[:-1]}",
    )
    router.add_api_route(
        f"/{{profile_id}}/{_path}",
        _make_list_endpoint(_model, _out, _path),
        methods=["GET"],
        response_model=list[_out],
        summary=f"List {_path}",
    )
    router.add_api_route(
        f"/{{profile_id}}/{_path}/{{entity_id}}",
        _make_get_endpoint(_model, _out, _path),
        methods=["GET"],
        response_model=_out,
        summary=f"Get {_path[:-1]}",
    )
    router.add_api_route(
        f"/{{profile_id}}/{_path}/{{entity_id}}",
        _make_update_endpoint(_model, _update, _out, _path),
        methods=["PUT"],
        response_model=_out,
        summary=f"Update {_path[:-1]}",
    )
    router.add_api_route(
        f"/{{profile_id}}/{_path}/{{entity_id}}",
        _make_delete_endpoint(_model, _path),
        methods=["DELETE"],
        status_code=status.HTTP_204_NO_CONTENT,
        summary=f"Delete {_path[:-1]}",
    )
