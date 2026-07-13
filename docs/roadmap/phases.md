# Development Roadmap

16 phases from scaffold to automation. Estimates assume one full-time developer; buffer for model tuning.

| Phase | Focus | Key Deliverable | Est. |
|-------|-------|-----------------|------|
| **0** | Project setup | Docker stack + repo scaffolding + stubs | 2 wk |
| **1** | User profile | Profile CRUD + frontend editor | 2 wk |
| **2** | Knowledge base | Upload → extract → embed → store pipeline | 3 wk |
| **3** | Job parser | URL/text/PDF → structured job data | 2 wk |
| **4** | Job analysis agent | Match report (gaps, ATS score, fit) | 2 wk |
| **5** | Resume builder | Tailored resume with versioning | 3 wk |
| **6** | PDF engine | HTML/LaTeX/Typst/DOCX → PDF | 2 wk |
| **7** | ATS optimizer | Score + suggestions | 2 wk |
| **8** | Cover letter agent | Company/role-specific letters | 1 wk |
| **9** | Interview agent | Q generation + mock interview + feedback | 3 wk |
| **10** | Application tracker | Pipeline tracking + dashboard | 2 wk |
| **11** | Company intelligence | Tech stack, culture, interview exp. report | 2 wk |
| **12** | Learning planner | Skill gap → 14-day roadmap | 2 wk |
| **13** | Analytics dashboard | Charts (response rate, ATS trend, etc.) | 2 wk |
| **14** | Memory | Persistent agent memory service | 2 wk |
| **15** | Automation | Daily scan + auto-prep + notifications | 2 wk |

**Total: ~32 weeks** (buffered).

## Phase Details

### Phase 0 — Project Setup ✅
- Initialize 4 repos (platform, prompts, models, docs)
- Docker Compose: PostgreSQL + pgvector, Qdrant, Ollama, Redis, MinIO
- FastAPI skeleton with health routes
- Next.js skeleton with Tailwind
- Alembic migrations baseline
- CI pipeline (lint, typecheck, test, build)
- **Deliverable:** Running platform, no intelligence

### Phase 1 — User Profile
- Data model: Profile, Experience, Projects, Education, Skills, Certificates, Achievements, Publications, Languages, GitHub, LinkedIn
- CRUD API + frontend profile editor
- Structured storage of all career data

### Phase 2 — Knowledge Base
- Upload: CV, certificates, transcripts, projects, portfolio, GitHub READMEs, blogs
- Pipeline: Extract (Tika/pdfplumber) → Chunk → Embed (bge-m3) → Store (Qdrant)
- MinIO for raw file storage

### Phase 3 — Job Parser
- Input: URL (Playwright + BeautifulSoup), pasted text, or PDF
- Extract: Company, Role, Salary, Requirements, Responsibilities, Skills, Experience, Keywords, Location, Tech Stack
- spaCy NER + regex + LLM-assisted parsing
- Store in `Job_Posts` with parsed JSON

### Phase 4 — Job Analysis Agent
- Output: Missing skills, Strengths, Weaknesses, ATS score, Culture fit, Interview difficulty, Company summary, Likely interview topics
- LangGraph agent using embeddings against profile

### Phase 5 — Resume Builder
- Input: Job + Master Resume → tailored Resume Version
- Versioning (v1, v2, v3 — never overwrite)
- LLM rewrites/reorders bullet points via prompts
- Vector retrieval of matching CV sections

### Phase 6 — PDF Engine
- Import PDF templates, convert, edit, generate
- Support: HTML (Jinja2 + WeasyPrint), LaTeX, Typst, DOCX, PDF

### Phase 7 — ATS Optimizer
- Checks: Keyword match, Action verbs, Length, Formatting, Quantified achievements, Missing skills, Readability
- Output: Score + Suggestions
- Iterative refinement loop

### Phase 8 — Cover Letter Agent
- Generate: Company-specific, Hiring-manager-specific, Role-specific
- Stored per application with versioning

### Phase 9 — Interview Agent
- Generate: Technical, Behavioral, Coding, System Design, ML, Backend, Leadership
- Mock interview flow: Q → A → Evaluate → Feedback → Score
- STAR method for behavioral

### Phase 10 — Application Tracker
- Store: Company, Position, Resume version, Cover letter version, Dates, Recruiter, Status, Salary, Location, Notes
- Status: Wishlist → Preparing → Applied → OA → Interview → HR → Final → Offer → Rejected → Accepted
- Dashboard / CLI listing

### Phase 11 — Company Intelligence
- Collect: Tech stack, Products, Competitors, Funding, Culture, Interview experiences
- Generate company report (offline / cached sources)

### Phase 12 — Learning Planner
- Compare job requirements vs. user skills → identify gaps
- Generate 14-day learning roadmap with resources, projects, practice questions

### Phase 13 — Analytics Dashboard
- Charts: Applications, Response rate, Interview rate, Offer rate, ATS score trend, Companies, Technologies, Skill demand, Monthly applications

### Phase 14 — Memory
- Agent remembers: Preferred resume, writing style, tech stack, companies, interview history, previous applications, recruiter feedback
- Persistent memory service (Qdrant long-term storage)

### Phase 15 — Automation
- Daily: Scan saved jobs → Compare profile → Recommend jobs → Prepare resume → Prepare interview questions → Notify dashboard
- Scheduler (Celery beat / ARQ cron)

## Cross-Cutting Concerns

- **Security:** Encrypt sensitive data at rest; bind to localhost; file permissions 600
- **Offline-only:** No external API calls; all models on-device
- **Testing:** Unit tests per module; integration tests via Docker Compose; mock LLMs for CI
- **Observability:** OpenTelemetry + Prometheus + Grafana (scaffold in Phase 0, enrich per phase)
- **CI/CD:** GitHub Actions — lint, typecheck, test, build on every PR
