# RecruitFlow AI - Code Changes Log

# Purpose
# This file is appended by every coding agent after completing a prompt.
# QA reads the relevant entry before testing a story.
# Planner reads recent entries to assess progress.
# Keep entries concise. No emojis.

# Format: append new entries at the top (newest first)

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
