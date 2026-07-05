# RecruitFlow AI

AI-powered recruitment platform for staffing and recruitment firms.

## Tech Stack

- **Backend**: Python 3.13, FastAPI, SQLAlchemy (async), Celery, Argon2, JWT
- **Frontend**: Next.js 16 (App Router), TypeScript, Tailwind CSS, shadcn/ui, TanStack React Query
- **Database**: PostgreSQL 15 (Cloud SQL), Redis, Qdrant (vector DB)
- **File Storage**: MinIO (dev), GCP Cloud Storage (prod)
- **LLM**: Z.AI GLM 5.2 via LiteLLM
- **Infrastructure**: GCP Cloud Run (prod), Vercel (frontend)

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

## Project Structure

```
recruitflow-ai/
    frontend/           # Next.js application
    backend/            # FastAPI modular monolith
    docs/               # Architecture decisions (ADR.md) and component docs
    .agents/            # Agent operating files - conventions, progress, role definitions
    scripts/            # Utility scripts
    .github/workflows/  # CI/CD pipelines
```

## License

Proprietary - All Rights Reserved
