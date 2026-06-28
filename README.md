# RecruitFlow AI

AI-powered recruitment platform for staffing and recruitment firms.

## Tech Stack

- **Backend**: Python 3.13, FastAPI, SQLAlchemy (async), Celery, Argon2, JWT
- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui, TanStack React Query
- **Database**: PostgreSQL 15, Redis 7, Qdrant (vector DB)
- **File Storage**: MinIO (dev), GCP Cloud Storage (prod)
- **LLM**: DeepSeek via LiteLLM
- **Infrastructure**: Docker Compose (local), GCP Cloud Run (prod), Vercel (frontend)

## Setup Instructions

### Prerequisites

- Docker and Docker Compose
- Python 3.13 (for local backend development)
- Node.js 20 (for local frontend development)

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

3. Start the full development stack:
   ```bash
   docker compose up -d
   ```

4. Access the services:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - MinIO Console: http://localhost:9001

### Running Without Docker

See the individual `backend/` and `frontend/` README files for local setup instructions.

## Project Structure

```
recruitflow-ai/
    frontend/           # Next.js application
    backend/            # FastAPI modular monolith
    agents/             # AI agent configuration and prompts
    docs/               # Architecture and component documentation
    docker/             # Docker-related files
    scripts/            # Utility scripts
    .github/workflows/  # CI/CD pipelines
```

## License

Proprietary - All Rights Reserved
