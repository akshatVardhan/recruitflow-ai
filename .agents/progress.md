# RecruitFlow AI - Project Progress

Last updated: 2026-07-04
Updated by: DevOps Eng
Current phase: Migration - OpenCode to Claude Code
Current sprint: RF-Sprint-1 (28 Jun - 5 Jul 2026)
Overall progress: Tooling migration in progress

---

## Phase Status

Phase | Name                        | Status      | Notes
1     | Foundation and Setup        | Completed   | Sprint 1 - repo, scaffold, agents, MCP, security baseline
2     | RAG Pipeline and Ingestion  | Completed   | All 9 Phase 2 stories QA-passed
3     | Doc Studio                  | Not Started | Blocked on Phase 2
4     | ATS                         | Not Started | Blocked on Phase 1
5     | Document Management         | Not Started | Blocked on Phase 2
6     | Talent Finder               | Not Started | Blocked on Phase 1
7     | Job Finder                  | Not Started | Blocked on Phase 1
8     | AI Chat Interface           | Not Started | Blocked on Phase 2
9     | Polish and Production       | Not Started | Final phase
M     | Tooling Migration           | In Progress | OpenCode -> Claude Code (Jul 4)

---

## Phase 1 - Current Sprint Detail

### Completed
RF-6  - [DevOps] Initialize GitHub repository with project structure
RF-7  - [DevOps] Set up Docker Compose for local development stack
RF-8  - [DevOps] Configure GitHub Actions CI pipeline
RF-9  - [DevOps] Set up GCP project and production infrastructure
RF-10 - [Backend] Initialize FastAPI modular monolith project
RF-11 - [Frontend] Initialize Next.js project with Tailwind and shadcn/ui
RF-12 - [DevOps] Create /agents folder with all agent files and templates
RF-13 - [DevOps] Configure MCP integrations (GitHub + JIRA + Notion)
RF-14 - [DevOps] Set up Notion workspace structure
RF-15 - [CyberSec] Configure branch protection and security baseline
-     - [DevOps] Migrate from OpenCode to Claude Code tooling (Jul 4)

### In Progress
(none yet)

### Pending
(none)

### Blocked
(none)

---

## Phase 2 - Current Sprint Detail

### Completed
RF-34 - [Backend] Document upload endpoint with database model and file storage (QA PASSED)
RF-20 - [Backend] Set up Qdrant collections for RAG (QA PASSED)
RF-21 - [Backend] Document text extraction pipeline (QA PASSED)
RF-22 - [Backend] Auto-tagging via DeepSeek V4-Flash (QA PASSED)
RF-23 - [Backend] Chunking strategy implementation (QA PASSED)
RF-24 - [Backend] Embedding pipeline with Sentence Transformers (QA PASSED)
RF-25 - [Backend] Celery async ingestion job (QA PASSED)
RF-26 - [Backend] Hybrid retrieval implementation (QA PASSED)
RF-27 - [Backend] RAG agent tools (LlamaIndex) (QA PASSED)

### In Progress
(none - all backend Phase 2 stories complete)

### Pending
(none - Phase 2 100% done)

### Blocked
(none)

---

## Security Audits

### Pre-Publication Git History Secret Scan (2026-07-03)

Result: **CLEAN** - no secrets found in git history across 168 commits.

Performed by DevOps Engineer (Session: 20260703-DO-P011):

- **gitleaks 8.30.1**: scanned 168 commits, 1.10 MB -- no leaks found
- **trufflehog 2.2.1**: scanned all commits -- false positives only (standard example/placeholder values like `user:password@localhost`, `change-me-in-production`, `minioadmin`)
- **Manual verification**: confirmed .env was NEVER committed; no GCP service account JSON key in any commit; no API token values leaked; no hardcoded production database passwords

Repository is safe to make public from a secret-leak perspective. No git history rewriting needed.

---

## Operational Maintenance (no JIRA story)

### CI/CD Cost Reduction + Cloud Build Revert (2026-07-03)

Completed by DevOps Engineer (Session: 20260703-DO-P010 and 20260703-DO-P012):

#### Phase 1 - Cost Reduction (kept permanently)
- **PR #20 closed** without merging -- its pull_request trigger approach superseded by properly scoped triggers
- **keepwarm.yml deleted** -- redundant because Cloud Run min-instances=1 prevents cold starts natively
- **backend.yml triggers scoped**: pull_request against staging + push to staging/main only (not every feature branch commit); pip caching added
- **frontend.yml triggers scoped**: same pattern; npm caching added

#### Phase 2 - Cloud Build Revert (repo made public, no longer needed)
- **cloudbuild.yaml deleted** -- was created during earlier migration, now reverted
- **backend-deploy.yml restored** from staging -- GitHub Actions -> Cloud Run deploy workflow
- All deploy back on GitHub Actions (unlimited free minutes on public repo)
- Updated conventions.md and devops_engineer_agent.md to reflect all-GitHub-Actions CI/CD

Branch: fix/ci-cost-reduction (not yet PR'd to staging)

---

## Agent Last Known State

Agent              | Last Prompt | Status      | Branch
Backend Dev         | PROMPT-019  | Complete    | feature/RF-23-chunking (latest fix)
Frontend Dev        | PROMPT-006  | Pending     | feature/RF-11-nextjs-scaffold
Quality Analyst     | PROMPT-008  | Complete    | (all 9 QA reviews done)
DevOps Eng          | PROMPT-009  | Complete    | fix/ci-cost-reduction
CyberSecurity Eng   | PROMPT-010  | Complete    | feature/RF-15-security-baseline (merged)
Architect           | (not yet run) | Ready    | (no branch)

---

## Staging Branch State

Last merged to staging: Claude Code migration (7f8e0cc) + prompts update (e014ed9)
No pending PRs. All Phase 2 stories have been merged.
Last security review: 2026-06-28 - CyberSecurity APPROVED on PRs #1 and #2

---

## Main Branch State

Last merged to main: initial scaffold (pending)
Production deploy status: not deployed yet

---

## Open Issues

ID | Type     | Severity | Agent         | Status
-- | -------- | -------- | ------------- | ------
RF-34 | Bug | Medium | Backend Dev | Fixed (doc_type enum, orphan cleanup, tests added)
RF-21 | Bug | Medium | Backend Dev | Fixed (corrupt file handling, hardcoded bucket)
RF-23 | Bug | Low | Backend Dev | Fixed (section fallback to paragraph chunking)

---

## Tooling Migration - OpenCode to Claude Code (2026-07-04)

### What Changed
- Deleted .opencode/ directory (was gitignored, force-tracked conventions.md removed)
- Created .agents/ directory replacing .opencode/manual/ with updated role files
- Created .claude/agents/ directory with 6 Claude Code subagent definitions
- Updated all role files with new agent names (Backend Dev, Frontend Dev, Quality Analyst, DevOps Eng, CyberSecurity Eng)
- Added new Architect role (.agents/roles/architect.md) to own docs/ADR.md
- Updated AGENTS.md to reference .agents/ paths instead of .opencode/manual/
- Removed all code-changes.md references from conventions, roles, AGENTS.md
- Updated .gitignore to stop ignoring .agents/ (now tracked)
- Updated docs/ADR.md maintainer from Backend Developer -> Architect
- Updated conventions.md with all role renames, path updates, and Architect sections

### Remaining
- Update JIRA sprint name (RF-Sprint-1 outdated - needs Planner to action)
- Frontend prompts (RF-28, RF-29) added to prompts.md (done)