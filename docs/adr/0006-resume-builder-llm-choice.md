# ADR 0006 — Resume Builder LLM Choice

## Status

Accepted

## Context

Phase 5 (Resume Builder) tailors a user's master resume (uploaded via the Knowledge Base in Phase 2) to match a target job posting. This involves sending substantial portions of the user's resume—including work history, skills, and project details—to the LLM provider to rewrite and reorder bullet points.

The platform's cross-cutting privacy rule (established in `docs/roadmap/phases.md`) states that "Resumes, CVs, cover letters, and personal documents use local Ollama by default." This ensures personal career data never leaves the local machine.

However, the Groq free-tier offers significantly faster inference (~500 tok/s vs. local Ollama) and the user has explicitly chosen Groq as the default provider for resume tailoring.

## Decision

**The Resume Builder will use whatever LLM provider is configured via `APP_LLM_PROVIDER`** (default: `groq`), consistent with the rest of the platform. The user is responsible for the privacy tradeoff—switching to `ollama` in `.env` keeps all personal data local.

The resume builder agent (`backend/agents/resume_builder_agent.py`) calls `parsers.llm_provider.complete()` which honors `APP_LLM_PROVIDER`. No hardcoded override.

## Consequences

- **Privacy**: If the user keeps `APP_LLM_PROVIDER=groq`, personal resume content is sent to Groq's cloud API (free tier). This contradicts the platform's "local-first for personal docs" stance. The README and documentation should make this tradeoff explicit.
- **Speed**: Groq is significantly faster (2-5s per build vs. 30-120s on local Ollama for a multi-section resume JSON).
- **Cost**: Groq free tier is free for solo use. No paid API keys needed.
- **Flexibility**: Switching to `ollama` with `qwen3:8b` keeps everything local but may produce lower-quality JSON output.
- **Auditability**: All prompts, evidence, and raw responses are stored per version (`resume_versions.prompt_text`, `evidence_text`, `raw_response`) for full traceability regardless of provider.

## Alternatives Considered

1. **Hardcode Ollama for resume builder regardless of `APP_LLM_PROVIDER`** — Rejected. Inconsistent with the rest of the platform; the user already toggles `APP_LLM_PROVIDER` for analysis (Phase 4) which also handles profile data. Retaining a single toggle is simpler and the user already understands the tradeoff.
2. **Add a separate `APP_RESUME_LLM_PROVIDER` setting** — Rejected. Unnecessary complexity. The existing provider toggle is sufficient; resume tailoring is conceptually similar to job analysis (LLM + personal data → structured output).

## Future

- Phase 6 (PDF Engine) will render the structured `content_json` into formatted PDFs. The rendering engine is completely local (Jinja2 + WeasyPrint) regardless of which LLM generated the content.
- Phase 14 (Memory) may introduce provider-specific optimizations for resume styles learned across builds.
