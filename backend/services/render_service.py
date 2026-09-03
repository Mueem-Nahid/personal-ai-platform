from __future__ import annotations

import asyncio
import logging
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from models.job import JobPost
from models.profile import Profile
from models.rendering import RenderJob, ResumeTemplate
from models.resume import ResumeVersion
from renderers.base import RenderContext, RenderError, RendererUnavailableError
from renderers.registry import capabilities, get_renderer, resolve_engine
from repositories.render_repo import RenderJobRepository, ResumeTemplateRepository
from schemas.resume import ResumeContent
from services.minio_service import MinioService

logger = logging.getLogger(__name__)

_PROFILE_FIELDS = (
    "full_name",
    "title",
    "email",
    "phone",
    "location",
    "github_url",
    "linkedin_url",
    "website",
)


def _safe_filename(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text).strip()
    return re.sub(r"[\s_]+", "-", cleaned)[:60]


class RenderService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._job_repo = RenderJobRepository(session)
        self._template_repo = ResumeTemplateRepository(session)
        self._minio = MinioService()

    async def create_render_job(
        self,
        profile_id: uuid.UUID,
        template_id: uuid.UUID,
        output_format: str,
        resume_version_id: uuid.UUID | None = None,
        content: ResumeContent | None = None,
    ) -> RenderJob:
        template = await self._template_repo.get(template_id)
        if template is None or template.status != "active":
            raise ValueError(f"ResumeTemplate {template_id} not found or inactive")

        try:
            engine = resolve_engine(template.format, output_format)
        except ValueError as err:
            raise ValueError(str(err)) from err
        for capability in capabilities():
            if (
                capability["format"] == template.format
                and capability["output"] == output_format
                and not capability["available"]
            ):
                raise ValueError(capability["reason"] or "Renderer not available")

        if content is None:
            if resume_version_id is None:
                raise ValueError("Either 'content' or 'resume_version_id' is required")
            version = await self._session.get(ResumeVersion, resume_version_id)
            if version is None:
                raise ValueError(f"ResumeVersion {resume_version_id} not found")
            if not version.content_json:
                raise ValueError(
                    f"ResumeVersion {resume_version_id} has no content to render "
                    f"(status: {version.status})"
                )
            content = ResumeContent(**version.content_json)

        job = RenderJob(
            profile_id=profile_id,
            template_id=template_id,
            resume_version_id=resume_version_id,
            content_json=content.model_dump(),
            output_format=output_format,
            engine=engine,
            status="queued",
        )
        job = await self._job_repo.create(job)
        await self._session.commit()
        return job

    async def run_background(self, job_id: uuid.UUID) -> None:
        job = await self._job_repo.get(job_id)
        if job is None:
            logger.error("RenderJob %s not found for background processing", job_id)
            return

        job.status = "rendering"
        await self._job_repo.update(job)
        await self._session.commit()

        try:
            data, filename = await self._render(job)
            object_key = self._minio.upload(
                data,
                filename,
                content_type="application/pdf"
                if job.output_format == "pdf"
                else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                prefix="renders",
            )
            job.minio_object_key = object_key
            job.filename = filename
            job.file_size_bytes = len(data)
            job.status = "done"
            job.error = None
        except RendererUnavailableError as e:
            job.status = "failed"
            job.error = str(e)[:2000]
            logger.error("Renderer unavailable for RenderJob %s: %s", job_id, e)
        except RenderError as e:
            job.status = "failed"
            job.error = str(e)[:2000]
            logger.error("Render failed for RenderJob %s: %s", job_id, e)
        except Exception as e:
            job.status = "failed"
            job.error = f"Unexpected error: {e}"[:2000]
            logger.exception("RenderJob %s crashed", job_id)

        await self._job_repo.update(job)
        await self._session.commit()

    async def _render(self, job: RenderJob) -> tuple[bytes, str]:
        template: ResumeTemplate | None = None
        if job.template_id is not None:
            template = await self._template_repo.get(job.template_id)

        content = ResumeContent(**(job.content_json or {}))
        profile = await self._session.get(Profile, job.profile_id)
        profile_ctx = (
            {k: (getattr(profile, k) or "") for k in _PROFILE_FIELDS}
            if profile
            else {}
        )

        job_ctx: dict[str, str] = {}
        version_label = "custom"
        if job.resume_version_id is not None:
            version = await self._session.get(ResumeVersion, job.resume_version_id)
            if version is not None:
                version_label = f"v{version.version_no}"
                job_post = await self._session.get(JobPost, version.job_id)
                if job_post is not None:
                    fields = job_post.parsed_fields or {}
                    job_ctx = {
                        "title": str(fields.get("title") or job_post.title or ""),
                        "company": str(fields.get("company") or job_post.company or ""),
                    }

        renderer = get_renderer(template.format if template else "html")
        asset = (
            self._minio.download(template.asset_key)
            if template is not None and template.asset_key
            else None
        )
        ctx = RenderContext(
            content=content,
            profile=profile_ctx,
            job=job_ctx,
            template_source=(template.source_text or "") if template else "",
            styles_text=template.styles_text if template else None,
            template_asset=asset,
        )
        data = await asyncio.to_thread(renderer.render, ctx, job.output_format)

        template_label = _safe_filename(template.name) if template else "resume"
        filename = f"resume-{template_label}-{version_label}.{job.output_format}"
        return data, filename

    async def get(self, job_id: uuid.UUID) -> RenderJob | None:
        return await self._job_repo.get(job_id)

    async def list_by_profile(
        self, profile_id: uuid.UUID, limit: int = 50
    ) -> list[RenderJob]:
        return await self._job_repo.list_by_profile(profile_id, limit)

    async def download(self, job_id: uuid.UUID) -> tuple[bytes, str, str]:
        """Return (data, filename, content_type) for a completed job."""
        job = await self._job_repo.get(job_id)
        if job is None:
            raise ValueError(f"RenderJob {job_id} not found")
        if job.status != "done" or not job.minio_object_key:
            raise ValueError(f"RenderJob {job_id} is not completed (status: {job.status})")
        content_type = (
            "application/pdf"
            if job.output_format == "pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        return (
            self._minio.download(job.minio_object_key),
            job.filename or f"resume.{job.output_format}",
            content_type,
        )

    async def delete(self, job_id: uuid.UUID) -> None:
        job = await self._job_repo.get(job_id)
        if job is None:
            raise ValueError(f"RenderJob {job_id} not found")
        if job.minio_object_key:
            self._minio.delete(job.minio_object_key)
        await self._job_repo.delete(job)
        await self._session.commit()
