from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)

_json_fence = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL)


def repair_json(raw: str, expected_fields: frozenset[str] | None = None) -> dict:
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

    if expected_fields and not any(k in parsed for k in expected_fields):
        raise ValueError(
            f"LLM response JSON missing all expected fields; got keys: {list(parsed.keys())}"
        )

    return parsed
