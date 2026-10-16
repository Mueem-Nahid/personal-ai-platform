from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


TemplateFormat = Literal["html", "typst", "latex", "docx"]
OutputFormat = Literal["pdf", "docx"]


class ResumeTemplateCreate(BaseModel):
    profile_id: UUID | None = None
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    format: TemplateFormat
    source_text: str | None = None
    styles_text: str | None = None


class ResumeTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    source_text: str | None = None
    styles_text: str | None = None


class ResumeTemplateOut(ORMBase):
    id: UUID
    profile_id: UUID | None
    builtin_key: str | None
    name: str
    description: str | None
    format: TemplateFormat
    source_text: str | None
    styles_text: str | None
    asset_key: str | None
    is_default: bool
    status: str
    is_builtin: bool
    created_at: datetime
    updated_at: datetime


class ResumeTemplateListOut(BaseModel):
    templates: list[ResumeTemplateOut]
    total: int


class TemplatePreviewRequest(BaseModel):
    profile_id: UUID | None = None
    format: TemplateFormat
    source_text: str
    styles_text: str | None = None
    content: dict[str, Any] | None = None
