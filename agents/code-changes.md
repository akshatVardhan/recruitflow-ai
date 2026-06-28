# RecruitFlow AI - Code Changes Log

# Purpose
# This file is appended by every coding agent after completing a prompt.
# QA reads the relevant entry before testing a story.
# Planner reads recent entries to assess progress.
# Keep entries concise. No emojis.

# Format: append new entries at the top (newest first)

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
