from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from services.qdrant_service import QdrantService


@pytest.mark.asyncio
async def test_delete_document_without_vector_collection() -> None:
    client = AsyncMock()
    client.collection_exists.return_value = False
    with patch("services.qdrant_service.AsyncQdrantClient", return_value=client):
        service = QdrantService()

    await service.delete_by_document(uuid.uuid4())

    client.collection_exists.assert_awaited_once_with(service._collection)
    client.delete.assert_not_awaited()
    client.create_collection.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_document_filters_existing_collection() -> None:
    client = AsyncMock()
    client.collection_exists.return_value = True
    with patch("services.qdrant_service.AsyncQdrantClient", return_value=client):
        service = QdrantService()
    document_id = uuid.uuid4()

    await service.delete_by_document(document_id)

    client.delete.assert_awaited_once()
    arguments = client.delete.await_args.kwargs
    assert arguments["collection_name"] == service._collection
    condition = arguments["points_selector"].filter.must[0]
    assert condition.key == "document_id"
    assert condition.match.value == str(document_id)


@pytest.mark.asyncio
async def test_delete_document_propagates_vector_store_failure() -> None:
    client = AsyncMock()
    client.collection_exists.side_effect = ConnectionError("Qdrant unavailable")
    with patch("services.qdrant_service.AsyncQdrantClient", return_value=client):
        service = QdrantService()

    with pytest.raises(ConnectionError, match="Qdrant unavailable"):
        await service.delete_by_document(uuid.uuid4())

    client.delete.assert_not_awaited()
