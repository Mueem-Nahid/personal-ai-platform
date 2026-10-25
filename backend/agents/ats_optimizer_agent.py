from __future__ import annotations

import json
import re

from core.config import settings
from schemas.resume import ResumeContent
from services.ats_scoring import contains_term, job_terms, resume_text
from utils.prompt_loader import load_prompt


def build_optimization_prompt(context: dict) -> str:
    template, _ = load_prompt(settings.prompts_path / "cv" / "optimize.md")
    payload = {
        "resume": context["source_content"],
        "job": context["job_fields"],
        "suggestions": context["report"]["suggestions"],
        "master_resume_evidence": context["reference_text"],
    }
    return template.replace("{{ optimization_input }}", json.dumps(payload, ensure_ascii=False))


def validate_refinement(content: ResumeContent, context: dict) -> None:
    if not content.sections or not any(item.strip() for s in content.sections for item in s.items):
        raise ValueError(
            "The optimizer returned an empty resume. The original version is unchanged."
        )
    source = ResumeContent(**context["source_content"])
    evidence = resume_text(source) + "\n" + context["reference_text"]
    output = resume_text(content)

    # Reject new numeric claims rather than trusting an instruction not to invent metrics.
    def numbers(text: str) -> set[str]:
        return {n.replace(",", "") for n in re.findall(r"\d+(?:[.,]\d+)*", text)}

    if numbers(output) - numbers(evidence):
        raise ValueError(
            "Optimization introduced unsupported numbers. Retry or edit the resume manually; "
            "no source content was changed."
        )
    for skill in job_terms(context["job_fields"], ("skills", "tech_stack")):
        if contains_term(output, skill) and not contains_term(evidence, skill):
            raise ValueError(
                f"Optimization introduced an unsupported skill ({skill}). "
                "Add genuine evidence to the master CV or edit manually."
            )
