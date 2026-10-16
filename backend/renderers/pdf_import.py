from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from io import BytesIO

import pdfplumber

from schemas.resume import ResumeContent, ResumeSection

KNOWN_HEADINGS = frozenset(
    {
        "summary",
        "objective",
        "profile",
        "professional summary",
        "about",
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "employment history",
        "education",
        "skills",
        "technical skills",
        "core competencies",
        "projects",
        "certifications",
        "certificates",
        "achievements",
        "awards",
        "publications",
        "languages",
        "interests",
        "volunteer experience",
        "volunteering",
        "references",
        "activities",
        "coursework",
    }
)

_SUMMARY_HEADINGS = frozenset(
    {"summary", "objective", "profile", "professional summary", "about", "about me"}
)

_BULLET_PREFIXES = ("•", "●", "▪", "◦", "‣", "·", "►", "■", "□", "-", "–", "—", "*")

_PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")

@dataclass
class PdfImportResult:
    content: ResumeContent
    name: str | None = None
    title: str | None = None
    contact: str | None = None


@dataclass
class _Line:
    size: float
    text: str
    top: float


def _is_heading(line: _Line, body_size: float) -> bool:
    text = line.text
    stripped = text.strip(" :").lower()
    if stripped in KNOWN_HEADINGS:
        return True
    if len(text) <= 60 and text.endswith(":") and text.count(" ") <= 4:
        return True
    if line.size >= body_size * 1.15 and len(text) <= 60 and text == text.upper():
        return len(text) > 3
    return False


def _is_bullet(text: str) -> bool:
    if text[:2] in ("- ", "* "):
        return True
    return len(text) > 1 and text[0] in _BULLET_PREFIXES and not text[0].isalnum()


def _clean_bullet(text: str) -> str:
    stripped = text.lstrip()
    if stripped[:2] in ("- ", "* "):
        return stripped[2:].strip()
    if stripped and stripped[0] in _BULLET_PREFIXES:
        return stripped[1:].strip()
    return stripped


def _is_contact(text: str) -> bool:
    return "@" in text or bool(_PHONE_RE.search(text))


def import_pdf(data: bytes) -> PdfImportResult:
    """Extract resume content from a PDF via layout heuristics.

    Uses font size + known heading names to split sections; bullets become items,
    wrapped non-bullet lines merge into the previous item. Fully local (pdfplumber).
    """
    lines: list[_Line] = []
    try:
        with pdfplumber.open(BytesIO(data)) as pdf:
            for page in pdf.pages:
                for raw in page.extract_text_lines():
                    text = (raw.get("text") or "").strip()
                    if not text:
                        continue
                    chars = raw.get("chars") or []
                    sizes = [c["size"] for c in chars if c.get("size")]
                    size = statistics.median(sizes) if sizes else 12.0
                    lines.append(_Line(size=size, text=text, top=raw.get("top", 0.0)))
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Could not read PDF: {e}") from e

    if not lines:
        raise ValueError("No extractable text found in PDF (scanned/image PDFs are not supported)")

    rounded_sizes = [round(line.size, 1) for line in lines]
    try:
        body_size = statistics.mode(rounded_sizes)
    except statistics.StatisticsError:
        body_size = statistics.median(rounded_sizes)

    name: str | None = None
    title: str | None = None
    contact: str | None = None

    cursor = 0
    if lines and lines[0].size >= body_size * 1.3 and len(lines[0].text) <= 60:
        name = lines[0].text
        cursor = 1
        if (
            len(lines) > 1
            and lines[1].size >= body_size * 1.1
            and len(lines[1].text) <= 80
            and not _is_heading(lines[1], body_size)
            and not _is_bullet(lines[1].text)
        ):
            title = lines[1].text
            cursor = 2
    while cursor < len(lines) and _is_contact(lines[cursor].text) and len(lines[cursor].text) <= 120:  # noqa: E501
        contact = lines[cursor].text if contact is None else f"{contact} | {lines[cursor].text}"
        cursor += 1

    summary_parts: list[str] = []
    sections: list[ResumeSection] = []
    current: ResumeSection | None = None
    last_was_wrapped = False

    for line in lines[cursor:]:
        text = line.text.strip()
        if not text:
            continue
        if _is_heading(line, body_size):
            heading = text.strip(" :")
            normalized = heading.lower()
            if heading.isupper():
                heading = heading.title()
            if normalized in _SUMMARY_HEADINGS:
                current = None
                last_was_wrapped = False
                continue
            current = ResumeSection(name=heading, items=[])
            sections.append(current)
            last_was_wrapped = False
            continue
        if current is None:
            if _is_contact(text) and not summary_parts:
                continue
            summary_parts.append(text)
            continue
        if _is_bullet(text):
            current.items.append(_clean_bullet(text))
            last_was_wrapped = False
        else:
            if current.items and last_was_wrapped:
                current.items[-1] = f"{current.items[-1]} {text}"
            else:
                current.items.append(text)
                last_was_wrapped = True

    summary = " ".join(part.strip() for part in summary_parts).strip()
    summary_text: str | None = summary if len(summary) > 10 else None
    sections = [s for s in sections if s.items]

    return PdfImportResult(
        content=ResumeContent(summary=summary_text, sections=sections),
        name=name,
        title=title,
        contact=contact,
    )
