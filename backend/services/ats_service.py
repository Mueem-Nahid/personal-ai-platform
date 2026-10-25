from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.job import JobPost
from models.knowledge import Document, DocumentChunk
from models.resume import MasterResume, ResumeVersion
from repositories.resume_repo import ResumeVersionRepository
from schemas.ats import AtsReport
from schemas.resume import ResumeContent
from services.ats_scoring import evaluate_resume, fingerprint, resume_text

logger = logging.getLogger(__name__)


class StaleAtsReportError(ValueError):
    pass


class AtsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ResumeVersionRepository(session)

    async def _inputs(self, version_id: UUID) -> tuple[ResumeVersion, JobPost, ResumeContent]:
        version = await self._repo.get(version_id)
        if version is None:
            raise LookupError("Resume version not found")
        if version.status != "built" or not version.content_json:
            raise ValueError("ATS checks require a completed resume with content")
        job = await self._session.get(JobPost, version.job_id)
        if job is None:
            raise LookupError("Job post not found")
        return version, job, ResumeContent(**version.content_json)

    async def get_report(self, version_id: UUID) -> AtsReport | None:
        version, job, content = await self._inputs(version_id)
        if not version.ats_report:
            return None
        report = AtsReport(**version.ats_report)
        report.is_stale = report.fingerprint != fingerprint(content, job.parsed_fields or {})
        return report

    async def evaluate(self, version_id: UUID) -> AtsReport:
        version, job, content = await self._inputs(version_id)
        report = evaluate_resume(
            content, job.parsed_fields or {}, version_id, version.ats_baseline_score
        )
        version.ats_report = report.model_dump(mode="json")
        await self._repo.update(version)
        await self._session.commit()
        return report

    async def create_refinement(self, version_id: UUID, expected_fingerprint: str) -> ResumeVersion:
        # Serialize a refinement snapshot against edits to its source version.
        await self._session.execute(
            select(ResumeVersion.id).where(ResumeVersion.id == version_id).with_for_update()
        )
        source, job, content = await self._inputs(version_id)
        report = await self.get_report(version_id)
        if report is None or report.is_stale or report.fingerprint != expected_fingerprint:
            raise StaleAtsReportError(
                "The resume or job changed. Run the ATS check again before refining."
            )
        if not report.suggestions:
            raise ValueError(
                "No actionable ATS suggestions remain. You can still edit the resume manually."
            )
        master = await self._session.get(MasterResume, source.master_resume_id)
        if master is None or master.profile_id != source.profile_id:
            raise ValueError("The source master resume is unavailable for this profile")
        document = await self._session.get(Document, master.document_id)
        if document is None or document.profile_id != source.profile_id:
            raise ValueError("The master document is unavailable for this profile")
        reference = document.extracted_text
        if not reference:
            result = await self._session.execute(
                select(DocumentChunk.text_content)
                .where(DocumentChunk.document_id == document.id)
                .order_by(DocumentChunk.chunk_index)
            )
            reference = "\n".join(result.scalars().all())
        version = ResumeVersion(
            profile_id=source.profile_id,
            job_id=source.job_id,
            master_resume_id=source.master_resume_id,
            version_no=await self._repo.next_version_no(source.profile_id, source.job_id),
            status="building",
            parent_version_id=source.id,
            ats_baseline_score=report.overall_score,
            optimization_context={
                "source_content": content.model_dump(),
                "source_version_no": source.version_no,
                "job_fields": job.parsed_fields or {},
                "report": report.model_dump(mode="json"),
                "reference_text": (reference or "")[: settings.resume_max_master_chars],
            },
        )
        await self._repo.create(version)
        await self._session.commit()
        return version

    async def run_refinement(self, version_id: UUID) -> None:
        from agents.ats_optimizer_agent import build_optimization_prompt, validate_refinement
        from parsers.llm_provider import complete
        from utils.json_repair import repair_json

        version = await self._repo.get(version_id)
        if version is None or version.status != "building":
            return
        try:
            context = version.optimization_context
            if not context:
                raise ValueError("Refinement snapshot is missing")
            version.prompt_text = build_optimization_prompt(context)
            version.evidence_text = context["reference_text"]
            version.provider = settings.llm_provider
            version.model = (
                settings.ollama_model if settings.llm_provider == "ollama" else settings.llm_model
            )
            version.prompt_version = "ats-v1"
            await self._repo.update(version)
            await self._session.commit()
            raw = await complete(
                version.prompt_text,
                json_mode=True,
                max_tokens=settings.resume_max_tokens,
                temperature=0.2,
            )
            version.raw_response = raw
            content = ResumeContent(**repair_json(raw, frozenset({"summary", "sections"})))
            validate_refinement(content, context)
            version.content_json = content.model_dump()
            version.content_text = resume_text(content)
            version.status = "built"
            version.error = None
            # Evaluate against the exact job snapshot used for this refinement.
            report = evaluate_resume(
                content, context["job_fields"], version.id, version.ats_baseline_score
            )
            version.ats_report = report.model_dump(mode="json")
        except Exception as exc:
            logger.exception("ATS refinement failed for %s", version_id)
            version.status = "failed"
            version.error = str(exc)[:2000] or "ATS refinement timed out"
        await self._repo.update(version)
        await self._session.commit()
