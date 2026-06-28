# RecruitFlow AI - Code Changes Log

# Purpose
# This file is appended by every coding agent after completing a prompt.
# QA reads the relevant entry before testing a story.
# Planner reads recent entries to assess progress.
# Keep entries concise. No emojis.

# Format: append new entries at the top (newest first)

---

## [CHANGE-010] 2026-06-28
Agent: CyberSecurity Engineer
Session: 20260628-CS-P010
Prompt ref: PROMPT-010
JIRA story: RF-15
Branch: feature/RF-15-security-baseline

### Files Modified
- .pre-commit-config.yaml - created, with ruff, black, detect-secrets hooks
- scripts/github-security-setup.sh - created, branch protection and secret scanning script

### What Changed
Created pre-commit configuration with ruff (linting), black (formatting), and detect-secrets hooks. Created GitHub security setup script for configuring branch protection (main: require PR + 1 approval, staging: require PR + security review) and enabling secret scanning. Verified CI pipelines already include pip-audit (backend) and npm audit --audit-level=high (frontend). Documented security baseline in Notion /Security Reviews/Sprint-1-Baseline.

### Test Coverage
N/A - configuration only

### Handover to QA
Run pre-commit install to activate hooks locally.
Branch protection requires gh CLI with admin token: bash scripts/github-security-setup.sh

### Notes
GitHub PAT in .env (GITHUB_MCP_TOKEN) did not have admin API access for branch protection. Manual execution of setup script with admin token is required.

---

## [CHANGE-009] 2026-06-28
Agent: Frontend Dev
Session: 20260628-FD-P006
Prompt ref: PROMPT-006
JIRA story: RF-11
Branch: feature/RF-11-nextjs-scaffold

### Files Modified
- frontend/ - created full Next.js scaffold (28 files)

### What Changed
Scaffolded Next.js 14+ App Router project with TypeScript, Tailwind, ESLint. Created dashboard shell layout with persistent left sidebar (6 nav items) and top bar with active client placeholder. Sidebar collapses on mobile using Sheet pattern. Created placeholder pages for all 6 features: doc-studio, ats, documents, talent-finder, job-finder, chat. Implemented lib/api.ts with axios instance and JWT interceptor, hooks/use-auth.ts (memory-only auth), hooks/use-stream.ts (SSE streaming).

### Test Coverage
N/A - scaffold only, no tests yet

### Handover to QA
Run: cd frontend && npm install && npm run dev (requires Node 20).
Verify shell layout renders at localhost:3000 with sidebar and top bar.

### Notes
npm install timed out in agent session due to network. Run manually before dev.

---

## [CHANGE-008] 2026-06-28
Agent: Backend Dev
Session: 20260628-BD-P005
Prompt ref: PROMPT-005
JIRA story: RF-10
Branch: feature/RF-10-fastapi-scaffold

### Files Modified
- backend/ - created full FastAPI scaffold (57 files)

### What Changed
Scaffolded FastAPI modular monolith with health endpoint (GET /api/v1/health), CORS middleware allowing localhost:3000, all module stubs (auth, recruiter, candidate, documents, jobs, rag, chat, analytics), core infrastructure (config, database, security, storage), shared middleware (request logging, error handler), API router aggregating all modules, pytest setup with conftest.py and health check test, Alembic configuration, Dockerfile, and requirements.txt.

### Test Coverage
- tests/test_health.py - 1 test (requires database to run)
- All Python files pass syntax validation

### Handover to QA
Test health endpoint: docker compose up -d then curl http://localhost:8000/api/v1/health
Or run: pip install -r backend/requirements.txt && pytest tests/ -v

### Notes
Health endpoint returns {"status": "ok", "version": "0.1.0"}.

---

## [CHANGE-007] 2026-06-28
Agent: DevOps Engineer
Session: 20260628-DO-P009
Prompt ref: PROMPT-009
JIRA story: RF-14
Branch: N/A (no code changes)

### Files Modified
- None - Notion-only changes

### What Changed
Verified and finalized Notion workspace structure. Confirmed all 4 pages exist under RecruitFlow AI: API Contracts, Local Setup Guide, Environment Variables, Security Reviews. Added "Last Updated" and "Maintained By" headers to each page. Local Setup Guide and Environment Variables populated with content.

