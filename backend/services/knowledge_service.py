from __future__ import annotations

import asyncio
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from models.knowledge import Document, DocumentChunk
from repositories.knowledge_repo import DocumentChunkRepository, DocumentRepository
from services.chunking_service import ChunkingService
from services.embedding_service import EmbeddingService
from services.extraction_service import ExtractionService
from services.minio_service import MinioService
from services.qdrant_service import QdrantService

logger = logging.getLogger(__name__)


class KnowledgeService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._doc_repo = DocumentRepository(session)
        self._chunk_repo = DocumentChunkRepository(session)
        self._minio = MinioService()
        self._extraction = ExtractionService()
        self._chunking = ChunkingService()
        self._embedding = EmbeddingService()
        self._qdrant = QdrantService()

    async def upload_and_process(
        self,
        profile_id: uuid.UUID,
        filename: str,
        file_type: str,
        file_data: bytes,
        file_size: int,
    ) -> Document:
        object_key = await asyncio.to_thread(self._minio.upload, file_data, filename)
        document = Document(
            profile_id=profile_id,
            filename=filename,
            file_type=file_type,
            file_size_bytes=file_size,
            minio_object_key=object_key,
            status="uploaded",
        )
        document = await self._doc_repo.create(document)

        try:
            document = await self._process(document, file_data)
        except Exception:
            logger.exception("Error processing document %s", document.id)
            document.status = "failed"
            document = await self._doc_repo.update(document)

        return document

    async def _process(self, document: Document, file_data: bytes) -> Document:
        document.status = "processing"
        document = await self._doc_repo.update(document)

        text = self._extraction.extract(file_data, document.file_type)
        document.extracted_text = text
        chunks_text = self._chunking.chunk(text)
        if not chunks_text:
            document.status = "failed"
            return await self._doc_repo.update(document)

        embeddings = await self._embedding.embed(chunks_text)
        point_ids = await self._qdrant.upsert_chunks(embeddings, document.profile_id, document.id)

        db_chunks = [
            DocumentChunk(
                document_id=document.id,
                profile_id=document.profile_id,
                chunk_index=i,
                text_content=chunks_text[i],
                qdrant_point_id=point_ids[i],
            )
            for i in range(len(chunks_text))
        ]
        await self._chunk_repo.bulk_create(db_chunks)

        document.status = "processed"
        document.chunk_count = len(chunks_text)
        return await self._doc_repo.update(document)

    async def get_document(self, document_id: uuid.UUID) -> Document | None:
        return await self._doc_repo.get_with_chunks(document_id)

    async def list_documents(self, profile_id: uuid.UUID) -> list[Document]:
        return await self._doc_repo.list_by_profile(profile_id)

    async def delete_document(self, document_id: uuid.UUID, profile_id: uuid.UUID) -> None:
        document = await self._doc_repo.get_with_chunks(document_id)
        if document is None or str(document.profile_id) != str(profile_id):
            raise ValueError(f"Document {document_id} not found")
        if document.minio_object_key:
            await asyncio.to_thread(self._minio.delete, document.minio_object_key)
        await self._qdrant.delete_by_document(document_id)
        await self._doc_repo.delete(document)
