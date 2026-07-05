# RecruitFlow AI

AI-powered recruitment platform for staffing and recruitment firms - document
intelligence, applicant tracking, talent and job discovery, and an AI chat
interface, all built around a RAG pipeline over resumes, job descriptions,
and HR documents.

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white" />
  <img alt="SQLAlchemy" src="https://img.shields.io/badge/SQLAlchemy-2.x-D71F00?logo=sqlalchemy&logoColor=white" />
  <img alt="Celery" src="https://img.shields.io/badge/Celery-async%20tasks-37814A?logo=celery&logoColor=white" />
  <img alt="Next.js" src="https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white" />
  <img alt="React" src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black" />
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white" />
  <img alt="Tailwind CSS" src="https://img.shields.io/badge/Tailwind%20CSS-3-06B6D4?logo=tailwindcss&logoColor=white" />
  <img alt="TanStack Query" src="https://img.shields.io/badge/TanStack%20Query-5-FF4154?logo=reactquery&logoColor=white" />
</p>
<p>
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white" />
  <img alt="Redis" src="https://img.shields.io/badge/Redis-cache%20%26%20broker-DC382D?logo=redis&logoColor=white" />
  <img alt="Qdrant" src="https://img.shields.io/badge/Qdrant-vector%20DB-DC244C?logo=qdrant&logoColor=white" />
  <img alt="MinIO" src="https://img.shields.io/badge/MinIO-dev%20storage-C72E49?logo=minio&logoColor=white" />
  <img alt="LiteLLM" src="https://img.shields.io/badge/LiteLLM-GLM%205.2%20via%20DeepInfra-6E56CF" />
  <img alt="LlamaIndex" src="https://img.shields.io/badge/LlamaIndex-RAG%20pipeline-6533EE" />
  <img alt="JWT" src="https://img.shields.io/badge/Auth-JWT%20%2B%20Argon2-000000?logo=jsonwebtokens&logoColor=white" />
</p>
<p>
  <img alt="Google Cloud" src="https://img.shields.io/badge/Google%20Cloud-Cloud%20Run%20%2F%20Cloud%20SQL%20%2F%20GCS-4285F4?logo=googlecloud&logoColor=white" />
  <img alt="Vercel" src="https://img.shields.io/badge/Vercel-frontend%20hosting-000000?logo=vercel&logoColor=white" />
  <img alt="Doppler" src="https://img.shields.io/badge/Doppler-secrets%20management-000000?logo=doppler&logoColor=white" />
  <img alt="GitHub Actions" src="https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white" />
  <img alt="pytest" src="https://img.shields.io/badge/tested%20with-pytest%20%2F%20vitest-0A9EDC?logo=pytest&logoColor=white" />
</p>

## Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Setup Instructions](#setup-instructions)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [License](#license)

## Overview

RecruitFlow AI centralizes the day-to-day work of a staffing/recruitment
firm - intake and tag every document that comes in, track candidates and
requisitions through a pipeline, search for the right person or the right
role, and generate client-ready documents - behind a single AI-assisted
workspace instead of a pile of spreadsheets and email threads.

## Features

Feature areas map to backend modules under `backend/app/modules/` and
frontend routes under `frontend/app/(dashboard)/`. Status reflects the
current build, not the final scope - see `.agents/progress.md` (private
companion repo) for day-to-day tracking.

| Area | What it does | Status |
|---|---|---|
| **Doc Studio** (`documents`) | Upload, auto-tag, and AI-generate recruitment documents (resumes reformatting, JD drafts, offer letters) with a RAG-backed writing assistant | In progress |
| **ATS** (`recruiter`, `candidate`, `jobs`) | Track candidates through a hiring pipeline against open requisitions | Planned |
| **Document Management** | Client-scoped document library with tagging, search, and lifecycle management | Planned |
| **Talent Finder** (`recruiter`) | Search and rank candidates against a job description using the RAG pipeline + resume scoring | Planned |
| **Job Finder** (`jobs`) | Match open roles to candidates, generate platform-optimized job postings (LinkedIn, WorkIndia, JobHai) | Planned |
| **AI Chat Interface** (`chat`) | Conversational interface over the firm's own documents (RAG) for ad-hoc Q&A and drafting | Planned |
| **Analytics** (`analytics`) | Pipeline and usage reporting across clients | Planned |
| **Auth** (`auth`) | JWT-based authentication, Argon2 password hashing, per-client data isolation | Foundation complete |

Every RAG search and AI action is scoped to a `client_id`, so a single
deployment can serve multiple staffing firms without their data mixing.

## Tech Stack

**Backend** - Python 3.13, FastAPI, SQLAlchemy 2.x (async), Alembic
migrations, Celery + Redis for async workloads, Argon2 password hashing,
JWT auth, PyMuPDF/python-docx for document parsing.

