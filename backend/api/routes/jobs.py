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
from services.job_service import JobService

router = APIRouter()


@router.post("/parse-url", response_model=JobPostOut, status_code=status.HTTP_201_CREATED)
async def parse_from_url(
    body: ParseUrlRequest,
    session: AsyncSession = Depends(get_session),
) -> JobPostOut:
    service = JobService(session)
    job = await service.parse_from_url(body.url)
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


@router.post("/parse-text", response_model=JobPostOut, status_code=status.HTTP_201_CREATED)
async def parse_from_text(
    body: ParseTextRequest,
    session: AsyncSession = Depends(get_session),
) -> JobPostOut:
    service = JobService(session)
    job = await service.parse_from_text(body.text, body.url)
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


@router.post("/parse-pdf", response_model=JobPostOut, status_code=status.HTTP_201_CREATED)
async def parse_from_pdf(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
) -> JobPostOut:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext != "pdf":
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    data = await file.read()
    service = JobService(session)
    job = await service.parse_from_pdf(data, file.filename)
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
