# RecruitFlow AI - Agent Prompts

# How to read this file
# - Find all prompts addressed to your agent role
# - Only act on prompts with status: Pending
# - Check Depends On field - do not start if dependency is not Done
# - Update status to In Progress before starting
# - Update status to Done after completing all required file updates
# - Do not modify prompts addressed to other agents

---

## Phase 1 - Foundation and Setup

---

### PROMPT-001
Agent: DevOps Engineer
JIRA: RF-6
Status: Done
Depends on: nothing
Priority: High - do this first, everything else depends on the repo existing

Task:
Initialize the GitHub repository recruitflow-ai with the full project structure.

Create the following folder structure committed to main:
frontend/ (empty placeholder with .gitkeep)
backend/ (empty placeholder with .gitkeep)
agents/ (copy all files from /agents/ folder in this repo)
docs/ (ADR.md and COMPONENTS.md empty templates)
docker/ (empty placeholder)
scripts/ (empty placeholder)
.github/workflows/ (empty placeholder)

Add to root:
- README.md with project name, tech stack summary, and setup instructions placeholder
- .gitignore covering Python, Node, .env files, __pycache__, .DS_Store, dist/, .next/
- .env.example with all variable names from conventions.md (no values)
- docker-compose.yml placeholder (populated in PROMPT-002)

Create branches: main (default), staging
Commit message: chore(repo): initialize project structure RF-6
Session ID format: YYYYMMDD-DO-P001

After completing:
- Update /agents/progress.md (RF-6 to Completed, your agent row)
- Update /agents/code-changes.md
- Update /agents/agent-run-log.md
- Transition JIRA RF-6 to In Testing

---

### PROMPT-002
Agent: DevOps Engineer
JIRA: RF-7
Status: Done
Depends on: PROMPT-001 Done
Priority: High

Task:
Create docker-compose.yml at the project root for the full local development stack.

Services to include:
- postgres: image postgres:15-alpine, port 5432, volume postgres_data, healthcheck pg_isready
- redis: image redis:7.2-alpine, port 6379, healthcheck redis-cli ping
- qdrant: image qdrant/qdrant:v1.9.0, port 6333, volume qdrant_data
- minio: image minio/minio:RELEASE.2024-05-01T01-11-10Z, port 9000 and 9001, volume minio_data, command server /data --console-address :9001
- backend: build ./backend, port 8000, depends on postgres/redis/qdrant/minio all healthy, env_file ./backend/.env
- frontend: build ./frontend, port 3000, env_file ./frontend/.env
- celery_worker: build ./backend, command celery -A app.worker worker --loglevel=info, same deps as backend

All services that need env vars use env_file pointing to local .env files.
All services have restart: unless-stopped.
Volumes declared at bottom: postgres_data, qdrant_data, minio_data.

Also update /agents/md/04_devops_engineer_agent.md Local Setup Guide section with exact commands.
Update Notion /Local Setup Guide page with start-to-finish local setup steps.

Commit message: chore(docker): add full local dev stack compose RF-7
Session: YYYYMMDD-DO-P002

---

### PROMPT-003
Agent: DevOps Engineer
JIRA: RF-8
Status: Done
Depends on: PROMPT-001 Done
Priority: High

Task:
Create GitHub Actions CI pipelines for backend and frontend.

Create .github/workflows/backend.yml:
- Trigger: push to feature/* and bugfix/* (paths: backend/**)
- Steps: checkout, python 3.13, pip install -r backend/requirements.txt, ruff check, black --check, mypy app/, pip-audit, pytest tests/ -v

Create .github/workflows/frontend.yml:
- Trigger: push to feature/* and bugfix/* (paths: frontend/**)
- Steps: checkout, node 20, npm ci, eslint, prettier --check, npm audit, vitest run, next build

Create .github/workflows/keepwarm.yml:
- Trigger: schedule cron "*/10 * * * *"
- Step: curl --fail $CLOUD_RUN_URL/api/v1/health (CLOUD_RUN_URL from GitHub secret)

Add required GitHub secrets to the repo settings (document names only, not values):
DATABASE_URL, CLOUD_RUN_URL, GCS_CREDENTIALS_JSON, LITELLM_API_KEY

Commit message: ci: add backend and frontend pipelines with keep-warm RF-8

---

### PROMPT-004
Agent: DevOps Engineer
JIRA: RF-9
Status: Pending
Depends on: nothing (can run parallel to PROMPT-002 and PROMPT-003)
Priority: High

