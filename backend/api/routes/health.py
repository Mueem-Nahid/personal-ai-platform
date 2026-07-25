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


@router.get("/health/llm")
async def llm_health() -> dict:
    return {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "timeout_seconds": settings.llm_timeout_seconds,
        "groq_key_configured": bool(settings.groq_api_key),
        "gemini_key_configured": bool(settings.gemini_api_key),
        "ollama_url": settings.ollama_url,
        "ollama_model": settings.ollama_model,
    }
