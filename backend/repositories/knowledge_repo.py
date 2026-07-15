from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.knowledge import Document, DocumentChunk


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, document: Document) -> Document:
        self._session.add(document)
        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def get_with_chunks(self, document_id: UUID) -> Document | None:
        stmt = (
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.chunks))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_profile(self, profile_id: UUID) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.profile_id == profile_id)
            .order_by(Document.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, document: Document) -> Document:
        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def delete(self, document: Document) -> None:
        await self._session.delete(document)
        await self._session.flush()


class DocumentChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_create(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        self._session.add_all(chunks)
        await self._session.flush()
        for chunk in chunks:
            await self._session.refresh(chunk)
        return chunks

    async def delete_by_document(self, document_id: UUID) -> None:
        stmt = select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        result = await self._session.execute(stmt)
        for chunk in result.scalars():
            await self._session.delete(chunk)
        await self._session.flush()
