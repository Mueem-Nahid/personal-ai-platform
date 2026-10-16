from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from schemas.resume import ResumeContent
from schemas.template import OutputFormat


class RenderRequest(BaseModel):
    profile_id: UUID
    template_id: UUID
    output_format: OutputFormat = "pdf"
    resume_version_id: UUID | None = None
    content: ResumeContent | None = None


class RenderJobOut(BaseModel):
    id: UUID
    profile_id: UUID
    template_id: UUID | None
    resume_version_id: UUID | None
    output_format: str
    engine: str | None
    status: str
    filename: str | None
    file_size_bytes: int | None
    error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RenderJobListOut(BaseModel):
    jobs: list[RenderJobOut]
    total: int


class RenderFormatCapability(BaseModel):
    format: str
    engine: str
    output: str
    available: bool
    reason: str | None = None


class RenderFormatsOut(BaseModel):
    formats: list[RenderFormatCapability]


class PdfImportOut(BaseModel):
    content: ResumeContent
    name: str | None = None
    title: str | None = None
    contact: str | None = None


class ResumeContentUpdate(BaseModel):
    content: ResumeContent
