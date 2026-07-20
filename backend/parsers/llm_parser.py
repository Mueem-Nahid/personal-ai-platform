from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path

from ollama import AsyncClient

from core.config import settings
from schemas.job import JobParsedFields

logger = logging.getLogger(__name__)

_PROMPT_PATH = settings.prompts_path / "parsing" / "job-post.md"
_json_fence = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL)

MAX_TEXT_CHARS = 6000


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


async def llm_parse(text: str) -> JobParsedFields:
    template = _load_prompt()

    if len(text) > MAX_TEXT_CHARS:
        orig_len = len(text)
        text = text[:MAX_TEXT_CHARS]
        logger.info("Truncated job text from %d to %d chars", orig_len, MAX_TEXT_CHARS)

    prompt = template.replace("{{ job_text }}", text)

    raw = await _call_llm(prompt)
    parsed = _repair_json(raw)

    return JobParsedFields(
        title=parsed.get("title"),
        company=parsed.get("company"),
        location=parsed.get("location"),
        salary=parsed.get("salary"),
        experience=parsed.get("experience"),
        employment_type=parsed.get("employment_type"),
        requirements=parsed.get("requirements") or [],
        responsibilities=parsed.get("responsibilities") or [],
        skills=parsed.get("skills") or [],
        keywords=parsed.get("keywords") or [],
        tech_stack=parsed.get("tech_stack") or [],
    )


async def _call_llm(prompt: str) -> str:
    client = AsyncClient(host=settings.ollama_url)
    try:
        response = await asyncio.wait_for(
            client.generate(
                model=settings.ollama_model,
                prompt=prompt,
                options={"temperature": 0.1, "num_predict": 1024},
            ),
            timeout=300.0,
        )
    except asyncio.TimeoutError:
        logger.error("LLM call timed out after 120s")
        raise
    return response.response.strip()


def _repair_json(raw: str) -> dict:
    m = _json_fence.search(raw)
    if m:
        raw = m.group(1).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start : end + 1]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM response as JSON:\n%s", raw)
        return {}
