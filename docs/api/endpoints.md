# API Endpoints

Base path: `/api/v1`

## Health

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness probe |
| `/health/ready` | GET | Readiness probe |
| `/health/llm` | GET | LLM configuration (provider, model, API key status, timeout) |

## Jobs

| Endpoint | Method | Description | Body / Output |
|----------|--------|-------------|---------------|
| `/jobs` | GET | List stored jobs | `JobPostListOut` |
| `/jobs/{id}` | GET | Job details (parsed) | `JobPostOut` |
| `/jobs/{id}` | DELETE | Remove a job | 204 |
| `/jobs/parse-url` | POST | Parse job from URL | `{url}` → 202 `{job_id, status:"parsing"}` |
| `/jobs/parse-text` | POST | Parse job from pasted text | `{text, url?}` → 202 `{job_id, status:"parsing"}` |
| `/jobs/parse-pdf` | POST | Parse job from PDF upload | multipart `file` → 202 `{job_id, status:"parsing"}` |

All `POST` parse endpoints return **HTTP 202** immediately with `{job_id, status:"parsing"}`.
Parsing is dispatched to a **separate ARQ Redis worker**. Poll `GET /jobs/{id}` to monitor
completion (status transitions to `"parsed"` or `"failed"`). The backend startup sweeper
auto-recovers stranded jobs older than 5 minutes.

JobPost model fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique job identifier |
| `url` | string? | Source URL (if any) |
| `source` | string | `"url"`, `"text"`, or `"pdf"` |
| `status` | string | `"parsing"`, `"parsed"`, or `"failed"` |
| `raw_text` | string? | Original job posting text |
| `parsed_fields` | JSON | Structured extraction (title, company, location, salary, experience, employment_type, requirements, responsibilities, skills, keywords, tech_stack) |
| `title` | string? | Job title |
| `company` | string? | Company name |
| `location` | string? | Job location |
| `created_at` | datetime | When the job was created |
| `updated_at` | datetime | Last status/timestamp update |

## CVs

| Endpoint | Method | Description | Body / Output |
|----------|--------|-------------|---------------|
| `/cvs` | GET | List CV versions and templates | JSON list |
| `/cvs` | POST | Create/parse a new CV from data | user data → `{cv_id}` |
| `/cvs/{id}` | GET | Fetch a CV version | JSON CV object |
| `/cvs/{id}/customize` | POST | Tailor CV to a job | `{job_id}` → PDF |
| `/cvs/{id}/ats` | POST | Score CV against a job | `{job_id}` → ATS report |

## Templates

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/templates` | GET | List CV templates |
| `/templates` | POST | Create a CV template |

## Applications

| Endpoint | Method | Description | Body |
|----------|--------|-------------|------|
| `/applications` | GET | List applications | — |
| `/applications` | POST | Add application | `{job_id, cv_id}` → `{app_id}` |
| `/applications/{id}` | GET | Application details | — |
| `/applications/{id}` | PUT | Update status / notes | `{status?, notes?}` |
| `/applications/{id}` | DELETE | Remove application | — |

## Interview

| Endpoint | Method | Description | Body |
|----------|--------|-------------|------|
| `/interview/{app_id}` | GET | Generate interview questions | — |
| `/interview/{app_id}` | POST | Submit answer (mock interview) | `{question_id, answer}` → feedback |
| `/interview/{app_id}/report` | GET | Full interview report | — |

## Profile

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/profile` | GET | Current user profile |
| `/profile` | PUT | Update profile |
| `/profile/knowledge` | POST | Upload knowledge-base file |

## Analytics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analytics/summary` | GET | Counts and rates |
| `/analytics/trends` | GET | Time-series (applications, ATS score) |
| `/analytics/skills` | GET | Skill demand aggregation |

## Logs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/log` | GET | Retrieve event logs |

## Status Enums

Application `status`:
`wishlist` → `preparing` → `applied` → `oa` → `interview` → `hr` → `final` → `offer` → `rejected` | `accepted`

Job `status`:
`parsing` → `parsed` | `failed`

## Conventions

- All responses are JSON except PDF endpoints (`Content-Type: application/pdf`).
- Errors use RFC 7807 `application/problem+json`.
- POST jobs endpoints return 202 Accepted (async processing via ARQ worker).
- LLM provider is configured via `APP_LLM_PROVIDER` env (default: `groq`). See [ADR 0004](../adr/0004-cloud-llm-for-parsing.md).
- No auth in Phase 0 (local only). Token auth added in a later phase if multi-user.
