# RecruitFlow AI - Local Development Setup

# Start-to-finish guide for setting up the RecruitFlow AI development
# environment on a local machine.

---

## Prerequisites

- Git
- A code editor (VS Code recommended)
- Python 3.13 (for backend)
- Node.js 20 (for frontend)

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
- `DATABASE_URL` - connection string for PostgreSQL
- `JWT_SECRET_KEY` - generate a random 32-byte hex key
- `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` - credentials for local MinIO

**frontend/.env required values:**
- `NEXT_PUBLIC_API_BASE_URL` - use `http://localhost:8000` for local dev

---

## Step 3 - Run Services Directly

Start each service in its own terminal:

```bash
# Terminal 1: Backend
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

---

## Step 4 - Run Database Migrations

```bash
cd backend && alembic upgrade head
```

---

## Step 5 - Access the Application

| Service    | URL                          |
|------------|------------------------------|
| Frontend   | http://localhost:3000        |
| Backend    | http://localhost:8000        |
| API Docs   | http://localhost:8000/docs   |

---

## Step 6 - Run Tests

Backend tests:
```bash
cd backend && pytest tests/ -v
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
- Verify backend/.env has all required values
- Check backend logs for startup errors

### Frontend fails to start
- Verify backend is running and reachable
- Check frontend logs for startup errors
- Verify frontend/.env has NEXT_PUBLIC_API_BASE_URL set
