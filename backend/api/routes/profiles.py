from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_session
from schemas.profile import ProfileCreate, ProfileOut, ProfileUpdate
from services.profile_service import ProfileService

router = APIRouter()


@router.post("", response_model=ProfileOut, status_code=status.HTTP_201_CREATED)
async def create_profile(data: ProfileCreate, session: AsyncSession = Depends(get_session)) -> ProfileOut:
    service = ProfileService(session)
    profile = await service.create_profile(data)
    return ProfileOut.model_validate(profile)


@router.get("", response_model=list[ProfileOut])
async def list_profiles(
    limit: int = 100, offset: int = 0, session: AsyncSession = Depends(get_session)
) -> list[ProfileOut]:
    service = ProfileService(session)
    profiles = await service.list_profiles(limit=limit, offset=offset)
    return [ProfileOut.model_validate(p) for p in profiles]


@router.get("/{profile_id}", response_model=ProfileOut)
async def get_profile(profile_id: UUID, session: AsyncSession = Depends(get_session)) -> ProfileOut:
    service = ProfileService(session)
    try:
        profile = await service.get_profile(profile_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return ProfileOut.model_validate(profile)


@router.put("/{profile_id}", response_model=ProfileOut)
async def update_profile(
    profile_id: UUID, data: ProfileUpdate, session: AsyncSession = Depends(get_session)
) -> ProfileOut:
    service = ProfileService(session)
    try:
        profile = await service.update_profile(profile_id, data)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return ProfileOut.model_validate(profile)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_profile(profile_id: UUID, session: AsyncSession = Depends(get_session)) -> None:
    service = ProfileService(session)
    try:
        await service.delete_profile(profile_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
