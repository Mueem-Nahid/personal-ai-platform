from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.profile import Profile
from models.rendering import ResumeTemplate
from renderers.base import RenderContext
from renderers.registry import get_renderer
from repositories.render_repo import ResumeTemplateRepository
from schemas.resume import ResumeContent, ResumeSection
from services.minio_service import MinioService

logger = logging.getLogger(__name__)

SAMPLE_CONTENT = ResumeContent(
    summary=(
        "Backend engineer with 6 years of experience building distributed systems. "
        "Cut API latency 45% at scale and led a platform team of six engineers."
    ),
    sections=[
        ResumeSection(
            name="Experience",
            items=[
                "Senior Engineer, Acme Corp (2021-present) — Led platform team of 6; latency -45%",
                "Engineer, Globex (2018–2021) — Shipped payments service handling 2M requests/day",
            ],
        ),
        ResumeSection(
            name="Skills",
            items=["Python, Go, PostgreSQL, Redis, Kubernetes, AWS"],
        ),
        ResumeSection(
            name="Education",
            items=["B.Sc. Computer Science, State University (2018)"],
        ),
    ],
)

SAMPLE_PROFILE = {
    "full_name": "Jane Doe",
    "title": "Senior Software Engineer",
    "email": "jane.doe@example.com",
    "phone": "+1 (555) 010-2030",
    "location": "Berlin, DE",
    "github_url": "github.com/janedoe",
    "linkedin_url": "linkedin.com/in/janedoe",
    "website": "janedoe.dev",
}


def _read_builtin_template_files() -> list[dict[str, Any]] | None:
    """Read built-in template directories into plain dicts (sync, run in a thread)."""
    import pathlib

    root = pathlib.Path(settings.templates_builtin_path)
    if not root.is_dir():
        logger.warning("Built-in template directory %s not found; skipping seed", root)
        return None

    entries: list[dict[str, Any]] = []
    for meta_path in sorted(root.glob("*/meta.yaml")):
        try:
            meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
            directory = meta_path.parent
            preferred = directory / f"template.{meta['format']}"
            if preferred.exists():
                source_path = preferred
            else:
                candidates = sorted(directory.glob("template.*"))
                source_path = candidates[0] if candidates else preferred
            source_text = (
                source_path.read_text(encoding="utf-8") if source_path.exists() else None
            )
            styles_path = directory / "styles.css"
            styles_text = (
                styles_path.read_text(encoding="utf-8") if styles_path.exists() else None
            )
            entries.append(
                {
                    "key": str(meta["key"]),
                    "name": str(meta["name"]),
                    "description": meta.get("description"),
                    "format": str(meta["format"]),
                    "is_default": bool(meta.get("is_default", False)),
                    "source_text": source_text,
                    "styles_text": styles_text,
                }
            )
        except Exception:
            logger.exception("Failed to read built-in template at %s", meta_path)
    return entries


