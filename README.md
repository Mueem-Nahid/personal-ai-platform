# Career Agent Platform

Privacy-respectful hybrid AI platform for personalized job applications. Built with FastAPI, Next.js, and open-source models. Embeddings and sensitive documents run locally; job-post parsing uses a free cloud LLM (Groq) for speed. No telemetry, no paid services.

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

For development with hot reload, use the dev script (starts backend + ARQ worker + frontend natively):
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

All parsing is dispatched to a Redis-backed ARQ worker process, decoupled from the HTTP server. Parsing uses **Groq's Llama 3.1 8B** (free tier, ~500 tok/s). Embeddings use local **Ollama bge-m3**. See [ADR 0004](docs/adr/0004-cloud-llm-for-parsing.md) for the cloud LLM decision.

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

## LLM Provider

The platform abstracts LLM calls behind a provider plug (`backend/parsers/llm_provider.py`). Set `APP_LLM_PROVIDER` to control which backend is used:

| Provider | Default for | Model | Requires |
|---|---|---|---|
| `groq` | Job parsing | `llama-3.1-8b-instant` | `APP_GROQ_API_KEY` |
| `ollama` | Embeddings, future agents | `qwen3:8b` / `bge-m3` | Docker ollama container |
| `gemini` | (stub — not yet implemented) | — | `APP_GEMINI_API_KEY` |

Switch at any time by changing `APP_LLM_PROVIDER` in your `.env` or Docker environment.

## Status

Phase 5 — Resume Builder **complete**. Tailor resumes to specific jobs with versioning (v1, v2, v3). Vector retrieval of matching CV sections via Qdrant. LangGraph agent rewrites/reorders bullet points. See `docs/roadmap/phases.md` for the 16-phase plan.

## License

MIT
