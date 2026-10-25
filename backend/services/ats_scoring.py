"""Local, reproducible checks on resume content; never calls an LLM."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import UTC, datetime
from uuid import UUID

from schemas.ats import AtsCheck, AtsReport, AtsSuggestion
from schemas.resume import ResumeContent

SCORING_VERSION = "1.0"
_VERBS = set(
    [
        "achieved",
        "automated",
        "built",
        "coached",
        "collaborated",
        "created",
        "cut",
        "decreased",
        "delivered",
        "deployed",
        "designed",
        "developed",
        "directed",
        "drove",
        "enabled",
        "engineered",
        "established",
        "expanded",
        "implemented",
        "improved",
        "increased",
        "integrated",
        "launched",
        "led",
        "maintained",
        "managed",
        "mentored",
        "migrated",
        "optimized",
        "orchestrated",
        "organized",
        "owned",
        "performed",
        "planned",
        "produced",
        "published",
        "reduced",
        "refactored",
        "resolved",
        "scaled",
        "shipped",
        "simplified",
        "streamlined",
        "supported",
        "tested",
        "trained",
        "transformed",
        "analyzed",
        "coordinated",
        "conducted",
        "documented",
        "evaluated",
        "generated",
        "introduced",
        "negotiated",
        "restructured",
        "secured",
        "supervised",
        "upgraded",
        "validated",
        "wrote",
        "build",
        "design",
        "develop",
        "lead",
        "implement",
        "improve",
        "manage",
        "maintain",
        "deliver",
        "automate",
        "optimize",
        "mentor",
        "create",
        "support",
    ]
)
_ALIASES = {
    "javascript": ("javascript", "js"),
    "typescript": ("typescript", "ts"),
    "node.js": ("node.js", "nodejs", "node js"),
    "react": ("react", "react.js", "reactjs"),
    "postgresql": ("postgresql", "postgres"),
    "kubernetes": ("kubernetes", "k8s"),
    "aws": ("aws", "amazon web services"),
    "ci/cd": ("ci/cd", "ci / cd", "continuous integration and continuous delivery"),
    ".net": (".net", "dotnet", "dot net"),
    "c#": ("c#", "csharp", "c sharp"),
    "c++": ("c++", "cpp", "c plus plus"),
}
_CANONICAL = {alias: canonical for canonical, aliases in _ALIASES.items() for alias in aliases}
_HEADINGS = {
    "summary",
    "professional summary",
    "profile",
    "objective",
    "experience",
    "work experience",
    "professional experience",
    "employment",
    "employment history",
    "projects",
    "selected projects",
    "personal projects",
    "education",
    "skills",
    "technical skills",
    "core competencies",
    "certifications",
    "certificates",
    "achievements",
    "awards",
    "publications",
    "languages",
    "volunteer experience",
}


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).casefold()).strip()


def canonical_term(term: str) -> str:
    return _CANONICAL.get(normalized(term), normalized(term))


def contains_term(text: str, term: str) -> bool:
    """Whole terms, including punctuation-bearing skills like C++, C#, and .NET."""
    aliases = _ALIASES.get(canonical_term(term), (normalized(term),))
    haystack = normalized(text)
    return any(
        re.search(r"(?<![\w+#.])" + re.escape(alias) + r"(?![\w+#])", haystack) is not None
        for alias in aliases
        if alias
    )


def job_terms(fields: dict, keys: tuple[str, ...]) -> list[str]:
    terms: dict[str, str] = {}
    for key in keys:
        values = fields.get(key)
        if not isinstance(values, list):
            continue
        for value in values:
            if isinstance(value, str) and 0 < len(value.strip()) <= 100:
                terms.setdefault(canonical_term(value), value.strip())
    return list(terms.values())


def resume_text(content: ResumeContent) -> str:
    lines = [content.summary or ""]
    for section in content.sections:
        lines.append(f"\n## {section.name}")
        lines.extend(f"- {item}" for item in section.items)
    return "\n".join(lines).strip()


