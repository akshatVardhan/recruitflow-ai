# RecruitFlow AI - Local Development Setup

# Start-to-finish guide for setting up the RecruitFlow AI development
# environment on a local machine.

---

## Prerequisites

- Git
- A code editor (VS Code recommended)
- Python 3.13 (for backend)
- Node.js 20 (for frontend)
- [Doppler CLI](https://docs.doppler.com/docs/install-cli) - this project has
  no `.env` files, ever, under any circumstance. All secrets and config are
  injected via `doppler run --`. You need access to the `recruitflow-ai`
  Doppler project (config: `dev`).
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) and the
  [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy) -
  dev/test is GCP-only. There is no local Postgres and no Docker Compose;
  the backend connects to the real Cloud SQL instance through the proxy
  even for local development.

---

## Step 1 - Clone the Repository

```bash
git clone https://github.com/akshatVardhan/recruitflow-ai.git
cd recruitflow-ai
```

---

## Step 2 - Authenticate Doppler

```bash
doppler login
doppler setup   # select project: recruitflow-ai, config: dev
```

If a variable is missing, the command using it fails naturally - that
failure is the signal to check Doppler, not to create a `.env` file.
`.env.example` at the repo root documents variable names only; it is
never copied to an actual `.env`.

---

## Step 3 - Start the Cloud SQL Auth Proxy

Needed for any backend work that touches the database:

```bash
cloud-sql-proxy recruitflow-ai-500719:asia-south1:recruitflow-db
```

---

## Step 4 - Run Database Migrations

```bash
cd backend && doppler run -- alembic upgrade head
```

---

## Step 5 - Run Services Directly

Start each service in its own terminal:

```bash
# Terminal 1: Backend
cd backend && doppler run -- uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend && doppler run -- npm run dev
```

---

## Step 6 - Access the Application

| Service    | URL                          |
|------------|------------------------------|
| Frontend   | http://localhost:3000        |
| Backend    | http://localhost:8000        |
| API Docs   | http://localhost:8000/docs   |

---

## Step 7 - Run Tests

Backend tests:
```bash
cd backend && doppler run -- pytest tests/ -v
```

Frontend tests:
```bash
cd frontend && npx vitest run
```

---

## Troubleshooting

### Port conflicts
If any port (8000, 3000) is already in use, stop
the conflicting service or change the port mapping.

### Backend fails to start
- Verify `doppler setup` points at the `recruitflow-ai` / `dev` config and you're running commands through `doppler run --`
- Verify the Cloud SQL Auth Proxy is running (Step 3) before starting the backend
- Check backend logs for startup errors

### Frontend fails to start
- Verify backend is running and reachable
- Check frontend logs for startup errors
- Verify Doppler provides `NEXT_PUBLIC_API_BASE_URL` (defaults to `http://localhost:8000` for local dev)

### "Missing .env" or similar advice found elsewhere
This project never uses `.env` files. If you find outdated instructions telling you to create one, that's drift - all real values live in Doppler.
