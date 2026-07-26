from __future__ import annotations

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "name" in body
    assert "version" in body


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness() -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_llm_health() -> None:
    response = client.get("/api/v1/health/llm")
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "groq"
    assert body["model"] == "llama-3.1-8b-instant"
    assert isinstance(body["groq_key_configured"], bool)
    assert isinstance(body["timeout_seconds"], float)
