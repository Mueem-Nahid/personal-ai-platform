from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from models.mixins import TimestampMixin, UUIDMixin


class ResumeTemplate(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "resume_templates"

    profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=True
    )
    builtin_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    styles_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    asset_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )

    __table_args__ = (
        Index("ix_resume_templates_profile_id", "profile_id"),
        Index("ux_resume_templates_builtin_key", "builtin_key", unique=True),
    )

    @property
    def is_builtin(self) -> bool:
        return self.builtin_key is not None


class RenderJob(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "render_jobs"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("resume_templates.id", ondelete="SET NULL"), nullable=True
    )
    resume_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True
    )
    content_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    output_format: Mapped[str] = mapped_column(String(10), nullable=False)
    engine: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="queued"
    )
    minio_object_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_render_jobs_profile_id", "profile_id"),
        Index("ix_render_jobs_resume_version_id", "resume_version_id"),
        Index("ix_render_jobs_status", "status"),
    )
