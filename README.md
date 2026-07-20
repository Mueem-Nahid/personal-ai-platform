# Career Agent Platform

Offline, local-first AI platform for personalized job applications. Built with FastAPI, Next.js, and open-source models running entirely on your machine via Docker.

## Quickstart

```bash
# start all services (postgres, qdrant, redis, minio, ollama, backend, frontend)
docker compose up -d

# pull the default LLM (one-time, ~5GB)
docker exec career-agent-ollama ollama pull qwen3:8b

# backend: http://localhost:8000/api/v1/docs
# frontend: http://localhost:3000
```

## Architecture

```
Next.js Dashboard  →  FastAPI Gateway  →  Agents / Services
                                              ↓
                            PostgreSQL (pgvector) · Qdrant · Redis · MinIO · Ollama
```

## Structure

| Path | Purpose |
|------|---------|
| `frontend/` | Next.js 16 web UI |
| `backend/` | FastAPI app, agents, parsers, templates |
| `workers/` | Background job runners (Celery/ARQ) |
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

# frontend
cd frontend
npm install
npm run dev

# tests
cd backend && pytest
```

## Status

Phase 3 — Job Parser in progress. See `docs/roadmap/phases.md` for the 16-phase plan.

## License

MIT
