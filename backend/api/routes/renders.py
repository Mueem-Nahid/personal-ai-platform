from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_session
from schemas.render import RenderJobListOut, RenderJobOut, RenderRequest
from services.render_service import RenderService
from workers.redis_pool import get_redis

router = APIRouter()


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def start_render(
    body: RenderRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    from models.profile import Profile

    profile = await session.get(Profile, body.profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    service = RenderService(session)
    try:
        job = await service.create_render_job(
            profile_id=body.profile_id,
            template_id=body.template_id,
            output_format=body.output_format,
            resume_version_id=body.resume_version_id,
            content=body.content,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    redis = await get_redis()
    await redis.enqueue_job("render_document", str(job.id))
    return {"render_job_id": str(job.id), "status": job.status}


@router.get("", response_model=RenderJobListOut)
async def list_renders(
    profile_id: UUID = Query(...),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> RenderJobListOut:
    service = RenderService(session)
    jobs = await service.list_by_profile(profile_id, limit)
    return RenderJobListOut(
        jobs=[RenderJobOut.model_validate(j) for j in jobs],
        total=len(jobs),
    )


@router.get("/{job_id}", response_model=RenderJobOut)
async def get_render(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> RenderJobOut:
    service = RenderService(session)
    job = await service.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Render job not found")
    return RenderJobOut.model_validate(job)


@router.get("/{job_id}/download")
async def download_render(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> Response:
    service = RenderService(session)
    try:
        data, filename, content_type = await service.download(job_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_render(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    service = RenderService(session)
    try:
        await service.delete(job_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
