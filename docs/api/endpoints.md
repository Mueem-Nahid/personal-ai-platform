# API Endpoints

Base path: `/api/v1`

## Health

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness probe |
| `/health/ready` | GET | Readiness probe |

## Jobs

| Endpoint | Method | Description | Body / Output |
|----------|--------|-------------|---------------|
| `/jobs` | GET | List stored jobs | JSON list |
| `/jobs` | POST | Add job (URL or text) | `{url?, text?}` → `{job_id}` |
| `/jobs/{id}` | GET | Job details (parsed) | JSON job object |
| `/jobs/{id}` | DELETE | Remove a job | — |

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

## Conventions

- All responses are JSON except PDF endpoints (`Content-Type: application/pdf`).
- Errors use RFC 7807 `application/problem+json`.
- No auth in Phase 0 (local only). Token auth added in a later phase if multi-user.