### Test Coverage
N/A

### Handover to QA
Verify Notion workspace /RecruitFlow AI/ has 4 sub-pages with headers.

### Notes
No git commit required per PROMPT-009.

---

## [CHANGE-006] 2026-06-28
Agent: DevOps Engineer
Session: 20260628-DO-P008
Prompt ref: PROMPT-008
JIRA story: RF-13
Branch: feature/RF-13-mcp-integrations

### Files Modified
- .opencode/config.json - already configured with GitHub, JIRA, Notion MCP servers
- Notion /Local Setup Guide - added MCP Setup section

### What Changed
Verified MCP integration configuration: GitHub (PAT-based with repo/PR/actions scopes), JIRA (Atlassian Rovo OAuth), Notion (integration token). All servers declared in .opencode/config.json with tokens from .env. Added MCP Setup documentation section to Notion Local Setup Guide with connection steps for each provider.

### Test Coverage
N/A - configuration documentation

### Handover to QA
Verify .opencode/config.json has all 3 MCP server entries.
Verify tokens exist in .env: GITHUB_MCP_TOKEN, NOTION_TOKEN, JIRA_API_TOKEN.

### Notes
MCP setup was already in place from initial bootstrap. No code changes needed.

---

## [CHANGE-005] 2026-06-28
Agent: DevOps Engineer
Session: 20260628-DO-P007
Prompt ref: PROMPT-007
JIRA story: RF-12
Branch: feature/RF-12-agent-files

### Files Modified
- agents/ - created with all 12 agent files (conventions, progress, prompts, code-changes, agent-run-log, design-system, schema, 5 agent MD files)

### What Changed
Created /agents/ directory in the repository with all agent configuration files copied from /.agents/. Includes conventions, progress tracker, prompts, code change log, run log, design system spec, database schema, and all 5 agent role definitions.

### Test Coverage
N/A - file population only

### Handover to QA
Verify agents/ directory exists with all expected files: 12 files total.

### Notes
.opencode/config.json was already present from initial bootstrap commit.

---

## [CHANGE-004] 2026-06-28
Agent: DevOps Engineer
Session: 20260628-DO-P004
Prompt ref: PROMPT-004
JIRA story: RF-9
Branch: feature/RF-9-gcp-setup

### Files Modified
- scripts/gcp-setup.sh - created, full GCP provisioning script with gcloud commands

### What Changed
Created GCP setup script with step-by-step gcloud commands for provisioning production infrastructure: project creation, API enablement (Cloud Run, Cloud SQL, Cloud Storage, Secret Manager), PostgreSQL 15 instance (db-f1-micro, asia-south1), Cloud Storage bucket, Cloud Run placeholder, and budget alert. Updated Notion /Environment Variables with all variable descriptions.

### Test Coverage
N/A - infrastructure documentation only

### Handover to QA
Script requires gcloud CLI and GCP billing account. Run manually: bash scripts/gcp-setup.sh

### Notes
GCP project recruitflow-ai assumed not yet created. The script is idempotent for most steps.

---

## [CHANGE-003] 2026-06-28
Agent: DevOps Engineer
Session: 20260628-DO-P003
Prompt ref: PROMPT-003
JIRA story: RF-8
Branch: feature/RF-8-ci-pipelines

### Files Modified
- .github/workflows/backend.yml - created, Python CI with ruff, black, mypy, pip-audit, pytest
- .github/workflows/frontend.yml - created, Node CI with eslint, prettier, npm audit, vitest, next build
- .github/workflows/keepwarm.yml - created, scheduled ping every 10 minutes

