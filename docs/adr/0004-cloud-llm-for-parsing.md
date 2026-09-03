# ADR 0004: Cloud LLM for Job-Post Parsing (Groq)

- **Status:** Accepted (amended 2026-08-18 — model migrated, see below)
- **Date:** 2026-07-26
- **Supersedes:** ADR 0003 *for the job-post parsing use case* (0003 remains active for embeddings and heavier agent tasks later).

> **Amendment (2026-08-18):** Groq decommissioned `llama-3.1-8b-instant` on 2026-08-16 —
> the provider risk called out below materialized after ~3 weeks. The platform migrated to
> **`openai/gpt-oss-120b`** (Groq's recommended replacement; `openai/gpt-oss-20b` also verified
> available). Because this is a reasoning model, `llm_provider.py` now sends
> `reasoning_effort: "low"` + `reasoning_format: "parsed"` for gpt-oss models (keeps reasoning
> tokens out of `content` and the token budget), and defensively strips Harmony-channel /
> `<think>` leakage before JSON repair. Token budgets were raised (`llm_max_tokens` 1024→2048,
> `analysis_max_tokens` 1024→2048, `resume_max_tokens` 1500→3072) since reasoning tokens count
> toward completion on Groq. Verified live: clean JSON, ~1 s probe latency. Migration was a
> one-env-var change plus the reasoning-model handling — as this ADR predicted.

## Context

1. The platform's default local LLM, `qwen3:8b` (Q4_K_M, ~5 GB), requires ≥8 GB VRAM. The developer's laptop has an RTX 3050 Ti Mobile with **4 GB VRAM** — the model cannot fit entirely in GPU memory.

2. With CPU fallback, `qwen3:8b` inference for a ~1 KB job posting took **60+ seconds**, frequently exceeding the backend's 300 s timeout and the frontend's 6-minute poll window. Parsing routinely failed with "Parsing timed out."

3. The Docker Ollama container, starved for VRAM, consumed 5–8 GB of system RAM instead, triggering **WSL2 OOM kills** on the developer's Windows machine and crashing the entire Docker stack.

4. The job-post text submitted for parsing is **public data** (copied from a public job board). This distinguishes it from personal documents (resumes, CVs, cover letters) which will remain local-only in later phases.

5. Multiple cloud LLM providers offer **free tiers** with generous rate limits suitable for a solo-developer project.

## Decision

Use **Groq's Llama-3.1-8B-Instant** via the `openai/v1/chat/completions` API as the **default provider for job-post parsing**.

The general LLM invocation path is abstracted behind a provider plug (`backend/parsers/llm_provider.py`) dispatched by the `APP_LLM_PROVIDER` environment variable:

| Provider | Model | Uses | Privacy posture |
|---|---|---|---|
| `groq` (default) | `openai/gpt-oss-120b` *(was `llama-3.1-8b-instant`, decommissioned 2026-08-16)* | Job-post parsing, analysis, resume tailoring | Public job text; anonymized profile (ADR 0005) |
| `ollama` (fallback) | `qwen3:8b` | Embeddings (`bge-m3`), future resume/CV agents | Personal data |
| `gemini` (stub) | — | Unimplemented, reserved | — |

All configuration is in `backend/core/config.py`:

```python
llm_provider: str = "groq"
llm_model: str = "openai/gpt-oss-120b"
groq_api_key: str | None = None
```

### Why Groq
| Criterion | Groq | Google Gemini Flash | Cerebras | Local qwen3:8b |
|---|---|---|---|---|
| Free tier | 30 RPM / 14k req/day | 15 RPM / 1500 req/day, 1M TPM | Free, rate-limited | Free |
| Speed | **~500 tok/s** | Fast | ~400 tok/s | 2–10 tok/s (CPU) |
| Structured output | `response_format={"type":"json_object"}` | Native JSON schema | JSON mode | `format="json"` via Ollama |
| API compat | OpenAI-compatible (zero SDK dep) | `google-generativeai` SDK needed | OpenAI-compatible | Ollama Python client |
| Privacy | Data sent to Groq | Data sent to Google | Data sent to Cerebras | 100% local |
| Latency variability | Low | Low | Low | High (CPU-bound) |

Groq's free tier (30 requests/minute, 14,000 requests/day) is more than sufficient for a single-user job-parsing tool. Its OpenAI-compatible API requires **zero extra dependencies** — the client is a single `httpx.AsyncClient.post` call. A parse takes **1–3 seconds** end-to-end.

### ARQ Redis worker
Job parsing is dispatched to a separate **ARQ worker** process (`backend/workers/arq_worker.py`), decoupled from the FastAPI event loop. This:

- Survives uvicorn `--reload` restarts.
- Provides automatic retries (`max_tries=3`) for transient Groq API failures.
- Prevents LLM call latency from blocking the HTTP server.
- Enables the startup sweeper (`backend/main.py:_sweep_stale_parsing_jobs`) to recover stranded rows after a crash.

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| **Keep qwen3:8b local with GPU tuning** | 4 GB VRAM cannot fit the model; partial offload still slow and WSL2-unstable on this hardware. |
| **Swap to qwen3:4b** | Would fit GPU, but quality drop on extraction tasks was noticeable. Deferred to a later evaluation. |
| **Google Gemini 1.5 Flash** | Excellent free tier; requires `google-generativeai` SDK — heavier dep footprint. Stub added for future. |
| **Cerebras** | Fast, OpenAI-compatible, but less mature. |
| **OpenRouter (Llama 3.3 70B)** | Free models available but unpredictable rate-limiting. |
| **Skip provider abstraction** | Direct Groq integration would be simpler, but the `APP_LLM_PROVIDER` toggle keeps Ollama as a one-env-var fallback, and makes future provider swaps trivial. |

## Consequences

**Positive:**
- Parsing completes in **<5 seconds** (down from 60 s+ / timeouts).
- Docker stack no longer crashes on parse requests (Ollama only serves `bge-m3` embeddings, <3 GB RAM).
- Free tier (14,000 req/day) is far beyond solo-dev usage.
- No new Python dependencies needed — Groq uses the existing `httpx` already in `pyproject.toml`.
- Provider abstraction (`llm_provider.py`) makes adding Gemini or swapping providers a one-file change.
- ARQ worker durability protects against `--reload` restarts and provides automatic retries.

**Negative:**
- **Network dependency** — parsing requires internet access. If offline, fall back by setting `APP_LLM_PROVIDER=ollama` (expect slower parsing on the 4 GB GPU).
- **Privacy boundary** — job-post text is transmitted to Groq. This is acceptable because job listings are public data; resumes and CVs (Phases 5–9) will still default to local Ollama.
- **Provider risk** — Groq could change its free tier or deprecate the `llama-3.1-8b-instant` model. The `APP_LLM_MODEL` env var makes this a one-line fix.

## Revisit When

- GPU upgraded to a device with ≥12 GB VRAM (makes local `qwen3:8b` viable again).
- Groq free-tier limits become constraining (e.g., team use).
- A new cloud provider with a better free tier emerges.
- Local model landscape shifts (e.g., a 4B model matching qwen3:8b extraction quality ships).
