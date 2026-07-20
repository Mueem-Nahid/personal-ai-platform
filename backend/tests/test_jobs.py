import asyncio
import httpx
import pytest
from httpx import ASGITransport

from main import app
from parsers.extractors import find_salary

JOB_TEXT = """Senior Backend Engineer at TechCorp

Location: San Francisco, CA (Remote OK)
Salary: $150,000 – $190,000 per year
Employment Type: Full-time

About the Role:
We are looking for a Senior Backend Engineer to join our platform team.

Requirements:
- 5+ years of experience in backend development
- Strong proficiency in Python and Go
- Experience with PostgreSQL, Redis, and Kubernetes
- BS in Computer Science or equivalent

Responsibilities:
- Design and build scalable microservices
- Optimize database queries and API performance
- Mentor junior engineers

Skills: Python, Go, PostgreSQL, Redis, Kubernetes, Docker, gRPC, AWS
Tech Stack: Python, Go, PostgreSQL, Redis, Kubernetes, Docker, AWS, Terraform
"""

POLL_TIMEOUT = 300


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def poll_until_done(client: httpx.AsyncClient, job_id: str, timeout: int = POLL_TIMEOUT) -> dict:
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        resp = await client.get(f"/api/v1/jobs/{job_id}")
        if resp.status_code == 200:
            job = resp.json()
            if job["status"] != "parsing":
                return job
        await asyncio.sleep(3)
    raise TimeoutError(f"Job {job_id} did not finish within {timeout}s")


@pytest.fixture
async def saved_job(client: httpx.AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/jobs/parse-text",
        json={"text": JOB_TEXT},
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    return await poll_until_done(client, job_id)


# ── unit: salary regex ───────────────────────────────────────────────────────

def test_salary_regex_range():
    result = find_salary("Salary: $150,000 – $190,000 per year")
    assert result is not None
    assert "150" in result

def test_salary_regex_single():
    result = find_salary("Compensation: $120k")
    assert result is not None
    assert "120" in result

def test_salary_regex_no_match():
    result = find_salary("Competitive salary and benefits")
    assert result is None


# ── integration: parse-text ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_parse_text_creates_job(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/jobs/parse-text",
        json={"text": JOB_TEXT},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["job_id"]
    assert body["status"] == "parsing"

    job = await poll_until_done(client, body["job_id"])
    assert job["id"]
    assert job["source"] == "text"
    assert job["status"] in ("parsed", "failed")

    if job["status"] == "parsed" and job["parsed_fields"]:
        fields = job["parsed_fields"]
        assert isinstance(fields, dict)
        assert isinstance(fields.get("skills", []), list)


@pytest.mark.asyncio
async def test_parse_text_rejects_short_input(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/jobs/parse-text",
        json={"text": "Short"},
    )
    assert response.status_code == 422


# ── integration: crud ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_jobs(client: httpx.AsyncClient, saved_job: dict) -> None:
    response = await client.get("/api/v1/jobs/")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert any(j["id"] == saved_job["id"] for j in body["jobs"])


@pytest.mark.asyncio
async def test_get_job(client: httpx.AsyncClient, saved_job: dict) -> None:
    job_id = saved_job["id"]
    response = await client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["id"] == job_id


@pytest.mark.asyncio
async def test_get_job_not_found(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_job(client: httpx.AsyncClient, saved_job: dict) -> None:
    job_id = saved_job["id"]
    response = await client.delete(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 404
