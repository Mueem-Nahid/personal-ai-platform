from __future__ import annotations

import logging

from parsers.extractors import find_salary
from parsers.llm_parser import llm_parse
from schemas.job import JobParsedFields

logger = logging.getLogger(__name__)


async def parse_job_text(raw_text: str) -> tuple[str, JobParsedFields | None, str]:
    try:
        fields = await llm_parse(raw_text)
    except Exception:
        logger.exception("LLM parsing failed")
        return raw_text, None, "failed"

    _post_fill_salary(raw_text, fields)

    return raw_text, fields, "parsed"


def _post_fill_salary(raw_text: str, fields: JobParsedFields) -> None:
    if fields.salary:
        return
    regex_result = find_salary(raw_text)
    if regex_result:
        fields.salary = regex_result
