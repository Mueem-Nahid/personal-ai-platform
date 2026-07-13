# ADR 0001: Monorepo Structure

- **Status:** Accepted
- **Date:** 2026-07-14
- **Supersedes:** Initial multi-repo proposal (2026-07-13)

## Context

The initial design proposed four separate repositories (career-agent-platform, career-agent-prompts, career-agent-models, career-agent-docs) to allow independent versioning of prompts, models, and docs. On review, the overhead of multi-repo coordination (cross-repo commits, separate CI, local linking) outweighed the benefits for a solo-developer project at this stage. The "prompts change often" argument is satisfied equally well by a versioned subfolder.

## Decision

Use a **single monorepo** with logically separated top-level folders:

```
personal-ai-platform/
├── backend/        # FastAPI app
├── frontend/       # Next.js UI
├── workers/        # Background jobs
├── infrastructure/ # Dockerfiles, configs
├── scripts/        # Setup and dev helpers
├── prompts/        # Versioned prompt templates
├── models/         # LLM/embedding configs, Ollama manifests
├── docs/           # Architecture, ADRs, roadmap, data models
└── shared/         # Shared contracts
```

## Rationale

- **Atomic history** — a new endpoint + its prompt + its docs are one commit
- **Simpler setup** — one clone, one CI pipeline
- **No linking overhead** — imports and path references are direct
- **Preserved separation** — folder boundaries keep concerns isolated without git ceremony
- **Exit ramp preserved** — if a second product later needs to share prompts/models, extracting a subfolder to its own repo via `git filter-repo` is a one-time operation

## Consequences

**Positive:**
- Cross-cutting changes are atomic
- Single CI pipeline
- One clone for local dev
- Simpler dependency management

**Negative:**
- Single clone is larger (mitigated: prompts and model configs are small text files)
- Less granular access control (irrelevant for solo dev)
- Repository-level versioning not possible (mitigated: prompts and model configs carry their own `version` field in frontmatter/YAML)

## Revisit When

- A second deployable product needs to share prompts/models as versioned dependencies
- Multiple teams with different ownership boundaries contribute
