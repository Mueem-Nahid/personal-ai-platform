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

## Source Documents

The design was informed by:
- `research/deep-research-report.md` — technical research (data models, ML pipeline, tech stack)
- `research/Personalized Job Application Agent.md` — multi-repo architecture and phased plan

## Sibling Folders

- `../backend/` — FastAPI application
- `../frontend/` — Next.js UI
- `../prompts/` — versioned prompt templates
- `../models/` — model configs and Ollama manifests
