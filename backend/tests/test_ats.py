from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from agents.ats_optimizer_agent import validate_refinement
from schemas.resume import ResumeContent, ResumeSection
from services.ats_scoring import contains_term, evaluate_resume, fingerprint, job_terms
from services.ats_service import AtsService, StaleAtsReportError


def content(bullets=None, summary="Python backend engineer") -> ResumeContent:
    return ResumeContent(
        summary=summary,
        sections=[
            ResumeSection(
                name="Experience", items=bullets or ["Built Python APIs and reduced latency by 40%"]
            ),
            ResumeSection(name="Skills", items=["Python, PostgreSQL"]),
        ],
    )


def score(resume=None, fields=None):
    return evaluate_resume(
        resume or content(),
        fields
        if fields is not None
        else {
            "skills": ["Python", "Go"],
            "keywords": ["APIs"],
            "tech_stack": ["PostgreSQL"],
        },
        uuid4(),
    )


def dimension(report, category):
    return next(check for check in report.checks if check.category == category)


@pytest.mark.parametrize(
    ("text", "term", "expected"),
    [
        ("Django developer", "Go", False),
        ("Built Go services", "Go", True),
        ("C++ and C# engineer", "C", False),
        ("C++ and C# engineer", "C++", True),
        ("C++ and C# engineer", "C#", True),
        (".NET services", ".NET", True),
        ("internet services", ".NET", False),
        ("Postgres and k8s", "PostgreSQL", True),
        ("Postgres and k8s", "Kubernetes", True),
        ("React.js apps", "React", True),
        ("JavaScript", "Java", False),
    ],
)
def test_term_boundaries_and_aliases(text, term, expected):
    assert contains_term(text, term) is expected


def test_all_seven_dimensions_and_weighted_total():
    report = score()
    assert len(report.checks) == 7
    assert sum(c.weight for c in report.checks) == 100
    assert report.overall_score == round(sum(c.score * c.weight for c in report.checks) / 100)
    assert report.missing_skills == ["Go"]
    assert dimension(report, "action_verbs").score == 100
    assert dimension(report, "quantified_achievements").score == 100


def test_empty_resume_scores_zero():
    assert score(ResumeContent()).overall_score == 0


def test_aliases_are_not_counted_as_separate_requirements():
    assert job_terms({"skills": ["Postgres", "PostgreSQL", "PYTHON", "python"]}, ("skills",)) == [
        "Postgres",
        "PYTHON",
    ]


def test_repeated_keywords_do_not_inflate_keyword_score():
    original = score()
    repeated = score(content(summary="Python " * 100))
    assert dimension(original, "keyword_match").score == dimension(repeated, "keyword_match").score


def test_unavailable_job_terms_do_not_receive_full_credit():
    report = score(fields={})
    assert dimension(report, "keyword_match").score is None
    assert dimension(report, "missing_skills").score is None
    assert "No structured" in dimension(report, "keyword_match").summary


def test_employment_dates_and_software_versions_are_not_metrics():
    report = score(content(["Developed Python 3 applications (2021–2024)"]))
    assert dimension(report, "quantified_achievements").score == 0


def test_abbreviated_metrics_count_but_month_year_dates_do_not():
    assert (
        dimension(
            score(content(["Built services handling 100K requests"])), "quantified_achievements"
        ).score
        == 100
    )
    assert (
        dimension(
            score(content(["Built services (01/2020–12/2023)"])), "quantified_achievements"
        ).score
        == 0
    )


def test_education_numbers_are_not_achievement_metrics():
    resume = content(["Built APIs"])
    resume.sections.append(ResumeSection(name="Education", items=["BSc 2020, GPA 3.9"]))
    assert dimension(score(resume), "quantified_achievements").score == 0


def test_action_verb_after_employer_header_counts():
    report = score(content(["Acme – Engineer (2020–2023) – Built Python APIs"]))
    assert dimension(report, "action_verbs").score == 100


def test_action_verb_after_plain_text_employer_header_counts():
    report = score(content(["Acme - Engineer (2020-2023) - Built Python APIs"]))
    assert dimension(report, "action_verbs").score == 100


def test_duplicate_and_empty_sections_reduce_formatting_score():
    resume = content()
    resume.sections.extend(
        [ResumeSection(name="Skills", items=[]), ResumeSection(name="", items=[""])]
    )
    report = score(resume)
    assert dimension(report, "formatting").score < 100
    assert any(s.category == "formatting" for s in report.suggestions)


def test_long_sentences_reduce_readability_score():
    short = score(content(["Built Python services."]))
    long = score(content(["Built " + "complex " * 70 + "services."]))
    assert dimension(long, "readability").score < dimension(short, "readability").score


