from __future__ import annotations

import asyncio
import os
from unittest.mock import MagicMock

import httpx
import pytest
from httpx import ASGITransport

from main import app

JOB_TEXT = """Senior Backend Engineer at TechCorp

Location: San Francisco, CA (Remote OK)
Salary: $150,000 – $190,000 per year
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
        {"name": "Python", "category": "backend", "proficiency": "expert",
         "years_of_experience": 6.0},
        {"name": "PostgreSQL", "category": "databases", "proficiency": "advanced",
         "years_of_experience": 5.0},
    ],
    "experiences": [
        {
            "company": "PrevCorp",
            "title": "Backend Engineer",
            "employment_type": "full-time",
            "description": "Built APIs",
            "bullet_points": ["Led migration to microservices"],
        }
    ],
    "education": [
        {"institution": "State University", "degree": "BS", "field_of_study": "CS"},
    ],
}

POLL_TIMEOUT = 300
ANALYSIS_POLL_TIMEOUT = 180


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def saved_profile(client: httpx.AsyncClient) -> dict:
    response = await client.post("/api/v1/profiles", json=PROFILE_CREATE)
    assert response.status_code == 200
    return response.json()


@pytest.fixture
async def saved_job(client: httpx.AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/jobs/parse-text",
        json={"text": JOB_TEXT},
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    deadline = asyncio.get_event_loop().time() + POLL_TIMEOUT
    while asyncio.get_event_loop().time() < deadline:
        resp = await client.get(f"/api/v1/jobs/{job_id}")
        if resp.status_code == 200:
            job = resp.json()
            if job["status"] != "parsing":
                return job
        await asyncio.sleep(3)
    raise TimeoutError(f"Job {job_id} did not finish within {POLL_TIMEOUT}s")


# ── Unit: profile digest ──────────────────────────────────────────────────────

def test_profile_digest_strips_pii():
    from agents.profile_digest import _PII_FIELDS, build_digest
    from models.profile import Profile

    profile = MagicMock(spec=Profile)
    profile.full_name = "Jane Doe"
    profile.email = "jane@example.com"
    profile.phone = "+1-555-0000"
    profile.github_url = "https://github.com/jane"
    profile.linkedin_url = "https://linkedin.com/in/jane"
    profile.website = "https://jane.dev"
    profile.title = "Senior Engineer"
    profile.summary = "Experienced engineer"
    profile.location = "San Francisco"
    profile.skills = []
    profile.experiences = []
    profile.projects = []
    profile.education = []
    profile.certificates = []
    profile.languages = []
    profile.achievements = []

    digest = build_digest(profile)

    for pii_field in _PII_FIELDS:
        assert pii_field not in " ".join(digest.split())
    assert "Senior Engineer" in digest
    assert "San Francisco" in digest
    assert "jane@example.com" not in digest
    assert "github.com" not in digest


def test_profile_digest_includes_skills():
    from agents.profile_digest import build_digest
    from models.profile import Profile, Skill

    profile = MagicMock(spec=Profile)
    profile.title = "Engineer"
    profile.summary = None
    profile.location = None
    skill = MagicMock(spec=Skill)
    skill.name = "Python"
    skill.category = "backend"
    skill.proficiency = "expert"
    skill.years_of_experience = 6.0
    profile.skills = [skill]
    profile.experiences = []
    profile.projects = []
    profile.education = []
    profile.certificates = []
    profile.languages = []
    profile.achievements = []

    digest = build_digest(profile)
    assert "Python" in digest
    assert "backend" in digest
    assert "expert" in digest
    assert "6.0" in digest


# ── Unit: JSON repair ─────────────────────────────────────────────────────────

def test_repair_json_valid():
    from utils.json_repair import repair_json

    result = repair_json('{"title": "Engineer", "company": "Acme"}')
    assert result["title"] == "Engineer"


def test_repair_json_raises_on_invalid():
    from utils.json_repair import repair_json

    with pytest.raises(ValueError):
        repair_json("not json at all")


# ── Integration: analysis workflow ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_analysis_missing_job_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/analyses",
        json={
            "job_id": "00000000-0000-0000-0000-000000000000",
            "profile_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_start_analysis_missing_profile_returns_404(
    client: httpx.AsyncClient, saved_job: dict
) -> None:
    response = await client.post(
        "/api/v1/analyses",
        json={
            "job_id": saved_job["id"],
            "profile_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_start_analysis_creates_pending(
    client: httpx.AsyncClient, saved_job: dict, saved_profile: dict
) -> None:
    response = await client.post(
        "/api/v1/analyses",
        json={
            "job_id": saved_job["id"],
            "profile_id": saved_profile["id"],
        },
    )
    assert response.status_code == 202
    body = response.json()
    assert body["analysis_id"]
    assert body["status"] == "analyzing"


@pytest.mark.asyncio
async def test_get_analysis_not_found(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/analyses/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_analysis_completes(
    client: httpx.AsyncClient, saved_job: dict, saved_profile: dict
) -> None:
    if not os.environ.get("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY not set; skipping live analysis integration test")

    response = await client.post(
        "/api/v1/analyses",
        json={
            "job_id": saved_job["id"],
            "profile_id": saved_profile["id"],
        },
    )
    assert response.status_code == 202
    analysis_id = response.json()["analysis_id"]

    deadline = asyncio.get_event_loop().time() + ANALYSIS_POLL_TIMEOUT
    while asyncio.get_event_loop().time() < deadline:
        resp = await client.get(f"/api/v1/analyses/{analysis_id}")
        if resp.status_code == 200:
            analysis = resp.json()
            if analysis["status"] != "analyzing":
                assert analysis["status"] == "analyzed"
                assert analysis["report"] is not None
                assert isinstance(analysis["report"].get("matched_skills"), list)
                return
        await asyncio.sleep(3)
    raise TimeoutError(f"Analysis {analysis_id} did not finish")


@pytest.mark.asyncio
async def test_delete_analysis(
    client: httpx.AsyncClient, saved_job: dict, saved_profile: dict
) -> None:
    response = await client.post(
        "/api/v1/analyses",
        json={
            "job_id": saved_job["id"],
            "profile_id": saved_profile["id"],
        },
    )
    assert response.status_code == 202
    analysis_id = response.json()["analysis_id"]

    response = await client.delete(f"/api/v1/analyses/{analysis_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/analyses/{analysis_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_analyses(
    client: httpx.AsyncClient, saved_job: dict, saved_profile: dict
) -> None:
    response = await client.post(
        "/api/v1/analyses",
        json={
            "job_id": saved_job["id"],
            "profile_id": saved_profile["id"],
        },
    )
    assert response.status_code == 202

    response = await client.get("/api/v1/analyses")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert isinstance(body["analyses"], list)

    response = await client.get(
        f"/api/v1/analyses?job_id={saved_job['id']}"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
