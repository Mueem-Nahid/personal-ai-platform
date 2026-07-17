from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DocumentChunkBase(BaseModel):
    chunk_index: int
    text_content: str
    qdrant_point_id: UUID | None = None


class DocumentChunkOut(DocumentChunkBase, ORMBase):
    id: UUID
    document_id: UUID
    profile_id: UUID
    created_at: datetime


class DocumentBase(BaseModel):
    filename: str
    file_type: str
    file_size_bytes: int | None = None


class DocumentOut(DocumentBase, ORMBase):
    id: UUID
    profile_id: UUID
    status: str
    chunk_count: int | None = None
    extra_metadata: dict | None = None
    created_at: datetime
    updated_at: datetime
    chunks: list[DocumentChunkOut] = []


class DocumentListOut(BaseModel):
    documents: list[DocumentOut]
    total: int