### What Changed
Created 3 GitHub Actions CI workflow files. Backend pipeline triggers on feature/* and bugfix/* branches with backend/ path changes, runs linting (ruff, black, mypy), dependency audit (pip-audit), and tests (pytest). Frontend pipeline uses same trigger with frontend/ path changes, runs eslint, prettier check, npm audit, vitest, and next build. Keep-warm workflow runs every 10 minutes to prevent Cloud Run cold starts.

### Test Coverage
N/A - CI pipeline configuration only

### Handover to QA
Verify workflows run on next push to a feature branch with backend/ or frontend/ changes.
Required GitHub secrets (must be set in repo settings): DATABASE_URL, CLOUD_RUN_URL, GCS_CREDENTIALS_JSON, LITELLM_API_KEY

### Notes
pip-audit (backend) and npm audit --audit-level=high (frontend) included as per CyberSecurity requirements (PROMPT-010). Keep-warm requires CLOUD_RUN_URL secret to be set.

---

## [CHANGE-002] 2026-06-28
Agent: DevOps Engineer
Session: 20260628-DO-P002
Prompt ref: PROMPT-002
JIRA story: RF-7
Branch: feature/RF-7-docker-compose

### Files Modified
- docker-compose.yml - created, full local dev stack with 7 services
- .agents/md/04_devops_engineer_agent.md - updated Local Setup Guide with exact commands
- Notion /Local Setup Guide - created and populated with setup steps
- Notion /API Contracts, /Environment Variables, /Security Reviews - created as placeholder pages

### What Changed
Created docker-compose.yml with all 7 services: PostgreSQL 15, Redis 7, Qdrant v1.9.0, MinIO, FastAPI backend, Next.js frontend, and Celery worker. All services have health checks, persistent volumes, and restart policies. Backend depends on all infrastructure services being healthy. Updated DevOps Engineer agent MD with exact local setup commands.

### Test Coverage
N/A - infrastructure only

### Handover to QA
Test the compose file starts correctly: docker compose up -d
Verify all services become healthy: docker compose ps
Verify backend is reachable: curl http://localhost:8000/api/v1/health

### Notes
Notion pages created under RecruitFlow AI parent page. Environment Variables page still needs content population.

---

## [CHANGE-001] 2026-06-28
Agent: DevOps Engineer
Session: 20260628-DO-P001
Prompt ref: PROMPT-001
JIRA story: RF-6
Branch: feature/RF-6-repo-structure

### Files Modified
- README.md - created, project overview and tech stack
- docker-compose.yml - created, placeholder for PROMPT-002
- .github/workflows/.gitkeep - placeholder for CI workflows
- agents/ - created, copied all agent files from .agents/
- frontend/.gitkeep - placeholder for Next.js app
- backend/.gitkeep - placeholder for FastAPI app
- docker/.gitkeep - placeholder for Docker files
- scripts/.gitkeep - placeholder for utility scripts

### What Changed
Created the full project directory structure for RecruitFlow AI. Added README.md with project name, tech stack summary, and setup instructions placeholder. Created docker-compose.yml placeholder. Added .gitkeep files to all empty directories to ensure git tracks them. Copied all agent files from .agents/ into agents/ for repository visibility.

### Test Coverage
N/A - repository structure setup only

### Handover to QA
No QA needed for repo structure. Next DevOps prompt (PROMPT-002) will populate docker-compose.yml.

### Notes
.python-version file exists locally but was intentionally excluded from commit. It may be added to .gitignore or committed in a future prompt.

---

## [CHANGE-000] TEMPLATE ENTRY - DO NOT DELETE

Agent: [Agent Name]
Session: YYYYMMDD-XX-P000
Prompt ref: PROMPT-000
JIRA story: RF-0
Branch: feature/RF-0-example

### Files Modified
- backend/app/modules/auth/router.py - created, JWT login and refresh endpoints
- backend/app/core/security.py - created, JWT and Argon2 utilities
- backend/alembic/versions/001_users_table.py - created, users table migration
- tests/test_auth.py - created, 8 unit tests for auth endpoints

### What Changed
Implemented JWT authentication with Argon2 password hashing. Login endpoint
returns access and refresh tokens. Refresh endpoint validates refresh token
and returns new access token. All tokens are memory-only on the frontend.

### Test Coverage
- tests/test_auth.py - 8 tests, all passing

### Handover to QA
Test focus: POST /api/v1/auth/login with valid and invalid credentials.
Run: cd backend && pytest tests/test_auth.py -v
Seed data: python scripts/seed_dev.py (creates test user admin@test.com / password: testpass123)
Env vars needed: JWT_SECRET_KEY, JWT_ALGORITHM, DATABASE_URL

### Notes
Argon2 hashing is intentionally slow on first request after cold start.
Not a bug. See core/security.py comments for tuning parameters.
