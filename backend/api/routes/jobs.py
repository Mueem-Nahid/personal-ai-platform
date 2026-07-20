from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_session
from core.database import SessionLocal
from schemas.job import (
    JobParsedFields,
    JobPostListOut,
    JobPostOut,
    ParseTextRequest,
    ParseUrlRequest,
)
from services.job_service import JobService

router = APIRouter()

_background_tasks: set[asyncio.Task] = set()


@router.post("/parse-url", status_code=status.HTTP_202_ACCEPTED)
async def parse_from_url(
    body: ParseUrlRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = JobService(session)
    job = await service.create_pending(text=None, url=body.url, source="url")
    task = asyncio.create_task(_process_url_background(job.id, body.url))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return {"job_id": str(job.id), "status": "parsing"}


@router.post("/parse-text", status_code=status.HTTP_202_ACCEPTED)
async def parse_from_text(
    body: ParseTextRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = JobService(session)
    job = await service.create_pending(text=body.text, url=body.url, source="text")
    task = asyncio.create_task(_process_text_background(job.id, body.text))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
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
    service = JobService(session)
    job = await service.create_pending(text=None, url=None, source="pdf")
    task = asyncio.create_task(_process_pdf_background(job.id, data))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
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


async def _process_url_background(job_id: UUID, url: str) -> None:
    async with SessionLocal() as session:
        service = JobService(session)
        await service.process_url_background(job_id, url)


async def _process_text_background(job_id: UUID, text: str) -> None:
    async with SessionLocal() as session:
        service = JobService(session)
        await service.process_text_background(job_id, text)


async def _process_pdf_background(job_id: UUID, data: bytes) -> None:
    async with SessionLocal() as session:
        service = JobService(session)
        await service.process_pdf_background(job_id, data)
