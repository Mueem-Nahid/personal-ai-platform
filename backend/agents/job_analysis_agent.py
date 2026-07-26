from __future__ import annotations

import logging
import uuid
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from agents.profile_digest import build_digest
from core.config import settings
from parsers.llm_provider import complete
from schemas.job_analysis import JobAnalysisReport
from utils.json_repair import repair_json

logger = logging.getLogger(__name__)

_PROMPT_PATH = settings.prompts_path / "analysis" / "job-fit.md"
_EXPECTED_FIELDS = frozenset(JobAnalysisReport.model_fields.keys())


class AnalysisState(TypedDict):
    analysis_id: str
    job_id: str
    profile_id: str
    raw_job_text: str
    profile_digest: str
    retrieved_chunks: list[str]
    prompt: str
    report: dict | None
    error: str | None
    provider: str
    model: str
    prompt_version: str


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


async def retrieve_job_and_profile(state: AnalysisState) -> AnalysisState:
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from core.database import SessionLocal
    from models.job import JobPost
    from models.profile import Profile

    async with SessionLocal() as session:
        job = await session.get(JobPost, uuid.UUID(state["job_id"]))
        if not job:
            state["error"] = f"JobPost {state['job_id']} not found"
            return state
        state["raw_job_text"] = job.raw_text or ""

        stmt = (
            select(Profile)
            .where(Profile.id == uuid.UUID(state["profile_id"]))
            .options(
                selectinload(Profile.experiences),
                selectinload(Profile.projects),
                selectinload(Profile.education),
                selectinload(Profile.skills),
                selectinload(Profile.certificates),
                selectinload(Profile.achievements),
                selectinload(Profile.publications),
                selectinload(Profile.languages),
            )
        )
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()
        if not profile:
            state["error"] = f"Profile {state['profile_id']} not found"
            return state
        state["profile_digest"] = build_digest(profile)

    return state


async def vector_context(state: AnalysisState) -> AnalysisState:
    if state["error"]:
        return state
    try:
        from services.embedding_service import EmbeddingService
        from services.qdrant_service import QdrantService

        if not state["raw_job_text"]:
            state["retrieved_chunks"] = []
            return state

        query = state["raw_job_text"]
        max_chars = settings.llm_max_text_chars
        if len(query) > max_chars:
            query = query[:max_chars]

        embedding_svc = EmbeddingService()
        qdrant_svc = QdrantService()
        embedding = await embedding_svc.embed_single(query)
        results = await qdrant_svc.search(
            embedding, uuid.UUID(state["profile_id"]), limit=6
        )

        doc_chunk_ids = [
            uuid.UUID(r["payload"]["document_id"])
            for r in results
            if r.get("payload") and r["payload"].get("document_id")
        ]
        chunk_indices = [
            r["payload"].get("chunk_index")
            for r in results
            if r.get("payload") and r["payload"].get("chunk_index") is not None
        ]
        state["retrieved_chunks"] = await _fetch_chunk_texts(
            doc_chunk_ids, chunk_indices, uuid.UUID(state["profile_id"])
        )
    except Exception:
        logger.exception("Vector context retrieval failed, continuing without evidence")
        state["retrieved_chunks"] = []
    return state


async def _fetch_chunk_texts(
    document_ids: list[uuid.UUID],
    chunk_indices: list[int],
    profile_id: uuid.UUID,
) -> list[str]:
    if not document_ids:
        return []
    from sqlalchemy import select

    from core.database import SessionLocal
    from models.knowledge import DocumentChunk

    async with SessionLocal() as session:
        stmt = select(DocumentChunk.text_content).where(
            DocumentChunk.profile_id == profile_id,
            DocumentChunk.document_id.in_(document_ids),
            DocumentChunk.chunk_index.in_(chunk_indices),
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def build_prompt(state: AnalysisState) -> AnalysisState:
    if state["error"]:
        return state
    template = _load_prompt()
    raw_text = state["raw_job_text"]
    max_chars = settings.llm_max_text_chars
    if len(raw_text) > max_chars:
        raw_text = raw_text[:max_chars]

    evidence = (
        "\n".join(state["retrieved_chunks"])
        if state["retrieved_chunks"]
        else "No relevant CV sections found."
    )
    state["prompt"] = (
        template.replace("{{ job_description }}", raw_text)
        .replace("{{ candidate_profile }}", state["profile_digest"])
        .replace("{{ retrieved_evidence }}", evidence)
    )
    state["prompt_version"] = "v1"
    return state


async def analyze(state: AnalysisState) -> AnalysisState:
    if state["error"]:
        return state
    try:
        raw = await complete(
            state["prompt"],
            json_mode=True,
            max_tokens=2048,
            temperature=0.3,
        )
        state["report"] = repair_json(raw, _EXPECTED_FIELDS)
        state["provider"] = settings.llm_provider
        state["model"] = settings.llm_model
    except Exception as e:
        state["error"] = str(e)
        logger.exception("LLM analysis call failed")
    return state


async def validate(state: AnalysisState) -> AnalysisState:
    if state["error"]:
        return state
    if state["report"] is None:
        state["error"] = "No report produced; LLM returned no valid data"
        return state
    try:
        JobAnalysisReport(**state["report"])
    except Exception as e:
        logger.warning("Report validation warning: %s", e)
    return state


def build_graph() -> StateGraph:
    builder = StateGraph(AnalysisState)
    builder.add_node("retrieve", retrieve_job_and_profile)
    builder.add_node("vector_context", vector_context)
    builder.add_node("build_prompt", build_prompt)
    builder.add_node("analyze", analyze)
    builder.add_node("validate", validate)
    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "vector_context")
    builder.add_edge("vector_context", "build_prompt")
    builder.add_edge("build_prompt", "analyze")
    builder.add_edge("analyze", "validate")
    builder.add_edge("validate", END)
    return builder


_graph = build_graph().compile()
