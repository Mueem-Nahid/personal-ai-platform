from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_session
from schemas.job_analysis import (
    AnalyzeJobRequest,
    JobAnalysisListOut,
    JobAnalysisOut,
    JobAnalysisReport,
)
from services.job_analysis_service import JobAnalysisService
from workers.redis_pool import get_redis

router = APIRouter()


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def start_analysis(
    body: AnalyzeJobRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    from models.job import JobPost
    from models.profile import Profile

    job = await session.get(JobPost, body.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job post not found")
    profile = await session.get(Profile, body.profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    service = JobAnalysisService(session)
    analysis = await service.create_pending(body.job_id, body.profile_id)
    redis = await get_redis()
    await redis.enqueue_job("analyze_job", str(analysis.id))
    return {"analysis_id": str(analysis.id), "status": "analyzing"}


@router.get("", response_model=JobAnalysisListOut)
async def list_analyses(
    job_id: UUID | None = Query(None),
    profile_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> JobAnalysisListOut:
    service = JobAnalysisService(session)
    if job_id:
        analyses = await service.list_by_job(job_id)
    elif profile_id:
        analyses = await service.list_by_profile(profile_id)
    else:
        analyses = await service.list_all()
    return JobAnalysisListOut(
        analyses=[
            JobAnalysisOut(
                id=a.id,
                job_id=a.job_id,
                profile_id=a.profile_id,
                status=a.status,
                report=JobAnalysisReport(**a.report) if a.report else None,
                error=a.error,
                provider=a.provider,
                model=a.model,
                prompt_version=a.prompt_version,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
            for a in analyses
        ],
        total=len(analyses),
    )


@router.get("/{analysis_id}", response_model=JobAnalysisOut)
async def get_analysis(
    analysis_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> JobAnalysisOut:
    service = JobAnalysisService(session)
    analysis = await service.get(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return JobAnalysisOut(
        id=analysis.id,
        job_id=analysis.job_id,
        profile_id=analysis.profile_id,
        status=analysis.status,
        report=JobAnalysisReport(**analysis.report) if analysis.report else None,
        error=analysis.error,
        provider=analysis.provider,
        model=analysis.model,
        prompt_version=analysis.prompt_version,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
    )


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_analysis(
    analysis_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    service = JobAnalysisService(session)
    try:
        await service.delete(analysis_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail="Analysis not found") from err
