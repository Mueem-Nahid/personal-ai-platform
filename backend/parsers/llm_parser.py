from __future__ import annotations

import logging
from functools import lru_cache

from core.config import settings
from parsers.llm_provider import complete
from schemas.job import JobParsedFields
from utils.json_repair import repair_json

logger = logging.getLogger(__name__)

_PROMPT_PATH = settings.prompts_path / "parsing" / "job-post.md"

_EXPECTED_FIELDS = frozenset(JobParsedFields.model_fields.keys())


@lru_cache
def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


async def llm_parse(text: str) -> JobParsedFields:
    template = _load_prompt()

    max_chars = settings.llm_max_text_chars
    if len(text) > max_chars:
        orig_len = len(text)
        text = text[:max_chars]
        logger.info("Truncated job text from %d to %d chars", orig_len, max_chars)

    prompt = template.replace("{{ job_text }}", text)

    raw = await complete(
        prompt,
        json_mode=True,
        max_tokens=settings.llm_max_tokens,
        temperature=settings.llm_temperature,
    )
    parsed = repair_json(raw, expected_fields=_EXPECTED_FIELDS)

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