Task:
Set up the GCP production infrastructure for RecruitFlow AI.

Steps:
1. Create GCP project named recruitflow-ai (separate from CommuteWatch)
2. Enable APIs: Cloud Run, Cloud SQL Admin, Cloud Storage, Secret Manager
3. Create Cloud SQL instance: PostgreSQL 15, tier db-f1-micro, region asia-south1 (Mumbai)
4. Create Cloud Storage bucket: recruitflow-ai-documents, region asia-south1
5. Create Cloud Run service placeholder (will deploy actual image in PROMPT-010)
6. Set budget alert on recruitflow-ai project: INR 1000/month, alerts at 50%, 90%, 100%

Document in Notion /Environment Variables:
- DATABASE_URL (Cloud SQL connection string format)
- GCS_BUCKET_NAME
- CLOUD_RUN_URL (once created)

Commit message: chore(infra): document GCP setup and update env example RF-9

---

### PROMPT-005
Agent: Backend Dev
JIRA: RF-10
Status: Pending
Depends on: PROMPT-001 Done (repo must exist)
Priority: High

Task:
Scaffold the FastAPI modular monolith backend.

Create the following structure under backend/:
app/
    main.py - FastAPI app, CORS middleware, router registration, lifespan events
    modules/
        auth/ - __init__.py, router.py, models.py, schemas.py, service.py
        recruiter/ - __init__.py, router.py, models.py, schemas.py, service.py
        candidate/ - __init__.py, router.py, models.py, schemas.py, service.py
        documents/ - __init__.py, router.py, models.py, schemas.py, service.py
        jobs/ - __init__.py, router.py, models.py, schemas.py, service.py
        rag/ - __init__.py, router.py, models.py, schemas.py, service.py, tools.py
        chat/ - __init__.py, router.py, schemas.py, service.py
        analytics/ - __init__.py placeholder
    shared/
        middleware.py - request logging, error handler
    core/
        config.py - Pydantic Settings loading all env vars
        database.py - SQLAlchemy async engine, session factory, Base
        storage.py - MinIO/GCS abstraction using boto3
        security.py - JWT create/validate, Argon2 hash/verify
    api/
        v1/ - api_router.py aggregating all module routers
alembic/ - alembic.ini, env.py, versions/
tests/
    conftest.py - pytest fixtures, test database setup
    test_health.py - smoke test for GET /api/v1/health
requirements.txt - all dependencies pinned
Dockerfile - python:3.13-slim, installs requirements, runs uvicorn
.env (not committed) - use .env.example as reference

Health endpoint must return: {"status": "ok", "version": "0.1.0"}
CORS must allow localhost:3000 and NEXT_PUBLIC_API_BASE_URL from env.

Run pytest tests/ - must show 1 passing test (health check smoke test).

Update Notion /API Contracts/ with: GET /api/v1/health response schema.
Commit message: feat(backend): scaffold FastAPI modular monolith RF-10

---

### PROMPT-006
Agent: Frontend Dev
JIRA: RF-11
Status: Pending
Depends on: PROMPT-001 Done (repo must exist)
Priority: High

Task:
Scaffold the Next.js 14+ frontend with App Router and full design system.

Setup:
- npx create-next-app@latest frontend --typescript --tailwind --app --eslint
- Install: @tanstack/react-query, react-hook-form, zod, lucide-react
- Install shadcn/ui and initialise with default theme
- Install prettier, vitest, @testing-library/react, @testing-library/jest-dom
- Install @sentry/nextjs (free tier DSN from env)

Create app structure:
app/
    (auth)/login/page.tsx - placeholder login page
    (dashboard)/
        layout.tsx - shell with sidebar and top bar
        doc-studio/page.tsx - placeholder
        ats/page.tsx - placeholder
        documents/page.tsx - placeholder
        talent-finder/page.tsx - placeholder
        job-finder/page.tsx - placeholder
        chat/page.tsx - placeholder

Shell layout requirements:
- Persistent left sidebar with nav links to all 6 features
- Top bar showing "RecruitFlow AI" and active client name (hardcoded placeholder for now)
- Sidebar collapses on mobile
- Uses shadcn/ui Sheet for mobile sidebar

