# Architecture Diagrams

## System Architecture

```mermaid
flowchart TB
    User([User])

    subgraph Client
      Web[Next.js Dashboard]
      CLI[CLI]
    end

    subgraph Gateway
      API[FastAPI Gateway]
    end

    subgraph Queue
      ARQWorker[ARQ Worker]
      RedisQ[(Redis ARQ queue)]
    end

    subgraph Agents
      CVAgent[CV Agent]
      JobAgent[Job Analyzer Agent]
      IntAgent[Interview Coach Agent]
      CoverAgent[Cover Letter Agent]
      CompanyAgent[Company Research Agent]
      LearnAgent[Learning Planner Agent]
    end

    subgraph Services
      Parser[Job/CV Parser]
      Tracker[Application Tracker]
      Analytics[Analytics Service]
      Memory[Memory Service]
      Scheduler[Scheduler]
    end

    subgraph Data
      PG[(PostgreSQL + pgvector)]
      Qdrant[(Qdrant)]
      MinIO[(MinIO)]
    end

    subgraph Inference
      GroqLLM[Groq - Llama 3.1 8B (parse)]
      OllamaEmb[Ollama - bge-m3 (embeddings)]
    end

    User --> Web
    User --> CLI
    Web --> API
    CLI --> API

    API -->|enqueue parse| RedisQ
    ARQWorker -->|dequeue| RedisQ
    ARQWorker --> GroqLLM
    ARQWorker --> PG

    API --> CVAgent
    API --> JobAgent
    API --> IntAgent
    API --> CoverAgent
    API --> CompanyAgent
    API --> LearnAgent
    API --> Tracker
    API --> Analytics

    CVAgent --> Qdrant
    CVAgent --> OllamaEmb
    JobAgent --> Qdrant
    JobAgent --> OllamaEmb
    IntAgent --> OllamaEmb
    CoverAgent --> OllamaEmb
    CompanyAgent --> OllamaEmb
    LearnAgent --> OllamaEmb

    Parser --> PG
    Parser --> Qdrant
    Tracker --> PG
    Analytics --> PG
    Memory --> Qdrant
    Memory --> PG
    Scheduler --> RedisQ
    Scheduler --> API

    CVAgent --> MinIO
    Parser --> MinIO
```

## Job Parsing Sequence (Phase 3 — ARQ + Groq)

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend (Next.js)
    participant A as FastAPI
    participant R as Redis (ARQ)
    participant W as ARQ Worker
    participant L as Groq LLM
    participant DB as PostgreSQL

    U->>F: paste job text, click Parse
    F->>A: POST /api/v1/jobs/parse-text {text}
    A->>DB: INSERT JobPost (status="parsing")
    A->>R: enqueue_job("parse_text", job_id, text)
    A-->>F: 202 {job_id, status:"parsing"}

    loop poll every 2s (max 60s)
        F->>A: GET /api/v1/jobs/{job_id}
        A-->>F: {status: "parsing"}
    end

    W->>R: dequeue parse_text
    W->>DB: SELECT JobPost
    W->>L: llm_parse(raw_text) via Groq API
    L-->>W: JSON {title, company, skills, ...}
    W->>DB: UPDATE JobPost (status="parsed", parsed_fields)

    F->>A: GET /api/v1/jobs/{job_id}
    A-->>F: {status: "parsed", parsed_fields: {...}}
    F-->>U: show parsed result
```

## CV Customization Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant W as Web/CLI
    participant A as API
    participant DB as PostgreSQL
    participant V as Qdrant
    participant L as Ollama (local)
    participant M as MinIO

    U->>W: select job + template
    W->>A: POST /cvs/{id}/customize {job_id}
    A->>DB: fetch job, template, profile
    A->>V: query CV embeddings vs job skills
    V-->>A: top matching sections
    A->>L: generate tailored bullets (cv-customize v1)
    L-->>A: rewritten sections
    A->>A: render Jinja2 HTML
    A->>M: store PDF
    A-->>W: return PDF URL
    W-->>U: preview + download
```

## Mock Interview Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant W as Web/CLI
    participant A as API
    participant L as Ollama (local)
    participant DB as PostgreSQL

    U->>W: start interview (app_id)
    W->>A: GET /interview/{app_id}
    A->>L: generate questions (interview-behavioral v1)
    L-->>A: question list
    A->>DB: persist interview guide
    A-->>W: first question
    W-->>U: show question

    loop until all questions answered
        U->>W: types answer
        W->>A: POST /interview/{app_id} {question_id, answer}
        A->>L: evaluate answer
        L-->>A: feedback + score
        A->>DB: log Q&A
        A-->>W: feedback + next question
        W-->>U: show feedback
    end

    U->>W: finish
    W->>A: GET /interview/{app_id}/report
    A->>DB: aggregate scores
    A-->>W: full report
    W-->>U: show report
```

## Application Tracker State Machine

```mermaid
stateDiagram-v2
    [*] --> Wishlist
    Wishlist --> Preparing: analyze + prep CV
    Preparing --> Applied: submit application
    Applied --> OA: online assessment sent
    Applied --> Interview: invited directly
    OA --> Interview: OA passed
    OA --> Rejected: OA failed
    Interview --> HR: technical round passed
    HR --> Final: final round
    Final --> Offer: selected
    Final --> Rejected: not selected
    Offer --> Accepted: candidate accepts
    Offer --> Rejected: candidate declines
    Interview --> Rejected: rejected mid-process
    Accepted --> [*]
    Rejected --> [*]
```