def fingerprint(content: ResumeContent, fields: dict) -> str:
    payload = json.dumps(
        {"content": content.model_dump(), "job": fields, "algorithm": SCORING_VERSION},
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _achievement_items(content: ResumeContent) -> list[str]:
    return [
        item.strip()
        for section in content.sections
        if any(
            part in normalized(section.name)
            for part in ("experience", "employment", "project", "achievement")
        )
        for item in section.items
        if item.strip()
    ]


def _action_led(item: str) -> bool:
    # Imported CVs often combine an employer/title/date and a bullet with an em dash.
    parts = re.split(r"\s+[–—-]\s+|:\s+", item)
    return any(
        (match := re.match(r"[\s\-*•]*([A-Za-z]+)", part)) and match.group(1).casefold() in _VERBS
        for part in parts
    )


def _quantified(item: str) -> bool:
    # Employment dates and software versions are not quantified achievements.
    text = re.sub(r"\b\d{1,2}[/.-](?:19|20)\d{2}\b", "", item)
    text = re.sub(r"\b(?:19|20)\d{2}\b", "", text)
    text = re.sub(
        r"\b(?:python|java|react|angular|node(?:\.js)?|version|v)\s*\d+(?:\.\d+)*",
        "",
        text,
        flags=re.I,
    )
    return re.search(r"(?<![\w.])\d+(?:[,.]\d+)*(?:[kKmMbB])?(?![\w.])", text) is not None


def evaluate_resume(
    content: ResumeContent,
    fields: dict,
    version_id: UUID,
    baseline_score: int | None = None,
) -> AtsReport:
    text = resume_text(content)
    # Count authored content, excluding headings and generated bullet markers.
    prose = "\n".join(
        [content.summary or ""] + [item for s in content.sections for item in s.items]
    )
    words = re.findall(r"\b[\w]+(?:['’/-][\w]+)*\b", prose)
    word_count = len(words)
    items = _achievement_items(content)
    keywords = job_terms(fields, ("keywords", "skills", "tech_stack"))
    skills = job_terms(fields, ("skills", "tech_stack"))
    # Headings do not count as evidence of a skill.
    matched = [term for term in keywords if contains_term(prose, term)]
    missing = [term for term in keywords if term not in matched]
    missing_skills = [term for term in skills if not contains_term(prose, term)]
    checks: list[AtsCheck] = []
    suggestions: list[AtsSuggestion] = []

    def check(category, label, score, weight, summary):
        checks.append(
            AtsCheck(category=category, label=label, score=score, weight=weight, summary=summary)
        )

    def suggest(category, priority, message):
        suggestions.append(AtsSuggestion(category=category, priority=priority, message=message))

    check(
        "keyword_match",
        "Keyword match",
        round(100 * len(matched) / len(keywords)) if keywords else None,
        25,
        f"{len(matched)} of {len(keywords)} unique job terms appear in the resume."
        if keywords
        else "No structured job keywords are available; "
        "parse a job with skills/keywords to evaluate this check.",
    )
    if missing:
        suggest(
            "keyword_match",
            "high",
            "Use relevant job terminology in evidence-based bullets: "
            + ", ".join(missing[:10])
            + ". Avoid keyword stuffing or adding claims you cannot support.",
        )
    action_count = sum(_action_led(item) for item in items)
    check(
        "action_verbs",
        "Action verbs",
        round(100 * action_count / len(items)) if items else None,
        15,
        f"{action_count} of {len(items)} experience/project bullets "
        "start with a strong action verb."
        if items
        else "No experience, project, or achievement bullets to evaluate.",
    )
    if items and action_count < len(items):
        suggest(
            "action_verbs",
            "medium",
            "Start experience/project bullets with clear action verbs such as Built, Designed, "
            "Led, or Improved, followed by the work and its result.",
        )
    length_score = (
        min(100, round(word_count / 300 * 100))
        if word_count <= 900
        else max(0, round(100 - (word_count - 900) / 6))
    )
    check(
        "length",
        "Length",
        length_score,
        10,
        f"{word_count} words; the content target is 300–900 words. "
        "Actual page count depends on the template.",
    )
    if word_count < 300:
        suggest(
            "length",
            "medium",
            "Add relevant, factual detail about your work, projects, and outcomes; "
            "aim for 300–900 words without padding.",
        )
    elif word_count > 900:
        suggest(
            "length",
            "medium",
            "Condense repeated or less relevant content toward 300–900 words "
            "while preserving the strongest evidence.",
        )
    headings = [normalized(section.name) for section in content.sections]
    duplicate_headings = len(headings) - len(set(headings))
    nonstandard = [
        section.name for section in content.sections if normalized(section.name) not in _HEADINGS
    ]
    empties = sum(
        not s.name.strip() or not any(i.strip() for i in s.items) for s in content.sections
    )
    empty_items = sum(not i.strip() for s in content.sections for i in s.items)
    markup = bool(re.search(r"<[^>]+>|\{\{.+?\}\}|[│┃┌┐└┘]|\|.+\|", text))
    formatting_score = max(
        0,
        100
        - min(40, duplicate_headings * 20)
        - min(30, len(nonstandard) * 10)
        - min(30, empties * 15)
        - min(20, empty_items * 5)
        - 20 * markup
        - (50 if not content.sections else 0),
    )
    check(
        "formatting",
        "Content formatting",
        formatting_score,
        10,
        "Checks standard headings, empty/duplicate sections, and embedded markup. "
        "PDF layout, columns, fonts, and reading order are not inspected.",
    )
    if formatting_score < 100:
        suggest(
            "formatting",
            "medium",
            "Use standard section headings (Experience, Skills, Education), remove empty/duplicate "
            "sections, and replace table-like markup with plain bullets.",
        )
    quantified_count = sum(_quantified(item) for item in items)
    # Half the substantive bullets quantified earns full credit; never encourage invented metrics.
    quantified_score = min(100, round(200 * quantified_count / len(items))) if items else None
    check(
        "quantified_achievements",
        "Quantified achievements",
        quantified_score,
        15,
        f"{quantified_count} of {len(items)} experience/project bullets contain numbers "
        "beyond employment years/software versions. Target: at least half."
        if items
        else "No experience, project, or achievement bullets to evaluate.",
    )
    if items and quantified_count / len(items) < 0.5:
        suggest(
            "quantified_achievements",
            "medium",
            "Where you have real evidence, quantify outcomes or scope (latency, users, delivery "
            "time, team size). Never invent numbers; leave qualitative results when metrics "
            "are unavailable.",
        )
    check(
        "missing_skills",
        "Job skills coverage",
        round(100 * (len(skills) - len(missing_skills)) / len(skills)) if skills else None,
        15,
        f"{len(missing_skills)} of {len(skills)} job skills/technologies are absent."
        if skills
        else "No structured job skills are available for comparison.",
    )
    if missing_skills:
        suggest(
            "missing_skills",
            "high",
            "Add specific evidence only for skills you actually have: "
            + ", ".join(missing_skills[:10])
            + ". Treat unsupported skills as gaps, not text to insert.",
        )
    readable = "\n".join(([content.summary] if content.summary else []) + items)
    sentences = [s for s in re.split(r"[.!?](?:\s|$)|\n", readable) if s.strip()]
    sentence_lengths = [len(re.findall(r"\b\w+\b", s)) for s in sentences]
    average = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
    long_bullets = sum(len(item.split()) > 40 for item in items)
    readability_score = (
        max(0, round(100 - max(0, average - 22) * 3 - min(30, long_bullets * 10)))
        if sentences
        else None
    )
    check(
        "readability",
        "Readability",
        readability_score,
        10,
        f"Average sentence length: {average:.1f} words; {long_bullets} bullets exceed 40 words. "
        "This is a length-based English heuristic, not a grammar assessment."
        if sentences
        else "No summary or experience/project prose to evaluate.",
    )
    if readability_score is not None and readability_score < 85:
        suggest(
            "readability",
            "low",
            "Split long sentences and bullets. Use direct language and aim for roughly "
            "15–25 words per sentence and fewer than 40 per bullet.",
        )
    applicable = [c for c in checks if c.score is not None]
    total_weight = sum(c.weight for c in applicable)
    overall = (
        round(sum(c.score * c.weight for c in applicable) / total_weight)
        if total_weight and word_count
        else 0
    )
    return AtsReport(
        resume_version_id=version_id,
        overall_score=overall,
        checks=checks,
        suggestions=sorted(
            suggestions, key=lambda s: {"high": 0, "medium": 1, "low": 2}[s.priority]
        ),
        matched_keywords=matched,
        missing_keywords=missing,
        missing_skills=missing_skills,
        word_count=word_count,
        scoring_version=SCORING_VERSION,
        fingerprint=fingerprint(content, fields),
        evaluated_at=datetime.now(UTC),
        baseline_score=baseline_score,
        score_delta=overall - baseline_score if baseline_score is not None else None,
        limitations=[
            "A reproducible content-quality estimate, not a score from an employer's ATS "
            "or a hiring prediction.",
            "Formatting checks inspect structured content only; export layout and PDF reading "
            "order require separate review.",
            "Unavailable checks are excluded and remaining weights are normalized; "
            "keyword repetition adds no credit.",
        ],
    )