**Frontend** - Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS,
shadcn/ui + Radix primitives, TanStack React Query, React Hook Form + Zod.

**Data & Storage** - PostgreSQL 15 (Cloud SQL in prod), Redis (cache +
Celery broker/backend), Qdrant (vector search), MinIO (dev file storage) /
GCP Cloud Storage (prod file storage), both behind the same S3-compatible
boto3 interface.

**AI / RAG** - LlamaIndex for document ingestion, chunking, and retrieval;
Sentence Transformers (`BAAI/bge-small-en-v1.5`) for local embeddings;
GLM 5.2 (via DeepInfra) as the LLM, called through a single shared LiteLLM
helper (`backend/app/core/llm.py`) so the model string and API key live in
exactly one place.

**Infrastructure** - GCP Cloud Run (backend), Vercel (frontend), Cloud SQL,
GCS, Doppler for all secrets (no `.env` files anywhere), GitHub Actions for
CI/CD (lint, type-check, tests, CodeQL, dependency/secret scanning,
Cloud Run deploy on push to `main`).

See [`docs/ADR.md`](docs/ADR.md) for the reasoning behind each of these
choices (modular monolith over microservices, LlamaIndex over LangChain,
local embeddings over a paid embeddings API, LiteLLM as the provider
abstraction, MinIO/GCS split, Redis/Qdrant hosting).

## Architecture

Backend is a modular monolith (one FastAPI process, module boundaries
clean enough to extract into services later if needed) rather than
microservices - overkill for the current team size and scale. Celery
handles anything that shouldn't block a request (document processing,
embedding generation, AI generation jobs). All LLM calls funnel through
`core/llm.py`; all object storage funnels through `core/storage.py`'s
S3-compatible interface so dev (MinIO) and prod (GCS) need no code changes,
only different credentials/endpoints via Doppler.

## Setup Instructions

### Prerequisites

- Python 3.13 (for backend)
- Node.js 20 (for frontend)
- [Doppler CLI](https://docs.doppler.com/docs/install-cli) - this project has no `.env` files, ever; all secrets and config are injected via `doppler run --`. You'll need access to the `recruitflow-ai` Doppler project.
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) and the [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy) - dev/test is GCP-only (no local Postgres, no Docker Compose), so the backend connects to the real Cloud SQL instance through the proxy even locally.

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/akshatVardhan/recruitflow-ai.git
   cd recruitflow-ai
   ```

2. Authenticate Doppler and select the project config:
   ```bash
   doppler login
   doppler setup   # select project: recruitflow-ai, config: dev
   ```

3. Start the Cloud SQL Auth Proxy (needed for any backend work that touches the database):
   ```bash
   cloud-sql-proxy recruitflow-ai-500719:asia-south1:recruitflow-db
   ```

4. Start the backend:
   ```bash
   cd backend && doppler run -- uvicorn app.main:app --reload
   ```

5. In a separate terminal, start the frontend:
   ```bash
   cd frontend && doppler run -- npm run dev
   ```

6. Access the services:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

Never create a `.env` file in this project. If you see one, it's leftover drift - delete it; the real values already live in Doppler.

A more detailed walkthrough (migrations, running tests, troubleshooting)
lives in [`docs/local-setup.md`](docs/local-setup.md).

## Project Structure

```
recruitflow-ai/
    frontend/               # Next.js application (App Router)
        app/                #   route groups: (auth), (dashboard)/{ats,chat,doc-studio,documents,job-finder,talent-finder}
        components/         #   shared + shadcn/ui components
        hooks/, lib/, types/
    backend/                # FastAPI modular monolith
        app/
            modules/        #   auth, recruiter, candidate, documents, jobs, rag, chat, analytics
            core/            #   config, db, storage, qdrant, embeddings, llm
            api/
        alembic/             # database migrations
        tests/
    docs/                    # ADR.md, COMPONENTS.md, local-setup.md
    scripts/                 # utility scripts (e.g. sync-agent-files.sh)
    .github/workflows/       # CI/CD pipelines (lint/test/security/deploy)
    .env.example             # documents variable names only - not used to run the app
```

Agent operating files (`.agents/`, `AGENTS.md`, `.opencode/`, `opencode.json`)
live in a private companion repo and are pulled in locally via
`scripts/sync-agent-files.sh` - they're internal process docs, not part of
the shipped product.

## Documentation

- [`docs/ADR.md`](docs/ADR.md) - architectural decisions and the reasoning behind them
- [`docs/COMPONENTS.md`](docs/COMPONENTS.md) - frontend component registry
- [`docs/local-setup.md`](docs/local-setup.md) - detailed local development walkthrough

## License

Proprietary - All Rights Reserved
