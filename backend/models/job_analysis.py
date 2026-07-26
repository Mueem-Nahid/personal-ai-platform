from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from models.mixins import TimestampMixin, UUIDMixin


class JobAnalysis(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "job_analyses"

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_posts.id", ondelete="CASCADE"), nullable=False
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="analyzing"
    )
    report: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(20), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(20), nullable=True)

    __table_args__ = (
        UniqueConstraint("job_id", "profile_id", name="uq_job_analyses_job_profile"),
        Index("ix_job_analyses_job_id", "job_id"),
        Index("ix_job_analyses_profile_id", "profile_id"),
        Index("ix_job_analyses_status", "status"),
    )
