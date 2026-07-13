# Data Models / ER Diagram

## Entity-Relationship Diagram

```mermaid
erDiagram
    Users ||--o{ CV_Versions : owns
    Users ||--o{ Applications : submits
    Users ||--o{ Interview_Guides : has
    Users ||--o{ Logs : performs

    CV_Templates ||--o{ CV_Versions : "rendered from"
    Job_Posts ||--o{ Applications : "applied to"
    CV_Versions ||--o{ Applications : "used in"
    Applications ||--o{ Interview_Guides : "generates"

    Users {
        uuid id PK
        string username
        string hashed_password
        text personal_info_json
        timestamp created_at
    }

    CV_Templates {
        uuid id PK
        string name
        string description
        string format "HTML|Markdown|LaTeX|Typst"
        text content_or_path
        timestamp created_at
    }

    CV_Versions {
        uuid id PK
        uuid user_id FK
        uuid template_id FK
        timestamp created_at
        timestamp modified_at
        text content
        string hash
        json metadata
    }

    Job_Posts {
        uuid id PK
        string url
        string title
        string company
        string location
        text raw_text
        json parsed_fields "skills, requirements, responsibilities, salary"
        timestamp date_scraped
    }

    Applications {
        uuid id PK
        uuid user_id FK
        uuid job_id FK
        uuid cv_id FK
        enum status "wishlist|preparing|applied|oa|interview|hr|final|offer|rejected|accepted"
        date date_applied
        timestamp last_updated
        text notes
        string recruiter
        string salary
    }

    Interview_Guides {
        uuid id PK
        uuid application_id FK
        json generated_questions "list of {question_text, category, difficulty}"
        json ideal_answers
        text feedback
        timestamp created_at
    }

    Embeddings {
        uuid id PK
        string parent_type "cv|job|profile"
        uuid parent_id FK
        vector vector_1024
        text metadata
    }

    Logs {
        uuid id PK
        timestamp timestamp
        uuid user_id FK
        string action "import_job|customize_cv|start_interview|..."
        json details
    }
```

## Storage Strategy

| Data | Store | Reason |
|------|-------|--------|
| Relational entities (Users, Jobs, Applications, etc.) | PostgreSQL | ACID, joins, structured queries |
| Inline vectors (small collections, profile embeddings) | pgvector | Collocated with relational data |
| Large-scale vector search (CV sections, job corpus) | Qdrant | Specialized performance, filtering |
| Raw uploaded files (PDFs, CVs, certificates) | MinIO | Object storage with versioning |
| Cache + task queue | Redis | Fast ephemeral storage, Celery/ARQ broker |
| Prompt templates | `prompts/` folder (filesystem) | Version-controlled, decoupled |

## Notes

- `parsed_fields` on `Job_Posts` is JSON to accommodate varying job-post structures.
- `CV_Versions` keeps a hash for deduplication and a full history (never overwrite).
- `Embeddings.parent_id` is a polymorphic FK — enforce via application logic, not DB constraint.
- `Interview_Guides.generated_questions` stores the full Q&A transcript after a mock interview.
- Sensitive fields (e.g. personal contact info) should be encrypted at the application layer using `APP_ENCRYPTION_KEY`.
