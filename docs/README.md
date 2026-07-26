# Career Agent Docs

Architecture, API specs, ADRs, roadmap, data models, and diagrams for the career-agent platform.

## Structure

```
architecture/   # system design, component descriptions
api/            # REST endpoint documentation
adr/            # architecture decision records
roadmap/        # phased development plan
diagrams/       # mermaid diagrams (architecture, sequence, ER)
data-models/    # entity-relationship design
research/       # original source documents
```

## Architecture Decision Records

| ADR | Title | Status |
|-----|-------|--------|
| [0001](./adr/0001-monorepo-structure.md) | Monorepo Structure | Accepted |
| [0002](./adr/0002-tech-stack-selection.md) | Tech Stack Selection | Accepted (amended for cloud LLM) |
| [0003](./adr/0003-local-llm-qwen3.md) | Default Local LLM — Qwen3 8B | Amended (superseded for parsing by 0004) |
| [0004](./adr/0004-cloud-llm-for-parsing.md) | Cloud LLM for Job-Post Parsing (Groq Llama 3.1 8B) | Accepted |

## Source Documents

The design was informed by:
- `research/deep-research-report.md` — technical research (data models, ML pipeline, tech stack)
- `research/Personalized Job Application Agent.md` — multi-repo architecture and phased plan

## Sibling Folders

- `../backend/` — FastAPI application
- `../frontend/` — Next.js UI
- `../prompts/` — versioned prompt templates
- `../models/` — model configs and Ollama manifests
