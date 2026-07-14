import httpx
import pytest
from httpx import ASGITransport

from main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_create_and_get_profile(client: httpx.AsyncClient) -> None:
    body = {
        "full_name": "Jane Doe",
        "email": "jane@example.com",
        "title": "Senior Engineer",
        "skills": [
            {"name": "Python", "category": "Programming", "proficiency": "expert"},
            {"name": "Docker", "category": "DevOps", "proficiency": "advanced"},
        ],
        "experiences": [
            {
                "company": "Acme Corp",
                "title": "Backend Engineer",
                "current": True,
                "bullet_points": ["Built API", "Scaled to 1M users"],
            }
        ],
    }
    response = await client.post("/api/v1/profiles", json=body)
    assert response.status_code == 201
    profile = response.json()
    assert profile["full_name"] == "Jane Doe"
    assert profile["email"] == "jane@example.com"
    assert len(profile["skills"]) == 2
    skill_names = {s["name"] for s in profile["skills"]}
    assert "Python" in skill_names
    assert "Docker" in skill_names
    assert len(profile["experiences"]) == 1
    assert profile["experiences"][0]["company"] == "Acme Corp"

    profile_id = profile["id"]
    get_response = await client.get(f"/api/v1/profiles/{profile_id}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["full_name"] == "Jane Doe"
    assert len(fetched["skills"]) == 2


@pytest.mark.asyncio
async def test_list_profiles(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/profiles")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_update_profile(client: httpx.AsyncClient) -> None:
    create_response = await client.post("/api/v1/profiles", json={"full_name": "Temp User"})
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]

    update_response = await client.put(
        f"/api/v1/profiles/{profile_id}",
        json={"title": "Updated Title", "location": "NYC"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["title"] == "Updated Title"
    assert updated["location"] == "NYC"


@pytest.mark.asyncio
async def test_get_nonexistent_profile(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/profiles/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_skill_for_profile(client: httpx.AsyncClient) -> None:
    create_response = await client.post("/api/v1/profiles", json={"full_name": "Skill Test"})
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]

    skill_response = await client.post(
        f"/api/v1/profiles/{profile_id}/skills",
        json={"name": "Rust", "proficiency": "intermediate"},
    )
    assert skill_response.status_code == 201
    skill = skill_response.json()
    assert skill["name"] == "Rust"
    assert skill["profile_id"] == profile_id


@pytest.mark.asyncio
async def test_delete_profile(client: httpx.AsyncClient) -> None:
    create_response = await client.post("/api/v1/profiles", json={"full_name": "Delete Me"})
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/profiles/{profile_id}")
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/profiles/{profile_id}")
    assert get_response.status_code == 404