def test_long_resume_loses_length_credit():
    report = score(content(summary="experience " * 1600))
    assert dimension(report, "length").score == 0


def test_fingerprint_tracks_content_job_and_is_order_independent():
    resume = content()
    assert fingerprint(resume, {"skills": ["Python"], "keywords": []}) == fingerprint(
        resume, {"keywords": [], "skills": ["Python"]}
    )
    assert fingerprint(resume, {}) != fingerprint(resume, {"skills": ["Python"]})
    assert fingerprint(resume, {}) != fingerprint(content(summary="Changed"), {})


def context():
    return {
        "source_content": content().model_dump(),
        "job_fields": {"skills": ["Python", "Go"]},
        "reference_text": "Built Python APIs and reduced latency by 40%",
        "report": score().model_dump(mode="json"),
    }


def test_refinement_accepts_supported_facts():
    validate_refinement(content(["Reduced Python API latency by 40%"]), context())


def test_refinement_rejects_invented_metrics():
    with pytest.raises(ValueError, match="unsupported numbers"):
        validate_refinement(content(["Reduced Python API latency by 75%"]), context())


def test_refinement_rejects_unsupported_skills():
    with pytest.raises(ValueError, match="unsupported skill"):
        validate_refinement(content(["Built Python and Go APIs"]), context())


def test_refinement_can_use_genuine_master_cv_evidence():
    snapshot = context()
    snapshot["reference_text"] += " Built Go services handling 200 requests."
    validate_refinement(content(["Built Go services handling 200 requests"]), snapshot)


def test_refinement_rejects_empty_output():
    with pytest.raises(ValueError, match="empty resume"):
        validate_refinement(ResumeContent(), context())


@pytest.mark.asyncio
async def test_saved_report_becomes_stale_after_edit():
    report = score(fields={})
    version = SimpleNamespace(
        status="built",
        content_json=content(summary="Edited").model_dump(),
        job_id=uuid4(),
        ats_report=report.model_dump(mode="json"),
    )
    session = SimpleNamespace(get=AsyncMock(return_value=SimpleNamespace(parsed_fields={})))
    service = AtsService(session)
    service._repo.get = AsyncMock(return_value=version)
    result = await service.get_report(uuid4())
    assert result.is_stale is True


@pytest.mark.asyncio
async def test_refinement_rejects_stale_report_before_creating_version():
    report = score(fields={})
    version = SimpleNamespace(
        status="built",
        content_json=content(summary="Edited").model_dump(),
        job_id=uuid4(),
        ats_report=report.model_dump(mode="json"),
    )
    session = SimpleNamespace(
        get=AsyncMock(return_value=SimpleNamespace(parsed_fields={})), execute=AsyncMock()
    )
    service = AtsService(session)
    service._repo.get = AsyncMock(return_value=version)
    service._repo.create = AsyncMock()
    with pytest.raises(StaleAtsReportError):
        await service.create_refinement(uuid4(), report.fingerprint)
    service._repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_worker_refinement_saves_new_score_and_baseline(monkeypatch):
    snapshot = context()
    version = SimpleNamespace(
        id=uuid4(), status="building", optimization_context=snapshot, ats_baseline_score=50
    )
    session = SimpleNamespace(commit=AsyncMock())
    service = AtsService(session)
    service._repo.get = AsyncMock(return_value=version)
    service._repo.update = AsyncMock()
    monkeypatch.setattr(
        "parsers.llm_provider.complete", AsyncMock(return_value=content().model_dump_json())
    )
    await service.run_refinement(version.id)
    assert version.status == "built"
    assert version.ats_report["baseline_score"] == 50
    assert version.ats_report["score_delta"] == version.ats_report["overall_score"] - 50
    assert snapshot["source_content"] == content().model_dump()


@pytest.mark.asyncio
async def test_failed_refinement_does_not_save_unsupported_content(monkeypatch):
    version = SimpleNamespace(
        id=uuid4(),
        status="building",
        optimization_context=context(),
        ats_baseline_score=50,
        content_json=None,
    )
    service = AtsService(SimpleNamespace(commit=AsyncMock()))
    service._repo.get = AsyncMock(return_value=version)
    service._repo.update = AsyncMock()
    monkeypatch.setattr(
        "parsers.llm_provider.complete",
        AsyncMock(return_value=content(["Improved performance by 99%"]).model_dump_json()),
    )
    await service.run_refinement(version.id)
    assert version.status == "failed"
    assert "unsupported numbers" in version.error
    assert version.content_json is None
