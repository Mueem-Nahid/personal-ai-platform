from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_session
from renderers.base import RenderError
from renderers.pdf_import import import_pdf
from renderers.registry import capabilities
from schemas.render import PdfImportOut, RenderFormatsOut
from schemas.resume import ResumeContent
from schemas.template import (
    ResumeTemplateCreate,
    ResumeTemplateListOut,
    ResumeTemplateOut,
    ResumeTemplateUpdate,
    TemplatePreviewRequest,
)
from services.template_service import TemplateService

router = APIRouter()

_UPLOAD_EXTENSIONS = {"html": "html", "htm": "html", "typ": "typst", "tex": "latex", "docx": "docx"}


@router.get("", response_model=ResumeTemplateListOut)
async def list_templates(
    profile_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> ResumeTemplateListOut:
    service = TemplateService(session)
    templates = await service.list_templates(profile_id)
    return ResumeTemplateListOut(
        templates=[ResumeTemplateOut.model_validate(t) for t in templates],
        total=len(templates),
    )


@router.get("/formats", response_model=RenderFormatsOut)
async def render_formats() -> RenderFormatsOut:
    return RenderFormatsOut(formats=capabilities())


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ResumeTemplateOut)
async def create_template(
    body: ResumeTemplateCreate,
    session: AsyncSession = Depends(get_session),
) -> ResumeTemplateOut:
    if body.format != "docx" and not (body.source_text or "").strip():
        raise HTTPException(status_code=400, detail="source_text is required for text formats")
    service = TemplateService(session)
    template = await service.create(
        profile_id=body.profile_id,
        name=body.name,
        format=body.format,
        description=body.description,
        source_text=body.source_text,
        styles_text=body.styles_text,
    )
    return ResumeTemplateOut.model_validate(template)


@router.post("/upload", status_code=status.HTTP_201_CREATED, response_model=ResumeTemplateOut)
async def upload_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str | None = Form(None),
    profile_id: UUID | None = Form(None),
    session: AsyncSession = Depends(get_session),
) -> ResumeTemplateOut:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    template_format = _UPLOAD_EXTENSIONS.get(ext)
    if template_format is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported template file type: {ext}. Upload .html, .typ, .tex, or .docx",
        )

    data = await file.read()
    service = TemplateService(session)
    if template_format == "docx":
        asset_key = service.upload_docx_asset(data, file.filename)
        template = await service.create(
            profile_id=profile_id,
            name=name,
            format="docx",
            description=description,
            asset_key=asset_key,
        )
    else:
        template = await service.create(
            profile_id=profile_id,
            name=name,
            format=template_format,
            description=description,
            source_text=data.decode("utf-8", errors="replace"),
        )
    return ResumeTemplateOut.model_validate(template)


@router.post("/preview")
async def preview_template(
    body: TemplatePreviewRequest,
    session: AsyncSession = Depends(get_session),
) -> Response:
    service = TemplateService(session)
    content = ResumeContent(**body.content) if body.content else None
    try:
        pdf_bytes = await service.render_preview(
            format=body.format,
            source_text=body.source_text,
            styles_text=body.styles_text,
            content=content,
            profile_id=body.profile_id,
        )
    except RenderError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="preview.pdf"'},
    )


@router.post("/import-pdf", response_model=PdfImportOut)
async def import_pdf_resume(
    file: UploadFile = File(...),
) -> PdfImportOut:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="A .pdf file is required")
    data = await file.read()
    try:
        result = import_pdf(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return PdfImportOut(
        content=result.content,
        name=result.name,
        title=result.title,
        contact=result.contact,
    )


@router.get("/{template_id}", response_model=ResumeTemplateOut)
async def get_template(
    template_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> ResumeTemplateOut:
    service = TemplateService(session)
    template = await service.get(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return ResumeTemplateOut.model_validate(template)


@router.put("/{template_id}", response_model=ResumeTemplateOut)
async def update_template(
    template_id: UUID,
    body: ResumeTemplateUpdate,
    session: AsyncSession = Depends(get_session),
) -> ResumeTemplateOut:
    service = TemplateService(session)
    try:
        template = await service.update(
            template_id,
            name=body.name,
            description=body.description,
            source_text=body.source_text,
            styles_text=body.styles_text,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    return ResumeTemplateOut.model_validate(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_template(
    template_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    service = TemplateService(session)
    try:
        await service.delete(template_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err


@router.post("/{template_id}/default", response_model=ResumeTemplateOut)
async def set_default_template(
    template_id: UUID,
    profile_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> ResumeTemplateOut:
    service = TemplateService(session)
    try:
        template = await service.set_default(template_id, profile_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    return ResumeTemplateOut.model_validate(template)
