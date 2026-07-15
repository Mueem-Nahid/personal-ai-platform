from __future__ import annotations

import uuid

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from core.config import settings


class QdrantService:
    def __init__(self) -> None:
        self._client = AsyncQdrantClient(url=settings.qdrant_url)
        self._collection = settings.qdrant_collection

    async def ensure_collection(self) -> None:
        exists = await self._client.collection_exists(self._collection)
        if not exists:
            await self._client.create_collection(
                collection_name=self._collection,
                vectors_config=qmodels.VectorParams(size=1024, distance=qmodels.Distance.COSINE),
            )

    async def upsert_chunks(
        self, embeddings: list[list[float]], profile_id: uuid.UUID, document_id: uuid.UUID
    ) -> list[uuid.UUID]:
        await self.ensure_collection()
        points = []
        point_ids: list[uuid.UUID] = []
        for i, embedding in enumerate(embeddings):
            pid = uuid.uuid4()
            point_ids.append(pid)
            points.append(
                qmodels.PointStruct(
                    id=str(pid),
                    vector=embedding,
                    payload={
                        "profile_id": str(profile_id),
                        "document_id": str(document_id),
                        "chunk_index": i,
                    },
                )
            )
        await self._client.upsert(collection_name=self._collection, points=points)
        return point_ids

    async def delete_by_document(self, document_id: uuid.UUID) -> None:
        await self._client.delete(
            collection_name=self._collection,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=str(document_id)))]
                )
            ),
        )

    async def search(
        self, embedding: list[float], profile_id: uuid.UUID, limit: int = 5
    ) -> list[dict]:
        await self.ensure_collection()
        results = await self._client.search(
            collection_name=self._collection,
            query_vector=embedding,
            query_filter=qmodels.Filter(
                must=[qmodels.FieldCondition(key="profile_id", match=qmodels.MatchValue(value=str(profile_id)))]
            ),
            limit=limit,
            with_payload=True,
        )
        return [{"id": r.id, "score": r.score, "payload": r.payload} for r in results]
