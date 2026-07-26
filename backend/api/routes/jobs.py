from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_session
from schemas.job import (
    JobParsedFields,
    JobPostListOut,
    JobPostOut,
    ParseTextRequest,
    ParseUrlRequest,
)
from services.extraction_service import ExtractionService
from services.job_service import JobService
from workers.redis_pool import get_redis

router = APIRouter()


@router.post("/parse-url", status_code=status.HTTP_202_ACCEPTED)
async def parse_from_url(
    body: ParseUrlRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = JobService(session)
    job = await service.create_pending(text=None, url=body.url, source="url")
    redis = await get_redis()
    await redis.enqueue_job("parse_url", str(job.id), body.url)
    return {"job_id": str(job.id), "status": "parsing"}


@router.post("/parse-text", status_code=status.HTTP_202_ACCEPTED)
async def parse_from_text(
    body: ParseTextRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = JobService(session)
    job = await service.create_pending(text=body.text, url=body.url, source="text")
    redis = await get_redis()
    await redis.enqueue_job("parse_text", str(job.id), body.text)
    return {"job_id": str(job.id), "status": "parsing"}


@router.post("/parse-pdf", status_code=status.HTTP_202_ACCEPTED)
async def parse_from_pdf(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext != "pdf":
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    data = await file.read()
    text = ExtractionService.extract(data, "pdf")
    service = JobService(session)
    job = await service.create_pending(text=text, url=None, source="pdf")
    redis = await get_redis()
    await redis.enqueue_job("parse_text", str(job.id), text)
    return {"job_id": str(job.id), "status": "parsing"}


@router.get("/", response_model=JobPostListOut)
async def list_jobs(
    session: AsyncSession = Depends(get_session),
) -> JobPostListOut:
    service = JobService(session)
    jobs = await service.list_jobs()
    return JobPostListOut(
        jobs=[
            JobPostOut(
                id=j.id,
                url=j.url,
                title=j.title,
                company=j.company,
                location=j.location,
                source=j.source,
                status=j.status,
                raw_text=j.raw_text,
                parsed_fields=JobParsedFields(**j.parsed_fields) if j.parsed_fields else None,
                created_at=j.created_at,
                updated_at=j.updated_at,
            )
            for j in jobs
        ],
        total=len(jobs),
    )


@router.get("/{job_id}", response_model=JobPostOut)
async def get_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> JobPostOut:
    service = JobService(session)
    job = await service.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job post not found")
    return JobPostOut(
        id=job.id,
        url=job.url,
        title=job.title,
        company=job.company,
        location=job.location,
        source=job.source,
        status=job.status,
        raw_text=job.raw_text,
        parsed_fields=JobParsedFields(**job.parsed_fields) if job.parsed_fields else None,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    service = JobService(session)
    try:
        await service.delete(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job post not found")
