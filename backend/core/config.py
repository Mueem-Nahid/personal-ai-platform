from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        extra="ignore",
    )

    app_name: str = "Career Agent API"
    app_version: str = "0.1.0"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    database_url: str = "postgresql+asyncpg://agent:agent_secret@localhost:5432/career_agent"
    database_echo: bool = False

    redis_url: str = "redis://localhost:6379/0"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "career_agent"

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"
    ollama_embed_model: str = "bge-m3"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "career-agent"
    minio_secure: bool = False

    prompts_path: Path = Path("../prompts")

    encryption_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
