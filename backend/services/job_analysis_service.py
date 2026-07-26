from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from agents.job_analysis_agent import _graph
from models.job_analysis import JobAnalysis
from repositories.job_analysis_repo import JobAnalysisRepository

logger = logging.getLogger(__name__)


class JobAnalysisService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = JobAnalysisRepository(session)

    async def create_pending(
        self, job_id: uuid.UUID, profile_id: uuid.UUID
    ) -> JobAnalysis:
        existing = await self._repo.get_by_job_and_profile(job_id, profile_id)
        if existing:
            await self._repo.delete(existing)
            await self._session.flush()
        analysis = JobAnalysis(
            job_id=job_id,
            profile_id=profile_id,
            status="analyzing",
        )
        analysis = await self._repo.create(analysis)
        await self._session.commit()
        return analysis

    async def run_background(self, analysis_id: uuid.UUID) -> None:
        analysis = await self._repo.get(analysis_id)
        if not analysis:
            logger.error("JobAnalysis %s not found for background processing", analysis_id)
            return

        try:
            result = await _graph.ainvoke(
                {
                    "analysis_id": str(analysis_id),
                    "job_id": str(analysis.job_id),
                    "profile_id": str(analysis.profile_id),
                    "raw_job_text": "",
                    "profile_digest": "",
                    "retrieved_chunks": [],
                    "prompt": "",
                    "report": None,
                    "error": None,
                    "provider": "",
                    "model": "",
                    "prompt_version": "",
                }
            )
        except Exception as e:
            logger.exception("Analysis graph failed for %s", analysis_id)
            analysis.status = "failed"
            analysis.error = str(e)[:2000]
            await self._repo.update(analysis)
            await self._session.commit()
            return

        if result.get("error"):
            analysis.status = "failed"
            analysis.error = result["error"][:2000]
        else:
            analysis.status = "analyzed"
            analysis.report = result.get("report")
            analysis.provider = result.get("provider")
            analysis.model = result.get("model")
            analysis.prompt_version = result.get("prompt_version")
        await self._repo.update(analysis)
        await self._session.commit()

    async def get(self, analysis_id: uuid.UUID) -> JobAnalysis | None:
        return await self._repo.get(analysis_id)

    async def list_by_job(self, job_id: uuid.UUID) -> list[JobAnalysis]:
        return await self._repo.list_by_job(job_id)

    async def list_by_profile(self, profile_id: uuid.UUID) -> list[JobAnalysis]:
        return await self._repo.list_by_profile(profile_id)

    async def list_all(self) -> list[JobAnalysis]:
        return await self._repo.list_all()

    async def delete(self, analysis_id: uuid.UUID) -> None:
        analysis = await self._repo.get(analysis_id)
        if analysis is None:
            raise ValueError(f"JobAnalysis {analysis_id} not found")
        await self._repo.delete(analysis)
        await self._session.commit()
