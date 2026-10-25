from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

AtsCategory = Literal[
    "keyword_match",
    "action_verbs",
    "length",
    "formatting",
    "quantified_achievements",
    "missing_skills",
    "readability",
]


class AtsCheck(BaseModel):
    category: AtsCategory
    label: str
    score: int | None = Field(default=None, ge=0, le=100)
    weight: int
    summary: str


class AtsSuggestion(BaseModel):
    category: AtsCategory
    priority: Literal["high", "medium", "low"]
    message: str


class AtsReport(BaseModel):
    resume_version_id: UUID
    overall_score: int = Field(ge=0, le=100)
    checks: list[AtsCheck]
    suggestions: list[AtsSuggestion]
    matched_keywords: list[str]
    missing_keywords: list[str]
    missing_skills: list[str]
    word_count: int
    scoring_version: str
    fingerprint: str
    evaluated_at: datetime
    is_stale: bool = False
    baseline_score: int | None = None
    score_delta: int | None = None
    limitations: list[str]


class AtsRefineRequest(BaseModel):
    fingerprint: str = Field(min_length=64, max_length=64, pattern=r"^[a-f0-9]+$")
