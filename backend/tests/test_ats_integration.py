"""Opt-in integration tests; only temporary rows and a mocked LLM/queue are used."""

from __future__ import annotations

import asyncio
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url

from core.config import settings
from core.database import SessionLocal
from main import app
from models.job import JobPost
from models.knowledge import Document
from models.profile import Profile
from models.resume import MasterResume, ResumeVersion
from schemas.resume import ResumeContent, ResumeSection
from workers.arq_worker import optimize_resume

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_ATS_DB_TESTS") != "1",
    reason="Set RUN_ATS_DB_TESTS=1 with migration 0008 applied",
)

SOURCE = ResumeContent(
    summary="Python engineer",
    sections=[
        ResumeSection(name="Experience", items=["Responsible for Python services"]),
        ResumeSection(name="Skills", items=["Python, PostgreSQL"]),
    ],
)
REFINED = ResumeContent(
    summary="Python and Go engineer",
    sections=[
        ResumeSection(
            name="Experience", items=["Built Python and Go services handling 200 requests"]
        ),
        ResumeSection(name="Skills", items=["Python, Go, PostgreSQL"]),
    ],
)


@pytest.fixture
async def setup_ats(monkeypatch):
    if make_url(settings.database_url).host not in {"localhost", "127.0.0.1", "::1"}:
        pytest.skip("ATS integration fixtures are restricted to a local development database")
    profile_id, job_id, doc_id, master_id, version_id = (uuid4() for _ in range(5))
    queue = SimpleNamespace(enqueue_job=AsyncMock())
    monkeypatch.setattr("api.routes.ats.get_redis", AsyncMock(return_value=queue))
    monkeypatch.setattr(
        "parsers.llm_provider.complete", AsyncMock(return_value=REFINED.model_dump_json())
    )
    async with SessionLocal() as session:
        session.add(Profile(id=profile_id, full_name="Temporary ATS integration test"))
        session.add(
            JobPost(
                id=job_id,
                source="text",
                status="parsed",
                raw_text="Python and Go engineer",
                parsed_fields={"skills": ["Python", "Go", "PostgreSQL"], "keywords": ["services"]},
            )
        )
        await session.flush()
        session.add(
            Document(
                id=doc_id,
                profile_id=profile_id,
                filename="ats-fixture.txt",
                file_type="txt",
                status="processed",
                extracted_text="Built Python and Go services handling 200 requests. PostgreSQL.",
            )
        )
        await session.flush()
        session.add(MasterResume(id=master_id, profile_id=profile_id, document_id=doc_id))
        await session.flush()
        session.add(
            ResumeVersion(
                id=version_id,
                profile_id=profile_id,
                job_id=job_id,
                master_resume_id=master_id,
                version_no=1,
                status="built",
                content_json=SOURCE.model_dump(),
            )
        )
        await session.commit()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield SimpleNamespace(
                client=client,
                version_id=version_id,
                profile_id=profile_id,
                job_id=job_id,
                queue=queue,
            )
    finally:
        async with SessionLocal() as session:
            profile = await session.get(Profile, profile_id)
            if profile:
                await session.delete(profile)
                await session.flush()
            job = await session.get(JobPost, job_id)
            if job:
                await session.delete(job)
            await session.commit()


async def checked(fixture):
    response = await fixture.client.post(f"/api/v1/resumes/{fixture.version_id}/ats")
    assert response.status_code == 200, response.text
    return response.json()


async def test_score_refine_rescore_and_manual_edit_loop(setup_ats):
    fixture = setup_ats
    path = f"/api/v1/resumes/{fixture.version_id}"
    response = await fixture.client.get(path + "/ats")
    assert response.status_code == 200 and response.json() is None
    baseline = await checked(fixture)
    assert len(baseline["checks"]) == 7
    response = await fixture.client.post(
        path + "/refine", json={"fingerprint": baseline["fingerprint"]}
    )
    assert response.status_code == 202, response.text
    child_id = response.json()["resume_version_id"]
    assert response.json()["version_no"] == 2
    fixture.queue.enqueue_job.assert_awaited_once_with("optimize_resume", child_id)
    await optimize_resume({}, child_id)
    response = await fixture.client.get(f"/api/v1/resumes/{child_id}")
    assert response.json()["status"] == "built"
    assert response.json()["parent_version_id"] == str(fixture.version_id)
    report = (await fixture.client.get(f"/api/v1/resumes/{child_id}/ats")).json()
    assert report["overall_score"] > baseline["overall_score"]
    assert report["baseline_score"] == baseline["overall_score"]
    assert report["score_delta"] == report["overall_score"] - baseline["overall_score"]
    assert not report["is_stale"]
    original = (await fixture.client.get(path)).json()
    assert original["content"] == SOURCE.model_dump()
    edited = REFINED.model_copy(update={"summary": "Updated resume summary"})
    response = await fixture.client.put(
        f"/api/v1/resumes/{child_id}/content", json={"content": edited.model_dump()}
    )
    assert response.status_code == 200, response.text
    assert (await fixture.client.get(f"/api/v1/resumes/{child_id}/ats")).json()["is_stale"]
    response = await fixture.client.post(
        f"/api/v1/resumes/{child_id}/refine", json={"fingerprint": report["fingerprint"]}
    )
    assert response.status_code == 409, response.text
    fixture.queue.enqueue_job.assert_awaited_once()
    refreshed = await fixture.client.post(f"/api/v1/resumes/{child_id}/ats")
    assert refreshed.status_code == 200
    assert not refreshed.json()["is_stale"]


async def test_concurrent_refinements_allocate_unique_versions(setup_ats):
    fixture = setup_ats
    baseline = await checked(fixture)

    async def refine():
        return await fixture.client.post(
            f"/api/v1/resumes/{fixture.version_id}/refine",
            json={"fingerprint": baseline["fingerprint"]},
        )

    responses = await asyncio.gather(refine(), refine())
    assert [r.status_code for r in responses] == [202, 202]
    assert {r.json()["version_no"] for r in responses} == {2, 3}


async def test_queue_failure_records_failed_child_and_preserves_source(setup_ats):
    fixture = setup_ats
    baseline = await checked(fixture)
    fixture.queue.enqueue_job.side_effect = ConnectionError("Queue disconnected")
    response = await fixture.client.post(
        f"/api/v1/resumes/{fixture.version_id}/refine",
        json={"fingerprint": baseline["fingerprint"]},
    )
    assert response.status_code == 503
    async with SessionLocal() as session:
        versions = (
            (
                await session.execute(
                    select(ResumeVersion).where(ResumeVersion.profile_id == fixture.profile_id)
                )
            )
            .scalars()
            .all()
        )
        assert len(versions) == 2
        assert next(v for v in versions if v.version_no == 1).content_json == SOURCE.model_dump()
        assert next(v for v in versions if v.version_no == 2).status == "failed"


async def test_missing_version_returns_404(setup_ats):
    response = await setup_ats.client.post(f"/api/v1/resumes/{uuid4()}/ats")
    assert response.status_code == 404
