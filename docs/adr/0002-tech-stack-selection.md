# ADR 0002: Tech Stack Selection

- **Status:** Accepted
- **Date:** 2026-07-13

## Context

The platform must run entirely offline on a user's machine using only permissively licensed open-source components. The owner has production experience with FastAPI, Docker, PostgreSQL, Redis, and LangChain, so the stack should leverage that expertise while introducing multi-agent orchestration and persistent memory.

## Decision

| Layer | Choice | License |
|-------|--------|---------|
| Frontend | Next.js 16, TypeScript, Tailwind, shadcn/ui, TanStack Query | MIT |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic | MIT |
| Agent framework | LangGraph | MIT |
| LLM runtime | Groq Cloud (parsing), Ollama (embeddings + fallback) | Free tier / MIT |
| LLM (parsing) | Llama 3.1 8B (via Groq) | Apache 2.0 |
| LLM (embeddings / fallback) | Qwen3 8B (via Ollama) | Apache 2.0 |
| Embeddings | BAAI bge-m3 | MIT |
| Vector DB | Qdrant | Apache 2.0 |
| Relational DB | PostgreSQL 16 + pgvector | PostgreSQL License |
| Cache / queue | Redis 7 | RSALv2/SSPL (acceptable for self-host) |
| Object storage | MinIO | AGPLv3 (acceptable for self-host) |
| PDF generation | Jinja2 + WeasyPrint | BSD |
| Job scraping | Playwright + BeautifulSoup | Apache 2.0 / MIT |
| Observability | OpenTelemetry + Prometheus + Grafana | Apache 2.0 |
| Deployment | Docker Compose (local), K8s-ready later | — |

## Alternatives Considered

- **Vector DB:** Weaviate (BSD) and pgvector-only were considered. Qdrant won on performance and Docker simplicity; pgvector kept for inline vectors and smaller collections.
- **LLM (parsing):** Local `qwen3:8b` could not fit in the developer's 4 GB VRAM, causing timeouts and Docker crashes. Cloud alternatives (Gemini Flash, Cerebras, OpenRouter, local `qwen3:4b`) were compared — see [ADR 0004](./0004-cloud-llm-for-parsing.md). Groq's Llama-3.1-8B Instant was chosen for speed, OpenAI-compatible API (zero new deps), and generous free tier.
- **LLM (embeddings / future agents):** Qwen3 8B retained as local fallback and default for personal-data agents (resume, cover-letter, interview). Phi-4-mini retained as a lightweight CPU-friendly config.
- **Agent framework:** Plain LangChain vs LangGraph. LangGraph chosen for long-running, stateful agent workflows.
- **PDF:** wkhtmltopdf, ReportLab, FPDF, Typst considered. WeasyPrint chosen for CSS fidelity.

## Consequences

**Positive:**
- Parsing uses a free cloud LLM (Groq) — fast, stable, no Docker/VRAM pressure.
- All sensitive/personal data paths (resume, CV, cover letter agents) remain local via Ollama by default.
- Stack aligns with owner's existing skills
- Permissive licenses avoid redistribution restrictions

**Negative:**
- Redis and MinIO licenses (RSALv2/SSPL, AGPLv3) are not strictly OSI-open but are fine for self-hosted offline use — documented as a caveat
- Multiple services increase operational footprint (mitigated by Docker Compose)

## Revisit When

- A truly OSI-only license stance is required (swap Redis → Valkey, MinIO → SeaweedFS)
- Scale demands require Kubernetes
