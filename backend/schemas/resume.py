from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ResumeSection(BaseModel):
    name: str
    items: list[str] = Field(default_factory=list)


class ResumeContent(BaseModel):
    summary: str | None = None
    sections: list[ResumeSection] = Field(default_factory=list)


class MasterResumeCreate(BaseModel):
    profile_id: UUID
    document_id: UUID
    is_default: bool = False


class MasterResumeOut(ORMBase):
    id: UUID
    profile_id: UUID
    document_id: UUID
    status: str
    is_default: bool
    created_at: datetime
    updated_at: datetime


class MasterResumeListOut(BaseModel):
    resumes: list[MasterResumeOut]
    total: int


class BuildResumeRequest(BaseModel):
    profile_id: UUID
    job_id: UUID
    master_resume_id: UUID | None = None


class ResumeVersionOut(ORMBase):
    id: UUID
    profile_id: UUID
    job_id: UUID
    master_resume_id: UUID
    version_no: int
    status: str
    content: ResumeContent | None = None
    content_text: str | None = None
    error: str | None = None
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    created_at: datetime
    updated_at: datetime


class ResumeVersionListOut(BaseModel):
    versions: list[ResumeVersionOut]
    total: int


class ResumeVersionTrace(BaseModel):
    version_id: UUID
    prompt_text: str | None = None
    evidence_text: str | None = None
    raw_response: str | None = None
