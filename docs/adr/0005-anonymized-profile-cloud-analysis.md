# ADR 0005: Anonymized Profile via Cloud LLM for Job-Fit Analysis

- **Status:** Accepted
- **Date:** 2026-07-26

## Context

Phase 4 (Job Analysis Agent) needs to analyze how well a candidate profile fits a job posting. This requires the LLM to see both:

1. The parsed job posting text (public data — already sent to Groq per ADR 0004)
2. The candidate's profile: skills, experience, education, projects, and relevant CV sections (personal data)

Per ADR 0004, personal data should remain local via Ollama. However, local `qwen3:8b` inference is 30-60s+ on the 4 GB VRAM laptop, causing timeouts and WSL2 instability for multi-step agent workflows.

## Decision

When running job analysis, the candidate's profile is **anonymized** before being sent to Groq:

1. A `build_digest(profile)` function in `backend/agents/profile_digest.py` constructs a plain-text summary containing only:
   - Title, summary (career objective), location (city-level)
   - Skills (name, category, proficiency level, years)
   - Experience (company name, title, employment type, bullet points)
   - Projects (name, tech stack, description, highlights)
   - Education (degree, field of study, institution — **no GPA**)
   - Certificates (name, issuer), Languages, Achievements

2. The following PII fields are **explicitly excluded** and never appear in the digest:
   - `full_name`, `email`, `phone`, `github_url`, `linkedin_url`, `website`
   - `GPA` (stripped from education records)

3. The anonymized digest + retrieved CV chunks are sent to Groq alongside the public job posting text.

4. The full local Ollama path remains available by setting `APP_LLM_PROVIDER=ollama` (existing toggle). When Ollama is the provider, the digest is still computed (no code divergence), but all data stays local.

## Privacy posture

| What's sent to Groq | Risk level | Mitigation |
|---|---|---|
| Job posting text | None — public data | Already established (ADR 0004) |
| Skill names + proficiency + years | Low — generic tags | No individual identification possible |
| Company names + job titles | Low — public professional history | Combined with skill tags makes reidentification theoretically possible but practically infeasible without names/emails |
| CV chunks from Qdrant | Low — evidence snippets | Gated by profile_id; only includes uploaded document chunks |
| Contact info (email, phone, URLs) | **Never sent** | Stripped by `build_digest()` with a unit test asserting absence |
| Full name, GPA, address | **Never sent** | Stripped |

## Alternatives considered

| Alternative | Why rejected |
|---|---|
| **Local Ollama for all analysis** | 30-60s+ inference time on target hardware; multi-step LangGraph agent would compound delays. Left as fallback via env var. |
| **Split: Ollama for profile digest, Groq for analysis** | Two LLM calls instead of one; digest-building is deterministic Python string assembly (no LLM needed). |
| **Full local Qwen3 with quantization swap** | Phi-4-mini (MIT) may work on 4 GB but quality drop on structured analysis tasks is unknown. Evaluated as future option. |

## Consequences

**Positive:**
- Analysis completes in <5 seconds (same as job parsing), avoiding the 30-60s+ local inference bottleneck.
- LangGraph agent (5-node pipeline with vector retrieval) runs entirely on the fast path without risk of timeout.
- No new API key or service — reuses the existing Groq free tier (30 RPM, 14k req/day).
- Digest construction is deterministic Python string assembly — zero LLM cost for anonymization.
- Unit test (`test_profile_digest_strips_pii`) ensures no PII regressions on digest refactoring.

**Negative:**
- Anonymized profile data is still sent to a cloud provider. While the data is professional (skills, companies, titles) and stripped of identifiers, the privacy boundary is less absolute than keeping everything local.
- A determined actor could theoretically correlate company + title + years to identify an individual, though this would require access to Groq's internal data and additional context.

## Revisit when

- Local LLM hardware improves (e.g. GPU upgrade to ≥12 GB VRAM makes `qwen3:8b` viable).
- A local model with strong structured-output reasoning ships at <4B parameters.
- For a multi-user or enterprise deployment, the privacy risk calculus may change, warranting a local-only default.
