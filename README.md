# RecruitFlow AI

AI-powered recruitment platform for staffing and recruitment firms.

## Tech Stack

- **Backend**: Python 3.13, FastAPI, SQLAlchemy (async), Celery, Argon2, JWT
- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui, TanStack React Query
- **Database**: PostgreSQL 15, Redis 7, Qdrant (vector DB)
- **File Storage**: MinIO (dev), GCP Cloud Storage (prod)
- **LLM**: Z.AI GLM 5.2 via LiteLLM
- **Infrastructure**: GCP Cloud Run (prod), Vercel (frontend)

## Setup Instructions

### Prerequisites

- Python 3.13 (for backend)
- Node.js 20 (for frontend)

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/akshatvardhan/recruitflow-ai.git
   cd recruitflow-ai
   ```

2. Copy environment files:
   ```bash
   cp .env.example backend/.env
   cp .env.example frontend/.env
   ```

3. Start the backend:
   ```bash
   cd backend && uvicorn app.main:app --reload
   ```

4. In a separate terminal, start the frontend:
   ```bash
   cd frontend && npm run dev
   ```

5. Access the services:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Running Without Docker

See the individual `backend/` and `frontend/` README files for local setup instructions.

## Project Structure

```
recruitflow-ai/
    frontend/           # Next.js application
    backend/            # FastAPI modular monolith
    docs/               # Architecture and component documentation
    scripts/            # Utility scripts
    .github/workflows/  # CI/CD pipelines
```

## License

Proprietary - All Rights Reserved
