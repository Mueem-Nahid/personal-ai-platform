from __future__ import annotations

import logging
import uuid
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from core.config import settings
from parsers.llm_provider import complete
from schemas.resume import ResumeContent
from utils.json_repair import repair_json

logger = logging.getLogger(__name__)

_PROMPT_PATH = settings.prompts_path / "cv" / "customize.md"
_EXPECTED_FIELDS = frozenset({"summary", "sections"})


class ResumeBuilderState(TypedDict):
    version_id: str
    profile_id: str
    job_id: str
    master_resume_id: str
    master_document_id: str
    raw_job_text: str
    job_parsed_fields: dict
    cv_full_text: str
    retrieved_chunks: list[str]
    retrieved_chunk_ids: list[str]
    evidence_text: str
    prompt: str
    raw_response: str
    content: dict | None
    content_text: str
    error: str | None
    provider: str
    model: str
    prompt_version: str


def _load_prompt() -> str:
    from utils.prompt_loader import load_prompt

    body, _metadata = load_prompt(_PROMPT_PATH)
    return body


async def retrieve_job_and_master(state: ResumeBuilderState) -> ResumeBuilderState:
    from sqlalchemy import select

    from core.database import SessionLocal
    from models.job import JobPost
    from models.knowledge import Document
    from models.knowledge import DocumentChunk
    from models.resume import MasterResume

    async with SessionLocal() as session:
        job = await session.get(JobPost, uuid.UUID(state["job_id"]))
        if not job:
            state["error"] = f"JobPost {state['job_id']} not found"
            return state

        raw_text = job.raw_text or ""
        max_chars = settings.llm_max_text_chars
        if len(raw_text) > max_chars:
            raw_text = raw_text[:max_chars]
        state["raw_job_text"] = raw_text
        state["job_parsed_fields"] = job.parsed_fields or {}

        master = await session.get(MasterResume, uuid.UUID(state["master_resume_id"]))
        if not master:
            state["error"] = f"MasterResume {state['master_resume_id']} not found"
            return state

        doc = await session.get(Document, master.document_id)
        if not doc:
            state["error"] = f"Document {master.document_id} not found for master resume"
            return state

        if doc.extracted_text:
            text = doc.extracted_text
        else:
            stmt = (
                select(DocumentChunk.text_content)
                .where(DocumentChunk.document_id == doc.id)
                .order_by(DocumentChunk.chunk_index)
            )
            result = await session.execute(stmt)
            chunk_texts = list(result.scalars().all())
            text = "\n\n".join(chunk_texts)

        master_limit = settings.resume_max_master_chars
        if len(text) > master_limit:
            text = text[:master_limit] + "\n\n[master resume truncated for length]"
        state["cv_full_text"] = text
        state["master_document_id"] = str(doc.id)

    return state


async def vector_context(state: ResumeBuilderState) -> ResumeBuilderState:
    if state["error"]:
        return state
    try:
        from services.embedding_service import EmbeddingService
        from services.qdrant_service import QdrantService

        if not state["raw_job_text"]:
            state["retrieved_chunks"] = []
            state["retrieved_chunk_ids"] = []
            return state

        query = state["raw_job_text"]
        max_chars = settings.llm_max_text_chars
        if len(query) > max_chars:
            query = query[:max_chars]

        embedding_svc = EmbeddingService()
        qdrant_svc = QdrantService()
        embedding = await embedding_svc.embed_single(query)

        results = await qdrant_svc.search_in_document(
            embedding,
            uuid.UUID(state["profile_id"]),
            uuid.UUID(state["master_document_id"]),
            limit=settings.resume_top_k,
        )

        chunk_ids = [uuid.UUID(r["id"]) for r in results if r.get("id")]
        state["retrieved_chunk_ids"] = [str(cid) for cid in chunk_ids]
        state["retrieved_chunks"] = await _fetch_chunk_texts(chunk_ids)
    except Exception:
        logger.exception("Vector context retrieval failed, continuing without evidence")
        state["retrieved_chunks"] = []
        state["retrieved_chunk_ids"] = []
    return state


