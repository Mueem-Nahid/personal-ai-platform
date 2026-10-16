from __future__ import annotations

import asyncio

import httpx
import pytest
from httpx import ASGITransport

from main import app

JOB_TEXT = """Senior Backend Engineer at TechCorp

Location: San Francisco, CA (Remote OK)
Salary: $150,000 - $190,000 per year
Employment Type: Full-time

Requirements:
- 5+ years Python and Go
- PostgreSQL, Redis, Kubernetes
- BS in CS

Responsibilities:
- Design and build scalable microservices
- Mentor junior engineers

Skills: Python, Go, PostgreSQL, Redis, Kubernetes, Docker, gRPC, AWS
"""

PROFILE_CREATE = {
    "full_name": "Test User",
    "email": "test@example.com",
    "phone": "+1-555-9999",
    "location": "San Francisco",
    "title": "Senior Backend Engineer",
    "summary": "Experienced backend engineer",
    "github_url": "https://github.com/test",
    "linkedin_url": "https://linkedin.com/in/test",
    "skills": [
        {"name": "Python", "category": "backend", "proficiency": "expert", "years_of_experience": 6.0},
        {"name": "PostgreSQL", "category": "databases", "proficiency": "advanced", "years_of_experience": 5.0},
    ],
    "experiences": [
        {
            "company": "PrevCorp",
            "title": "Backend Engineer",
            "employment_type": "full-time",
            "start_date": "2020-01-01",
            "end_date": "2023-12-31",
            "current": False,
            "description": "Built microservices in Python and Go",
            "bullet_points": ["Led migration to Kubernetes", "Reduced latency by 40%"],
        }
    ],
}

RESUME_DOC_CONTENT = """# Test User - Senior Backend Engineer

## Summary
Experienced backend engineer with 8 years of experience building scalable systems.

## Experience
### PrevCorp - Backend Engineer (2020-2023)
- Led migration of 15 microservices to Kubernetes, reducing deploy time by 60%
- Designed RESTful APIs handling 100K requests/minute with 99.9% uptime
- Mentored team of 4 junior engineers in Python and Go best practices
- Built CI/CD pipelines using GitHub Actions and ArgoCD

## Projects
### Open Source Monitoring Tool
- Created a distributed tracing library in Go processing 50K spans/second
- Published to PyPI with 2K monthly downloads

## Skills
Python, Go, PostgreSQL, Redis, Kubernetes, Docker, gRPC, AWS, Terraform

## Education
BS Computer Science, State University (2015)
"""


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    base_url = "http://test"
    return httpx.AsyncClient(transport=transport, base_url=base_url)


def _build_headers() -> dict:
    return {"Content-Type": "application/json"}


class TestPromptLoader:
    def test_load_with_frontmatter(self, tmp_path):
        from utils.prompt_loader import load_prompt

        file = tmp_path / "test.md"
        file.write_text(
            "---\nname: test\nversion: 1\ntemperature: 0.6\n---\n\n# Body\nThis is the body."
        )
        body, meta = load_prompt(file)
        assert body == "# Body\nThis is the body."
        assert meta["name"] == "test"
        assert meta["version"] == 1
        assert meta["temperature"] == 0.6

    def test_load_without_frontmatter(self, tmp_path):
        from utils.prompt_loader import load_prompt

        file = tmp_path / "nofront.md"
        file.write_text("Just a body\nno frontmatter")
        body, meta = load_prompt(file)
        assert body == "Just a body\nno frontmatter"
        assert meta == {}

    def test_load_customize_prompt_exists(self):
        from core.config import settings
        from utils.prompt_loader import load_prompt

        path = settings.prompts_path / "cv" / "customize.md"
        body, meta = load_prompt(path)
        assert len(body) > 50
        assert "summary" in body
        assert "sections" in body


class TestResumeVersionNumbering:
    @pytest.mark.skip(reason="Requires DB with migration 0006 applied")
    async def test_next_version_no(self, client):  # noqa: F811
        from core.database import SessionLocal

        from models.resume import ResumeVersion
        from repositories.resume_repo import ResumeVersionRepository

        async with SessionLocal() as session:
            repo = ResumeVersionRepository(session)
            v = await repo.next_version_no(
                __import__("uuid").UUID("00000000-0000-0000-0000-000000000001"),
                __import__("uuid").UUID("00000000-0000-0000-0000-000000000002"),
            )
            assert v == 1


class TestResumeBuilderAPI:
    @pytest.mark.skip(reason="Requires DB with migration 0006 applied")
    async def test_build_without_master_fails(self, client):  # noqa: F811
        headers = _build_headers()
        resp = await client.post(
            "/api/v1/resumes",
            json={
                "profile_id": "00000000-0000-0000-0000-000000000001",
                "job_id": "00000000-0000-0000-0000-000000000002",
            },
            headers=headers,
        )
        assert resp.status_code == 400

    @pytest.mark.skip(reason="Requires DB with migration 0006 applied")
    async def test_workflow_e2e(self, client):  # noqa: F811
        headers = _build_headers()

        # 1. Create profile
        resp = await client.post(
            "/api/v1/profiles", json=PROFILE_CREATE, headers=headers
        )
        assert resp.status_code == 201, resp.text
        profile = resp.json()

        # 2. Create job
        resp = await client.post(
            "/api/v1/jobs/parse-text",
            json={"text": JOB_TEXT},
            headers=headers,
        )
        assert resp.status_code == 202, resp.text
        job_meta = resp.json()
        job_id = job_meta["job_id"]

        # Wait for job parsing (instant in test — the real ARQ worker isn't running)
        await asyncio.sleep(0.2)

        # 3. Check the key endpoints respond correctly
        resp = await client.get(
            f"/api/v1/resumes/master?profile_id={profile['id']}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

        resp = await client.get(
            f"/api/v1/resumes?profile_id={profile['id']}&job_id={job_id}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "versions" in data

    @pytest.mark.skip(reason="Requires DB with migration 0006 applied")
    async def test_list_master_resumes_empty(self, client):  # noqa: F811
        headers = _build_headers()
        resp = await client.post("/api/v1/profiles", json=PROFILE_CREATE, headers=headers)
        assert resp.status_code == 201
        profile = resp.json()

        resp = await client.get(f"/api/v1/resumes/master?profile_id={profile['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0


class TestResumeContentSchema:
    def test_valid_content(self):
        from schemas.resume import ResumeContent, ResumeSection

        content = ResumeContent(
            summary="A test summary",
            sections=[
                ResumeSection(name="Experience", items=["Built microservices", "Mentored team"]),
                ResumeSection(name="Skills", items=["Python", "Go"]),
            ],
        )
        assert content.summary == "A test summary"
        assert len(content.sections) == 2

    def test_empty_content(self):
        from schemas.resume import ResumeContent

        content = ResumeContent()
        assert content.summary is None
        assert content.sections == []


class TestQdrantSearchInDocument:
    def test_method_exists(self):
        from services.qdrant_service import QdrantService

        svc = QdrantService()
        assert hasattr(svc, "search_in_document")
        assert callable(svc.search_in_document)
