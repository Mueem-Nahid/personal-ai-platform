from __future__ import annotations

import json
import logging
import re
from functools import lru_cache

from core.config import settings
from parsers.llm_provider import complete
from schemas.job import JobParsedFields

logger = logging.getLogger(__name__)

_PROMPT_PATH = settings.prompts_path / "parsing" / "job-post.md"
_json_fence = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL)

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


def _repair_json(raw: str) -> dict:
    m = _json_fence.search(raw)
    if m:
        raw = m.group(1).strip()

    parsed = None
    exceptions: list[Exception] = []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        exceptions.append(e)

    if parsed is None:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            raw = raw[start : end + 1]
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            exceptions.append(e)

    if parsed is None:
        msg = "Failed to parse LLM response as JSON"
        logger.warning("%s:\n%s", msg, raw)
        raise ValueError(msg) from (exceptions[0] if exceptions else None)

    if not any(k in parsed for k in _EXPECTED_FIELDS):
        raise ValueError(
            f"LLM response JSON missing all expected fields; got keys: {list(parsed.keys())}"
        )

    return parsed