async def _fetch_chunk_texts(point_ids: list[uuid.UUID]) -> list[str]:
    if not point_ids:
        return []
    from sqlalchemy import select

    from core.database import SessionLocal
    from models.knowledge import DocumentChunk

    async with SessionLocal() as session:
        stmt = select(DocumentChunk.text_content).where(
            DocumentChunk.qdrant_point_id.in_(point_ids),
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def build_prompt(state: ResumeBuilderState) -> ResumeBuilderState:
    if state["error"]:
        return state
    template = _load_prompt()

    fields = state.get("job_parsed_fields", {})
    job_title = fields.get("title") or ""
    company = fields.get("company") or ""

    req_parts: list[str] = []
    for key in ("requirements", "responsibilities", "skills", "keywords"):
        values = fields.get(key)
        if values and isinstance(values, list):
            req_parts.append(f"{key}: {', '.join(values)}")
    if not req_parts:
        req_parts = ["(see full job description below)"]
    job_requirements = "\n".join(req_parts)

    if state["retrieved_chunks"]:
        evidence = "\n\n".join(state["retrieved_chunks"])
    else:
        fallback = state["cv_full_text"]
        evidence_limit = settings.resume_max_evidence_chars
        if len(fallback) > evidence_limit:
            fallback = fallback[:evidence_limit] + "\n\n[fallback master resume excerpt truncated]"
        evidence = fallback

    evidence_limit = settings.resume_max_evidence_chars
    if len(evidence) > evidence_limit:
        evidence = evidence[:evidence_limit] + "\n\n[evidence truncated for length]"

    user_skills = fields.get("skills") or []

    state["evidence_text"] = evidence
    state["prompt"] = (
        template.replace("{{ job_title }}", job_title or "Unknown")
        .replace("{{ company }}", company or "Unknown")
        .replace("{{ job_requirements }}", job_requirements)
        .replace("{{ cv_sections }}", evidence)
        .replace("{{ user_skills }}", ", ".join(user_skills) if user_skills else "No skills extracted")
    )
    state["prompt_version"] = "v2"
    return state


async def tailor(state: ResumeBuilderState) -> ResumeBuilderState:
    if state["error"]:
        return state
    try:
        raw = await complete(
            state["prompt"],
            json_mode=True,
            max_tokens=settings.resume_max_tokens,
            temperature=settings.resume_temperature,
        )
        state["raw_response"] = raw
        state["content"] = repair_json(raw, _EXPECTED_FIELDS)
        state["provider"] = settings.llm_provider
        state["model"] = settings.llm_model
    except Exception as e:
        error_str = str(e)
        if "413" in error_str or "Payload Too Large" in error_str:
            state["error"] = (
                "Resume builder prompt too large for Groq free tier. "
                "Try using a smaller master resume or reducing resume_top_k."
            )
        else:
            state["error"] = error_str
        logger.exception("LLM resume tailoring call failed")
    return state


async def validate(state: ResumeBuilderState) -> ResumeBuilderState:
    if state["error"]:
        return state
    if state["content"] is None:
        state["error"] = "No content produced; LLM returned no valid data"
        return state
    try:
        validated = ResumeContent(**state["content"])
        state["content"] = validated.model_dump()

        lines: list[str] = []
        if validated.summary:
            lines.append(validated.summary)
        for section in validated.sections:
            lines.append(f"\n## {section.name}")
            for item in section.items:
                lines.append(f"- {item}")
        state["content_text"] = "\n".join(lines)
    except Exception as e:
        state["error"] = f"Resume content validation failed: {e}"
    return state


def build_graph() -> StateGraph:
    builder = StateGraph(ResumeBuilderState)
    builder.add_node("retrieve", retrieve_job_and_master)
    builder.add_node("vector_context", vector_context)
    builder.add_node("build_prompt", build_prompt)
    builder.add_node("tailor", tailor)
    builder.add_node("validate", validate)
    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "vector_context")
    builder.add_edge("vector_context", "build_prompt")
    builder.add_edge("build_prompt", "tailor")
    builder.add_edge("tailor", "validate")
    builder.add_edge("validate", END)
    return builder


_graph = build_graph().compile()
