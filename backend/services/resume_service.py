from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from models.knowledge import Document
from models.resume import MasterResume, ResumeVersion
from repositories.resume_repo import MasterResumeRepository, ResumeVersionRepository

logger = logging.getLogger(__name__)


class ResumeService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._master_repo = MasterResumeRepository(session)
        self._version_repo = ResumeVersionRepository(session)

    async def designate_master(
        self, profile_id: uuid.UUID, document_id: uuid.UUID, is_default: bool = False
    ) -> MasterResume:
        doc = await self._session.get(Document, document_id)
        if doc is None:
            raise ValueError(f"Document {document_id} not found")
        if doc.status != "processed":
            raise ValueError(
                f"Document {document_id} is not fully processed (status: {doc.status})"
            )

        existing = await self._master_repo.get_by_profile_and_document(
            profile_id, document_id
        )
        if existing:
            if is_default != existing.is_default or existing.status != "active":
                existing.is_default = is_default
                existing.status = "active"
                existing = await self._master_repo.update(existing)
                await self._session.flush()
            if is_default:
                await self._clear_other_defaults(profile_id, existing.id)
            await self._session.commit()
            return existing

        master = MasterResume(
            profile_id=profile_id,
            document_id=document_id,
            is_default=is_default,
        )
        master = await self._master_repo.create(master)
        await self._session.flush()
        if is_default:
            await self._clear_other_defaults(profile_id, master.id)
        await self._session.commit()
        return master

    async def _clear_other_defaults(self, profile_id: uuid.UUID, keep_id: uuid.UUID) -> None:
        from sqlalchemy import update

        stmt = (
            update(MasterResume)
            .where(
                MasterResume.profile_id == profile_id,
                MasterResume.id != keep_id,
                MasterResume.is_default.is_(True),
            )
            .values(is_default=False)
        )
        await self._session.execute(stmt)

    async def list_master_resumes(self, profile_id: uuid.UUID) -> list[MasterResume]:
        return await self._master_repo.list_by_profile(profile_id)

    async def remove_master_resume(self, master_id: uuid.UUID) -> None:
        master = await self._master_repo.get(master_id)
        if master is None:
            raise ValueError(f"MasterResume {master_id} not found")
        master.status = "archived"
        await self._master_repo.update(master)
        await self._session.commit()

    async def _resolve_master_resume_id(
        self, profile_id: uuid.UUID, master_resume_id: uuid.UUID | None
    ) -> uuid.UUID:
        if master_resume_id:
            master = await self._master_repo.get(master_resume_id)
            if master is None or master.status != "active":
                raise ValueError(
                    f"MasterResume {master_resume_id} not found or not active"
                )
            return master_resume_id
        default = await self._master_repo.get_default(profile_id)
        if default is None:
            raise ValueError(
                f"No active master resume found for profile {profile_id}. "
                "Designate one via POST /resumes/master first."
            )
        return default.id

    async def create_pending_build(
        self,
        profile_id: uuid.UUID,
        job_id: uuid.UUID,
        master_resume_id: uuid.UUID | None = None,
    ) -> ResumeVersion:
        resolved = await self._resolve_master_resume_id(profile_id, master_resume_id)
        version_no = await self._version_repo.next_version_no(profile_id, job_id)
        version = ResumeVersion(
            profile_id=profile_id,
            job_id=job_id,
            master_resume_id=resolved,
            version_no=version_no,
            status="building",
        )
        version = await self._version_repo.create(version)
        await self._session.commit()
        return version

    async def run_background(self, version_id: uuid.UUID) -> None:
        version = await self._version_repo.get(version_id)
        if not version:
            logger.error("ResumeVersion %s not found for background processing", version_id)
            return

        try:
            from agents.resume_builder_agent import _graph

            result = await _graph.ainvoke(
                {
                    "version_id": str(version_id),
                    "profile_id": str(version.profile_id),
                    "job_id": str(version.job_id),
                    "master_resume_id": str(version.master_resume_id),
                    "master_document_id": "",
                    "raw_job_text": "",
                    "job_parsed_fields": {},
                    "cv_full_text": "",
                    "retrieved_chunks": [],
                    "retrieved_chunk_ids": [],
                    "evidence_text": "",
                    "prompt": "",
                    "raw_response": "",
                    "content": None,
                    "content_text": "",
                    "error": None,
                    "provider": "",
                    "model": "",
                    "prompt_version": "",
                }
            )
        except Exception as e:
            logger.exception("Resume builder graph failed for %s", version_id)
            version.status = "failed"
            version.error = str(e)[:2000]
            await self._version_repo.update(version)
            await self._session.commit()
            return

        if result.get("error"):
            version.status = "failed"
            version.error = result["error"][:2000]
        else:
            version.status = "built"
            version.content_json = result.get("content")
            version.content_text = result.get("content_text")
            version.prompt_text = result.get("prompt") or None
            version.evidence_text = result.get("evidence_text") or None
            version.raw_response = result.get("raw_response") or None
            version.top_k_chunk_ids = result.get("retrieved_chunk_ids")
            version.provider = result.get("provider")
            version.model = result.get("model")
            version.prompt_version = result.get("prompt_version")
        await self._version_repo.update(version)
        await self._session.commit()

    async def get(self, version_id: uuid.UUID) -> ResumeVersion | None:
        return await self._version_repo.get(version_id)

    async def list_by_job_and_profile(
        self, profile_id: uuid.UUID, job_id: uuid.UUID
    ) -> list[ResumeVersion]:
        return await self._version_repo.list_by_job_and_profile(profile_id, job_id)

    async def list_all(self) -> list[ResumeVersion]:
        return await self._version_repo.list_all()

    async def delete(self, version_id: uuid.UUID) -> None:
        version = await self._version_repo.get(version_id)
        if version is None:
            raise ValueError(f"ResumeVersion {version_id} not found")
        await self._version_repo.delete(version)
        await self._session.commit()
