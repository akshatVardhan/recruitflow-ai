# RecruitFlow AI - Local Development Setup

# Start-to-finish guide for setting up the RecruitFlow AI development
# environment on a local machine.

---

## Prerequisites

- Docker Desktop (v24+) or Docker Engine + Docker Compose
- Git
- A code editor (VS Code recommended)
- 4GB+ free RAM (Docker services consume ~2GB total)

---

## Step 1 - Clone the Repository

```bash
git clone https://github.com/akshatvardhan/recruitflow-ai.git
cd recruitflow-ai
```

---

## Step 2 - Create Environment Files

```bash
cp .env.example backend/.env
cp .env.example frontend/.env
```

Edit both `.env` files and fill in actual values. At minimum, set:

**backend/.env required values:**
- `DATABASE_URL` - use `postgresql+asyncpg://user:password@postgres:5432/recruitflow` for Docker
- `JWT_SECRET_KEY` - generate a random 32-byte hex key
- `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` - credentials for local MinIO

**frontend/.env required values:**
- `NEXT_PUBLIC_API_BASE_URL` - use `http://localhost:8000` for local dev

---

## Step 3 - Start the Full Development Stack

```bash
docker compose up -d
```

This starts all 7 services:
| Service        | Purpose                  | Port(s)   |
|----------------|--------------------------|-----------|
| postgres       | Primary database         | 5432      |
| redis          | Cache and task queue     | 6379      |
| qdrant         | Vector database          | 6333      |
| minio          | Object storage (S3-compatible) | 9000, 9001 |
| backend        | FastAPI application      | 8000      |
| frontend       | Next.js application      | 3000      |
| celery_worker  | Async task processing    | (no port) |

First start takes 1-3 minutes while Docker images download and services initialise.

---

## Step 4 - Verify All Services Are Healthy

```bash
docker compose ps
```

All services should show `Up` and `(healthy)` status. If any show `(unhealthy)`, wait 30 seconds and check again:

```bash
docker compose ps
```

---

## Step 5 - Run Database Migrations

```bash
docker compose exec backend alembic upgrade head
```

---

## Step 6 - Access the Application

| Service    | URL                          |
|------------|------------------------------|
| Frontend   | http://localhost:3000        |
| Backend    | http://localhost:8000        |
| API Docs   | http://localhost:8000/docs   |
| MinIO Console | http://localhost:9001     |
| Qdrant UI  | http://localhost:6333        |

---

## Step 7 - Run Tests

Backend tests:
```bash
docker compose exec backend pytest tests/ -v
```

Frontend tests:
```bash
docker compose exec frontend npx vitest run
```

---

## Common Commands

View all service logs:
```bash
docker compose logs -f
```

View logs for a single service:
```bash
docker compose logs -f backend
```

Stop all services:
```bash
docker compose down
```

Stop and remove all data volumes (destroys databases and file storage):
```bash
docker compose down -v
```

Rebuild a service after code changes:
```bash
docker compose up -d --build backend
```

---

## Troubleshooting

### Port conflicts
If any port (5432, 6379, 6333, 9000, 9001, 8000, 3000) is already in use, stop
the conflicting service or change the port mapping in docker-compose.yml.

### Backend fails to start
- Verify all infrastructure services (postgres, redis, qdrant, minio) are healthy
- Check backend logs: `docker compose logs backend`
- Verify backend/.env has all required values

### Frontend fails to start
- Verify backend is running and reachable
- Check frontend logs: `docker compose logs frontend`
- Verify frontend/.env has NEXT_PUBLIC_API_BASE_URL set

### Docker image build fails
- On Apple Silicon (M1/M2/M3): add `--platform linux/amd64` to the FROM line in Dockerfile
- On Windows: ensure Docker Desktop is using Linux containers

### MinIO access denied
- Default credentials in docker-compose.yml are `minioadmin` / `minioadmin`
- Override via environment variables if you changed them
- MinIO creates buckets on first write from backend/storage.py
