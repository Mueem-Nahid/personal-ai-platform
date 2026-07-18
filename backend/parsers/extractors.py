from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

_SALARY_RE = re.compile(
    r"(?i)"
    r"(?:salary|compensation|pay|rate)"
    r"[:\s]*"
    r"(?:range[:\s]*)?"
    r"(?:up to\s*)?"
    r"[\$\€\£]\s*"
    r"([\d,]+(?:\.\d{1,2})?)\s*[kK]?"
    r"(?:\s*[-–—]+\s*[\$\€\£]?\s*([\d,]+(?:\.\d{1,2})?)\s*[kK]?)?"
    r"(?:\s*(?:/|\sper\s)\s*(?:year|yr|annually|month|mo|hour|hr))?"
)


def find_salary(text: str) -> str | None:
    match = _SALARY_RE.search(text)
    if not match:
        return None
    a = match.group(1)
    b = match.group(2)
    return f"${a} – ${b}" if b else f"${a}"


def find_emails(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)


_NAMED_ENTITY = None


def _get_spacy():
    global _NAMED_ENTITY
    if _NAMED_ENTITY is not None:
        return _NAMED_ENTITY
    try:
        import spacy
        _NAMED_ENTITY = spacy.load("en_core_web_sm")
    except Exception:
        logger.warning("spaCy model not available — NER disabled")
        _NAMED_ENTITY = False
    return _NAMED_ENTITY


def extract_orgs(text: str) -> list[str]:
    nlp = _get_spacy()
    if not nlp:
        return []
    doc = nlp(text[:10000])
    seen: set[str] = set()
    orgs: list[str] = []
    for ent in doc.ents:
        if ent.label_ == "ORG" and ent.text not in seen:
            seen.add(ent.text)
            orgs.append(ent.text)
    return orgs[:10]


def extract_locations(text: str) -> list[str]:
    nlp = _get_spacy()
    if not nlp:
        return []
    doc = nlp(text[:10000])
    seen: set[str] = set()
    locs: list[str] = []
    for ent in doc.ents:
        if ent.label_ in ("GPE", "LOC") and ent.text not in seen:
            seen.add(ent.text)
            locs.append(ent.text)
    return locs[:10]