class TemplateService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ResumeTemplateRepository(session)
        self._minio = MinioService()

    async def seed_builtins(self) -> int:
        """Insert built-in templates that do not exist yet.

        Existing rows are left untouched so user edits to built-in templates
        survive restarts. To ship a changed built-in, bump its ``key`` in
        meta.yaml or delete the row.
        """
        entries = await asyncio.to_thread(_read_builtin_template_files)
        if entries is None:
            return 0

        seeded = 0
        for entry in entries:
            try:
                existing = await self._repo.get_by_builtin_key(entry["key"])
                if existing is not None:
                    continue
                template = ResumeTemplate(
                    builtin_key=entry["key"],
                    name=entry["name"],
                    description=entry.get("description"),
                    format=entry["format"],
                    source_text=entry.get("source_text"),
                    styles_text=entry.get("styles_text"),
                    is_default=bool(entry.get("is_default", False)),
                    status="active",
                )
                self._session.add(template)
                seeded += 1
            except Exception:
                logger.exception("Failed to seed built-in template %s", entry.get("key"))
        if seeded:
            await self._session.commit()
            logger.info("Seeded %d new built-in templates", seeded)
        return seeded

    def upload_docx_asset(self, data: bytes, filename: str) -> str:
        """Store a binary .docx template in MinIO and return its object key."""
        return self._minio.upload(
            data,
            filename,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            prefix="templates",
        )

    async def list_templates(
        self, profile_id: uuid.UUID | None
    ) -> list[ResumeTemplate]:
        return await self._repo.list_visible(profile_id)

    async def get(self, template_id: uuid.UUID) -> ResumeTemplate | None:
        return await self._repo.get(template_id)

    async def create(
        self,
        profile_id: uuid.UUID | None,
        name: str,
        format: str,
        description: str | None = None,
        source_text: str | None = None,
        styles_text: str | None = None,
        asset_key: str | None = None,
        is_default: bool = False,
    ) -> ResumeTemplate:
        template = ResumeTemplate(
            profile_id=profile_id,
            name=name,
            description=description,
            format=format,
            source_text=source_text,
            styles_text=styles_text,
            asset_key=asset_key,
            is_default=False,
        )
        template = await self._repo.create(template)
        if is_default:
            await self.set_default(template.id, profile_id)
        else:
            await self._session.commit()
        return template

    async def update(
        self,
        template_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        source_text: str | None = None,
        styles_text: str | None = None,
    ) -> ResumeTemplate:
        template = await self._repo.get(template_id)
        if template is None:
            raise ValueError(f"ResumeTemplate {template_id} not found")
        if template.builtin_key is not None and name is not None and name != template.name:
            raise ValueError("Built-in template names cannot be changed")
        if name is not None:
            template.name = name
        if description is not None:
            template.description = description
        if source_text is not None:
            template.source_text = source_text
        if styles_text is not None:
            template.styles_text = styles_text
        template = await self._repo.update(template)
        await self._session.commit()
        return template

    async def delete(self, template_id: uuid.UUID) -> None:
        template = await self._repo.get(template_id)
        if template is None:
            raise ValueError(f"ResumeTemplate {template_id} not found")
        if template.builtin_key is not None:
            raise ValueError("Built-in templates cannot be deleted")
        if template.asset_key:
            self._minio.delete(template.asset_key)
        await self._repo.delete(template)
        await self._session.commit()

    async def set_default(
        self, template_id: uuid.UUID, profile_id: uuid.UUID | None = None
    ) -> ResumeTemplate:
        template = await self._repo.get(template_id)
        if template is None:
            raise ValueError(f"ResumeTemplate {template_id} not found")
        scope = profile_id if profile_id is not None else template.profile_id
        await self._repo.clear_defaults(scope)
        template.is_default = True
        template = await self._repo.update(template)
        await self._session.commit()
        return template

    async def get_default(self, profile_id: uuid.UUID) -> ResumeTemplate | None:
        return await self._repo.get_default(profile_id)

    async def render_preview(
        self,
        format: str,
        source_text: str,
        styles_text: str | None = None,
        content: ResumeContent | None = None,
        profile_id: uuid.UUID | None = None,
        output_format: str = "pdf",
    ) -> bytes:
        """Render sample or provided content synchronously for editor previews."""
        renderer = get_renderer(format)
        profile_ctx = dict(SAMPLE_PROFILE)
        if profile_id is not None:
            profile = await self._session.get(Profile, profile_id)
            if profile is not None:
                profile_ctx = {
                    k: (getattr(profile, k) or "")
                    for k in (
                        "full_name",
                        "title",
                        "email",
                        "phone",
                        "location",
                        "github_url",
                        "linkedin_url",
                        "website",
                    )
                }
        ctx = RenderContext(
            content=content or SAMPLE_CONTENT,
            profile=profile_ctx,
            template_source=source_text,
            styles_text=styles_text,
        )
        return await asyncio.to_thread(renderer.render, ctx, output_format)