Create:
lib/api.ts - axios instance, base URL from env, JWT interceptor (reads from memory state)
hooks/use-auth.ts - login, logout, token refresh (memory only, no localStorage)
hooks/use-stream.ts - SSE streaming hook (see frontend agent MD for implementation)

Runs cleanly on localhost:3000 via: docker compose up frontend
ESLint and Prettier must pass with zero errors.

Commit message: feat(frontend): scaffold Next.js app with shell and design system RF-11

---

### PROMPT-007
Agent: DevOps Engineer
JIRA: RF-12
Status: Pending
Depends on: PROMPT-001 Done
Priority: Medium

Task:
Populate the /agents/ folder in the repository with all agent files.

Copy the following files into /agents/ in the repository:
- conventions.md
- progress.md (current state)
- prompts.md (this file)
- code-changes.md (with template entry)
- agent-run-log.md (with template entry)
- design-system.md
- schema.md
- md/01_backend_dev_agent.md
- md/02_frontend_dev_agent.md
- md/03_qa_engineer_agent.md
- md/04_devops_engineer_agent.md
- md/05_cybersecurity_engineer_agent.md

Also create .opencode/config.json at the project root with MCP server declarations.
Tokens referenced from env vars only.

Commit message: chore(agents): add all agent files and opencode config RF-12

---

### PROMPT-008
Agent: DevOps Engineer
JIRA: RF-13
Status: Pending
Depends on: PROMPT-007 Done
Priority: Medium

Task:
Configure and test MCP integrations for agents.

GitHub MCP:
- Create Personal Access Token with scopes: repo, pull_requests, actions (read)
- Add to .env as GITHUB_MCP_TOKEN
- Add to .env.example as GITHUB_MCP_TOKEN=
- Update .opencode/config.json with GitHub MCP server entry
- Test: agent can list open PRs in the repo

JIRA MCP (Atlassian Rovo):
- Connect at https://www.atlassian.com/platform/remote-mcp-server
- Complete OAuth with Atlassian account
- Add connection URL to .opencode/config.json
- Test: agent can run JQL query: project = RF AND sprint in openSprints()

Notion MCP:
- Use existing integration token created during workspace setup
- Add to .env as NOTION_TOKEN
- Add to .opencode/config.json with Notion MCP server entry
- Test: agent can read the /RecruitFlow AI/API Contracts/ page

Document all connection steps in Notion /Local Setup Guide under "MCP Setup" section.
Commit message: chore(mcp): configure GitHub, JIRA, and Notion MCP integrations RF-13

---

### PROMPT-009
Agent: DevOps Engineer
JIRA: RF-14
Status: Pending
Depends on: nothing (can run in parallel)
Priority: Low

Task:
Verify and finalise the Notion workspace structure.

Confirm the following pages exist under "RecruitFlow AI":
- API Contracts/ (sub-pages will be added by Backend Dev per feature)
- Local Setup Guide (populated from agent MD local setup section)
- Environment Variables (all variable names from .env.example, no values)
- Security Reviews/ (empty, CyberSec will populate)

If any pages are missing, create them.
Add a "Last Updated" and "Maintained By" line at the top of each page.

No commit required. Update JIRA RF-14 comment and transition to Completed directly.

---

### PROMPT-010
Agent: CyberSecurity Engineer
JIRA: RF-15
Status: Pending
Depends on: PROMPT-001 Done (repo must exist), PROMPT-008 Done (CI pipelines exist)
Priority: Medium

Task:
Configure branch protection rules and establish the security baseline.

GitHub branch protection for main:
- Require pull request before merging
- Require 1 approval (project owner)
- Require status checks to pass: backend CI or frontend CI (whichever applies)
- Do not allow direct pushes

GitHub branch protection for staging:
- Require pull request before merging
- Require status checks to pass
- Require a comment matching "[AGENT: CyberSecurity]" and "APPROVED" before merge
- Do not allow direct pushes

Add to backend CI pipeline (backend.yml):
- pip-audit step (already in PROMPT-003, verify it is there)

Add to frontend CI pipeline (frontend.yml):
- npm audit --audit-level=high step (already in PROMPT-003, verify it is there)

Enable GitHub secret scanning on the repository settings.

Add pre-commit config file (.pre-commit-config.yaml):
- ruff hook
- black hook
- detect-secrets hook

Document the security baseline in Notion /Security Reviews/Sprint-1-Baseline.
Commit message: chore(security): configure branch protection and pre-commit hooks RF-15
