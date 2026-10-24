# Career Agent Platform

Hybrid AI platform for personalized job applications, built with FastAPI, Next.js, and open-source models. Upload storage, embeddings, ATS checks, and document rendering run locally. Parsing, analysis, resume tailoring, and ATS refinement use the configured LLM provider (Groq by default; Ollama for local inference). No telemetry or paid-service requirement.

## Quickstart

```bash
# 1. Get a free Groq API key: https://console.groq.com/keys
# 2. Set the key as an environment variable
$env:GROQ_API_KEY="gsk_your_key_here"   # PowerShell
# export GROQ_API_KEY=gsk_your_key_here  # Bash

# 3. Start all services (postgres, qdrant, redis, minio, ollama, backend, frontend, worker)
docker compose up -d --wait

# 4. Pull the embedding model (one-time, ~2GB)
docker exec career-agent-ollama ollama pull bge-m3

# 5. Backend: http://localhost:8000/api/v1/docs
#    Frontend: http://localhost:3000
```

For development with hot reload, use the dev script (starts backend + ARQ worker + frontend natively).
It installs `bge-m3` if missing; the first run downloads the embedding model:
```bash
# PowerShell
.\scripts\dev.ps1

# Bash
bash scripts/dev.sh
```

## Architecture

```
Next.js Dashboard  →  FastAPI Gateway  →  ARQ Worker (Redis)  →  Groq LLM (parse)
                         ↓                        ↓
              PostgreSQL (pgvector) · Qdrant · MinIO · Ollama (embeddings only)
```

All parsing is dispatched to a Redis-backed ARQ worker process, decoupled from the HTTP server. Parsing uses **Groq's gpt-oss-120b** (free tier, reasoning configured `low`/`parsed`). Embeddings use local **Ollama bge-m3**. See [ADR 0004](docs/adr/0004-cloud-llm-for-parsing.md) for the cloud LLM decision.

## Structure

| Path | Purpose |
|------|---------|
| `frontend/` | Next.js 16 web UI |
| `backend/` | FastAPI app, agents, parsers, LLM provider abstraction |
| `workers/` | Background job runners (ARQ) |
| `shared/` | Shared contracts between frontend/backend |
| `infrastructure/` | Dockerfiles, service configs |
| `scripts/` | Setup and dev helpers |
| `prompts/` | Versioned prompt templates (cv, interview, analysis) |
| `models/` | LLM/embedding configs and Ollama manifests |
| `docs/` | Architecture, ADRs, roadmap, data models, research |

## Development

```bash
# backend
cd backend
pip install -e ".[dev]"
alembic upgrade head
uvicorn main:app --reload

# ARQ worker (run in a separate terminal for background job processing)
cd backend
arq workers.arq_worker.WorkerSettings

# frontend
cd frontend
npm install
npm run dev

# tests
cd backend && pytest
```

Start the infrastructure services before running the backend natively:
`docker compose up -d --wait postgres qdrant redis minio ollama`.
Run `alembic upgrade head` from `backend/` on first setup and after pulling new
migrations. The backend requires these tables before application startup.

Native backend and worker processes read the root `.env` and then `backend/.env`
(backend values override root values). Both `GROQ_API_KEY` and `APP_GROQ_API_KEY`
are accepted. Keep the ARQ worker running alongside Uvicorn; parsing requests are
queued in Redis and cannot complete without it.

For HTML resume templates on native Windows, WeasyPrint also needs Pango and its
native libraries. Install [MSYS2](https://www.msys2.org/) at `C:\msys64`, then run
`pacman -S mingw-w64-ucrt-x86_64-pango` in its UCRT64 shell. Restart both the
backend and worker afterward. See the [WeasyPrint Windows setup guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows).
The Modern Typst template does not require these native libraries.
If Windows Application Control blocks the installed DLLs (`WinError 4551`),
choose Modern Typst or run rendering with the Docker worker, whose Linux image
includes the required libraries. Installing Pango again will not resolve a
Windows policy block.

## LLM Provider

The platform abstracts LLM calls behind a provider plug (`backend/parsers/llm_provider.py`). Set `APP_LLM_PROVIDER` to control which backend is used:

| Provider | Default for | Model | Requires |
|---|---|---|---|
| `groq` | Job parsing, analysis, resume tailoring | `openai/gpt-oss-120b` | `APP_GROQ_API_KEY` |
| `ollama` | Embeddings, future agents | `qwen3:8b` / `bge-m3` | Docker ollama container |
| `gemini` | (stub — not yet implemented) | — | `APP_GEMINI_API_KEY` |

Switch at any time by changing `APP_LLM_PROVIDER` in your `.env` or Docker environment.

## Status

Phase 7 — ATS Optimizer **complete**. Open a job, view a built resume version, and
use **ATS Optimizer → Run ATS check** for seven local checks and prioritized
suggestions. Edit and recheck, or **Refine into new version** to preserve the
source and compare before/after scores. The score estimates content quality;
exported PDF layout and employer-specific ATS behavior are outside its scope.
See [ADR 0008](docs/adr/0008-ats-optimizer.md) and the [roadmap](docs/roadmap/phases.md).

## License

MIT
