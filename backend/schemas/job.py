from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class JobParsedFields(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    salary: str | None = None
    experience: str | None = None
    employment_type: str | None = None
    requirements: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)


class JobPostOut(ORMBase):
    id: UUID
    url: str | None = None
    title: str | None = None
    company: str | None = None
    location: str | None = None
    source: str
    status: str
    raw_text: str | None = None
    parsed_fields: JobParsedFields | None = None
    created_at: datetime
    updated_at: datetime


class JobPostListOut(BaseModel):
    jobs: list[JobPostOut]
    total: int


class ParseUrlRequest(BaseModel):
    url: str = Field(..., min_length=5)


class ParseTextRequest(BaseModel):
    text: str = Field(..., min_length=50)
    url: str | None = None
