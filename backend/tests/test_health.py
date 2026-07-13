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
