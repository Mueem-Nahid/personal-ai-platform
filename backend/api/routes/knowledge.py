from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_session
from schemas.knowledge import DocumentOut, DocumentListOut
from services.knowledge_service import KnowledgeService

router = APIRouter()


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    profile_id: UUID,
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
) -> DocumentOut:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "txt"
    if ext not in ("pdf", "docx", "doc", "txt", "md"):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    data = await file.read()
    service = KnowledgeService(session)
    document = await service.upload_and_process(
        profile_id=profile_id,
        filename=file.filename,
        file_type=ext,
        file_data=data,
        file_size=len(data),
    )
    return DocumentOut.model_validate(document)


@router.get("", response_model=DocumentListOut)
async def list_documents(
    profile_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> DocumentListOut:
    service = KnowledgeService(session)
    documents = await service.list_documents(profile_id)
    return DocumentListOut(
        documents=[DocumentOut.model_validate(d) for d in documents],
        total=len(documents),
    )


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    profile_id: UUID,
    document_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> DocumentOut:
    service = KnowledgeService(session)
    document = await service.get_document(document_id)
    if document is None or str(document.profile_id) != str(profile_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentOut.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_document(
    profile_id: UUID,
    document_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    service = KnowledgeService(session)
    try:
        await service.delete_document(document_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Document not found")
