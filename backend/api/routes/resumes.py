from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_session
from schemas.render import ResumeContentUpdate
from schemas.resume import (
    BuildResumeRequest,
    MasterResumeCreate,
    MasterResumeListOut,
    MasterResumeOut,
    ResumeContent,
    ResumeVersionListOut,
    ResumeVersionOut,
    ResumeVersionTrace,
)
from services.resume_service import ResumeService
from workers.redis_pool import get_redis

router = APIRouter()


@router.post("/master", status_code=status.HTTP_201_CREATED, response_model=MasterResumeOut)
async def designate_master_resume(
    body: MasterResumeCreate,
    session: AsyncSession = Depends(get_session),
) -> MasterResumeOut:
    from models.knowledge import Document
    from models.profile import Profile

    profile = await session.get(Profile, body.profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    doc = await session.get(Document, body.document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    service = ResumeService(session)
    try:
        master = await service.designate_master(
            body.profile_id, body.document_id, body.is_default
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    return MasterResumeOut.model_validate(master)


@router.get("/master", response_model=MasterResumeListOut)
async def list_master_resumes(
    profile_id: UUID = Query(...),
    session: AsyncSession = Depends(get_session),
) -> MasterResumeListOut:
    service = ResumeService(session)
    resumes = await service.list_master_resumes(profile_id)
    return MasterResumeListOut(
        resumes=[MasterResumeOut.model_validate(r) for r in resumes],
        total=len(resumes),
    )


@router.delete("/master/{master_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def remove_master_resume(
    master_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    service = ResumeService(session)
    try:
        await service.remove_master_resume(master_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def start_build(
    body: BuildResumeRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str | int]:
    from models.job import JobPost
    from models.profile import Profile

    job = await session.get(JobPost, body.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job post not found")
    profile = await session.get(Profile, body.profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    service = ResumeService(session)
    try:
        version = await service.create_pending_build(
            body.profile_id, body.job_id, body.master_resume_id
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    redis = await get_redis()
    await redis.enqueue_job("build_resume", str(version.id))
    return {
        "resume_version_id": str(version.id),
        "version_no": version.version_no,
        "status": "building",
    }


@router.get("", response_model=ResumeVersionListOut)
async def list_versions(
    profile_id: UUID = Query(...),
    job_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> ResumeVersionListOut:
    service = ResumeService(session)
    if job_id:
        versions = await service.list_by_job_and_profile(profile_id, job_id)
    else:
        versions = await service.list_all()
    return ResumeVersionListOut(
        versions=[
            ResumeVersionOut(
                id=v.id,
                profile_id=v.profile_id,
                job_id=v.job_id,
                master_resume_id=v.master_resume_id,
                version_no=v.version_no,
                status=v.status,
                content=ResumeContent(**v.content_json) if v.content_json else None,
                content_text=v.content_text,
                error=v.error,
                provider=v.provider,
                model=v.model,
                prompt_version=v.prompt_version,
                created_at=v.created_at,
                updated_at=v.updated_at,
            )
            for v in versions
        ],
        total=len(versions),
    )


@router.get("/{version_id}/trace", response_model=ResumeVersionTrace)
async def get_version_trace(
    version_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> ResumeVersionTrace:
    service = ResumeService(session)
    version = await service.get(version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Resume version not found")
    return ResumeVersionTrace(
        version_id=version.id,
        prompt_text=version.prompt_text,
        evidence_text=version.evidence_text,
        raw_response=version.raw_response,
    )


@router.get("/{version_id}", response_model=ResumeVersionOut)
async def get_version(
    version_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> ResumeVersionOut:
    service = ResumeService(session)
    version = await service.get(version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Resume version not found")
    return ResumeVersionOut(
        id=version.id,
        profile_id=version.profile_id,
        job_id=version.job_id,
        master_resume_id=version.master_resume_id,
        version_no=version.version_no,
        status=version.status,
        content=ResumeContent(**version.content_json) if version.content_json else None,
        content_text=version.content_text,
        error=version.error,
        provider=version.provider,
        model=version.model,
        prompt_version=version.prompt_version,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


@router.put("/{version_id}/content", response_model=ResumeVersionOut)
async def update_version_content(
    version_id: UUID,
    body: ResumeContentUpdate,
    session: AsyncSession = Depends(get_session),
) -> ResumeVersionOut:
    service = ResumeService(session)
    try:
        version = await service.update_content(version_id, body.content)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    return ResumeVersionOut(
        id=version.id,
        profile_id=version.profile_id,
        job_id=version.job_id,
        master_resume_id=version.master_resume_id,
        version_no=version.version_no,
        status=version.status,
        content=ResumeContent(**version.content_json) if version.content_json else None,
        content_text=version.content_text,
        error=version.error,
        provider=version.provider,
        model=version.model,
        prompt_version=version.prompt_version,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


@router.delete("/{version_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_version(
    version_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    service = ResumeService(session)
    try:
        await service.delete(version_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail="Resume version not found") from err
