# ADR 0008 — Reproducible ATS checks and versioned refinement

Status: Accepted

## Decision

ATS checks run locally in `backend/services/ats_scoring.py`, without an LLM,
embedding service, or network request. The score is a content-quality heuristic,
not an employer's proprietary ATS score or a hiring prediction.

| Check | Weight | Rule |
|---|---:|---|
| Keyword match | 25 | Unique job keywords, skills, and technologies present in authored content |
| Action verbs | 15 | Experience/project/achievement bullets led by an action verb |
| Length | 10 | Full credit at 300–900 words; declines outside this range |
| Formatting | 10 | Standard headings; no empty/duplicate sections or table-like markup |
| Quantified achievements | 15 | Full credit when at least half of substantive bullets include numbers |
| Missing skills | 15 | Coverage of the job's structured skills and technology list |
| Readability | 10 | Sentence/bullet length; full credit below the long-sentence thresholds |

Matching respects term boundaries and common aliases, including punctuation in
C++, C#, and .NET. Repetition does not raise keyword credit. Employment years,
month/year dates, and common software-version numbers are excluded from metric
counts. These are heuristics, not semantic verification of each accomplishment.
Missing inputs produce N/A checks; the remaining weights are normalized. Empty
content always scores zero. Readability uses English length heuristics, not a
grammar model. Formatting checks do not inspect PDF columns, fonts, page count,
or exported reading order.

## Persistence and freshness

Migration `0008` adds four nullable fields to `resume_versions`: `ats_report`,
`parent_version_id`, `ats_baseline_score`, and `optimization_context`.
The report stores all seven checks, suggestions, matched/missing terms, word
count, evaluation time, and scoring version. Its SHA-256 fingerprint includes
the content, job fields, and algorithm version. Editing either input makes an
existing report stale. Rechecking replaces that version's cached report.

The existing job-fit analysis score remains separate: it measures profile fit;
this feature evaluates the selected resume's actual content.

## Refinement loop

1. View a completed resume version and run its ATS check.
2. Edit manually and recheck, or request AI refinement using the report fingerprint.
3. Reject stale refinement requests with HTTP 409 before creating a new version.
4. Snapshot the current resume, job fields, report, and bounded master-CV evidence.
5. Allocate a new resume version; preserve the source and its score as a baseline.
6. Dispatch `optimize_resume` through ARQ using the configured LLM provider.
7. Validate the returned content and reject newly introduced numeric values or
   job skills absent from the captured evidence. Other factual claims still need
   user review. Unmeasured outcomes remain qualitative rather than fabricated.
8. Score the new content locally and display the delta, including decreases.
9. Repeat until the resume is satisfactory; never promise a score increase.

Version numbers are allocated under a profile-row lock shared by normal builds
and refinements. The source self-reference uses `ON DELETE SET NULL`; the
snapshot and baseline remain interpretable if the source version is deleted.
Prompts, evidence, and raw responses use the existing per-version audit endpoint.
Failures mark the child version failed and preserve the original. The existing
stale-build sweeper also covers interrupted refinements.

Scoring stays local. AI refinement uses `APP_LLM_PROVIDER`, so the default Groq
path sends the captured resume/evidence to that provider, like normal tailoring.
Set the provider to Ollama to keep refinement inference local.

## Validation

Unit tests cover term boundaries, aliases, repetition, all seven checks,
unavailable inputs, stale fingerprints, and factual guardrails. Opt-in local
database tests cover the API/worker loop with a mocked LLM, concurrent version
numbering, queue failures, source preservation, and edit/recheck behavior:

```powershell
cd backend
$env:RUN_ATS_DB_TESTS = "1"
python -m pytest tests/test_ats.py tests/test_ats_integration.py
```
