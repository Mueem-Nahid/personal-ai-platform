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
| LLM runtime | Ollama | MIT |
| Default LLM | Qwen3 8B | Apache 2.0 |
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
- **LLM:** Phi-4-mini (smaller, CPU-friendly) and Mistral Small 3.1 were considered. Qwen3 8B chosen as default; Phi-4-mini retained as a fallback config.
- **Agent framework:** Plain LangChain vs LangGraph. LangGraph chosen for long-running, stateful agent workflows.
- **PDF:** wkhtmltopdf, ReportLab, FPDF, Typst considered. WeasyPrint chosen for CSS fidelity.

## Consequences

**Positive:**
- All components run locally without external API calls
- Stack aligns with owner's existing skills
- Permissive licenses avoid redistribution restrictions

**Negative:**
- Redis and MinIO licenses (RSALv2/SSPL, AGPLv3) are not strictly OSI-open but are fine for self-hosted offline use — documented as a caveat
- Multiple services increase operational footprint (mitigated by Docker Compose)

## Revisit When

- A truly OSI-only license stance is required (swap Redis → Valkey, MinIO → SeaweedFS)
- Scale demands require Kubernetes
