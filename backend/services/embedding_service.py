from __future__ import annotations

from ollama import AsyncClient

from core.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        self._client = AsyncClient(host=settings.ollama_url)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self._client.embed(
            model=settings.ollama_embed_model,
            input=texts,
        )
        return response.embeddings

    async def embed_single(self, text: str) -> list[float]:
        results = await self.embed([text])
        return results[0]
