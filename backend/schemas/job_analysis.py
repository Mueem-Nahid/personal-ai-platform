from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class JobAnalysisReport(BaseModel):
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    adjacent_strengths: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    experience_fit: str | None = None
    culture_signals: list[str] = Field(default_factory=list)
    ats_score: int | None = None
    interview_difficulty: str | None = None
    company_summary: str | None = None
    likely_interview_topics: list[str] = Field(default_factory=list)
    fit_score: int | None = None
    recommendation: str | None = None
    justification: str | None = None


class JobAnalysisOut(ORMBase):
    id: UUID
    job_id: UUID
    profile_id: UUID
    status: str
    report: JobAnalysisReport | None = None
    error: str | None = None
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    created_at: datetime
    updated_at: datetime


class JobAnalysisListOut(BaseModel):
    analyses: list[JobAnalysisOut]
    total: int


class AnalyzeJobRequest(BaseModel):
    job_id: UUID
    profile_id: UUID
