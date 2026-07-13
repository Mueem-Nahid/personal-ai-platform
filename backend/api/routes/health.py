from __future__ import annotations

from fastapi import APIRouter

from core.config import settings

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/health/ready")
async def readiness() -> dict[str, str]:
    return {"status": "ready"}
