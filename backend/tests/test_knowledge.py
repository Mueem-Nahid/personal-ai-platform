import httpx
import pytest
from httpx import ASGITransport

from main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def profile_id(client: httpx.AsyncClient) -> str:
    response = await client.post("/api/v1/profiles", json={"full_name": "KB Test User"})
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
async def test_upload_txt_document(client: httpx.AsyncClient, profile_id: str) -> None:
    response = await client.post(
        f"/api/v1/profiles/{profile_id}/knowledge",
        files={"file": ("test.txt", b"Hello world, this is a test document for knowledge base.")},
    )
    assert response.status_code == 201
    doc = response.json()
    assert doc["filename"] == "test.txt"
    assert doc["file_type"] == "txt"
    assert doc["status"] in ("processing", "processed")
    assert doc["profile_id"] == profile_id


@pytest.mark.asyncio
async def test_list_documents(client: httpx.AsyncClient, profile_id: str) -> None:
    response = await client.get(f"/api/v1/profiles/{profile_id}/knowledge")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data
    assert isinstance(data["documents"], list)


@pytest.mark.asyncio
async def test_get_document(client: httpx.AsyncClient, profile_id: str) -> None:
    upload = await client.post(
        f"/api/v1/profiles/{profile_id}/knowledge",
        files={"file": ("doc.txt", b"Sample content for testing retrieval.")},
    )
    assert upload.status_code == 201
    doc_id = upload.json()["id"]

    response = await client.get(f"/api/v1/profiles/{profile_id}/knowledge/{doc_id}")
    assert response.status_code == 200
    doc = response.json()
    assert doc["id"] == doc_id
    assert "chunks" in doc


@pytest.mark.asyncio
async def test_delete_document(client: httpx.AsyncClient, profile_id: str) -> None:
    upload = await client.post(
        f"/api/v1/profiles/{profile_id}/knowledge",
        files={"file": ("delete_me.txt", b"Will be deleted.")},
    )
    assert upload.status_code == 201
    doc_id = upload.json()["id"]

    delete_response = await client.delete(f"/api/v1/profiles/{profile_id}/knowledge/{doc_id}")
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/profiles/{profile_id}/knowledge/{doc_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_reject_unsupported_file(client: httpx.AsyncClient, profile_id: str) -> None:
    response = await client.post(
        f"/api/v1/profiles/{profile_id}/knowledge",
        files={"file": ("image.png", b"not actually an image")},
    )
    assert response.status_code == 400
