# RecruitFlow AI - Agent Conventions
# All agents must read and follow this file in full before starting any work.

---

## Project Identity

- Project name: RecruitFlow AI
- JIRA project key: RF
- Active sprint: RF-Sprint-1 (28 Jun - 5 Jul 2026)
- Repository: github.com/akshatvardhan/recruitflow-ai (update with actual URL)
- Notion workspace: RecruitFlow AI
- GCP project: recruitflow-ai-500719

---

## No Emojis Rule

Do not use emojis anywhere in this project unless explicitly requested by the project owner.
This applies without exception to:

- JIRA issue descriptions, comments, and summaries
- Notion pages and documentation
- Code comments and inline documentation
- Git commit messages and PR descriptions
- All agent files: progress.md, prompts.md, agent-run-log.md
- README files and all markdown documentation

Use plain text, dashes, and standard punctuation instead.

---

## Agent Self-Attribution

Every JIRA comment, Notion edit, and agent-run-log entry must begin with a signed header.

Format for JIRA comments:
[AGENT: Backend Dev] - RF-10 - 2026-06-30

Format for Notion edits (append to page edit log):
| 2026-06-30 | Backend Dev | Added POST /api/v1/documents/upload contract |

Format for agent-run-log.md entries:
Session ID: 20260630-BD-P004
Agent: Backend Dev

No exceptions. Every action must be traceable to a specific agent and session.

---

## Session ID Format

Every OpenCode session generates a session ID used across all outputs.

Format: YYYYMMDD-{INITIALS}-P{PROMPT_NUMBER}

Examples:
- 20260630-BD-P004  (Backend Dev, Prompt 004)
- 20260630-FD-P005  (Frontend Dev, Prompt 005)
- 20260630-QA-P004  (Quality Analyst, Prompt 004)
- 20260630-DO-P003  (DevOps Eng, Prompt 003)
- 20260630-CS-P015  (CyberSecurity Eng, Prompt 015)
- 20260702-AR-P0XX  (Architect, Prompt XXX)

This ID must appear in:
- agent-run-log.md entry header
- Git commit message footer (e.g. "Session: 20260630-BD-P004")
- JIRA comment header

---

## Git Branching Rules

Branch naming:
- feature/RF-{issue-number}-{short-description}
- bugfix/RF-{issue-number}-{short-description}
- hotfix/RF-{issue-number}-{short-description}

Examples:
- feature/RF-10-fastapi-scaffold
- bugfix/RF-34-auth-token-expiry
- hotfix/RF-41-file-upload-mime-check

Rules (non-negotiable):
- Never commit directly to main or staging
- Every feature or bugfix branch requires a PR to staging
- Staging requires a PR to main
- PR to staging requires: QA passed + JIRA completion comment with What Changed + JIRA in "In Review"
- PR to main requires: CyberSecurity sign-off comment on the staging PR

Commit message format:
type(scope): short description RF-{issue-number}

Types: feat, fix, chore, test, docs, refactor, ci

Examples:
- feat(auth): add JWT login endpoint RF-10
- fix(rag): correct chunk overlap calculation RF-22
- chore(docker): pin redis to 7.2-alpine RF-6
- test(auth): add refresh token expiry tests RF-10

Footer line on every commit:
Session: {session-id}

---

## JIRA Workflow

Project key: RF
Issue type: Task (no Story type available on free tier)

Statuses available:
- To Do
- In Progress
- In Testing
- Completed
- Blocked
- Cancelled

Story point scale (1-2 only):
- 1 point: small focused task, single endpoint, single component, config change
- 2 points: medium task, endpoint with business logic, component with multiple states
- Larger than 2 points: break into subtasks under a parent task, each subtask max 2 points

JIRA interaction rules:
- On starting work: transition story to "In Progress"
- On completing work: add signed comment with summary, transition to "In Testing"
- On blocking: transition to "Blocked", add comment naming the blocking story
- On cancellation: transition to "Cancelled", add comment with reason
- All comments must use the signed header format defined above

Blocked comment format:
[AGENT: Backend Dev] - RF-22 - 2026-06-30
Status: Blocked
Blocked by: RF-10 (FastAPI scaffold must be complete before RAG pipeline can start)
Expected unblock date: When RF-10 is in "Completed"

Cancellation comment format:
[AGENT: DevOps] - RF-14 - 2026-06-30
Status: Cancelled
Reason: Notion workspace setup was completed manually by project owner. No further action needed.

---

## Story Completion Comment Format

Every agent must post this comment when transitioning a story to "In Testing":

[AGENT: {Agent Name}] - {JIRA key} - {date}
Session: {session-id}

Summary: {one sentence description of what was done}

Files changed:
- {file path} - {what changed}
- {file path} - {what changed}

Branch: {branch name}
Commits: {commit hash} - {commit message}

Tests: {number passing} / {number total}

Handover to QA:
- {what to test}
- {how to run tests}
- {any seed data or env vars needed}

progress.md updated: yes
Notion updated: {yes / not required}

---

---

## prompts.md Reading Protocol

Every agent reads prompts.md at the start of each session.

Steps:
1. Find all prompts addressed to your agent role
2. Find prompts with status "Pending" only
3. Check "Depends on" field - do not start if dependency is not "Done"
4. Start with the lowest prompt number that is Pending and unblocked
5. Update status to "In Progress" before starting work
6. Update status to "Done" after completing and updating all required files

Do not work on prompts addressed to other agents.
Do not skip prompts without updating their status.

---

## agent-run-log.md Entry Format

Every agent appends one entry per session to agent-run-log.md.

## Session: {session-id} - {date} {time}
Agent: {Agent Name}
Prompt: {PROMPT-XXX}
JIRA story: {RF-XX}
Branch: {branch name}
Session started: {time}
Session ended: {time}
Exit status: Complete / Incomplete / Blocked

Commits made:
- {hash} - {message}

Files changed: {number}
Tests passing: {X}/{Y}

progress.md updated: yes/no
JIRA updated: yes/no
Notion updated: yes/no

Blockers encountered: {none / description}
Notes: {anything the project owner should know}

---

## QA Handover Rules

When a coding agent transitions a story to "In Testing", QA must:
1. Read the JIRA story completion comment (contains What Changed, Files Changed, Handover details)
2. Pull the feature branch (not staging)
3. Run the unit tests listed in the handover
4. Run the standard QA checklist (in .agents/roles/quality-analyst.md)
5. Post a JIRA comment with results:
   - [QA PASSED] or [QA FAILED]
   - List of test cases run and results
   - Any bugs found (create separate RF-XX bug tasks)
6. If passed: raise PR from feature branch to staging

---

## CyberSecurity Staging Review Rules

When a PR is raised to staging, CyberSecurity agent must:
1. Review the PR diff
2. Run pip-audit (backend) or npm audit (frontend)
3. Post a signed review comment on the PR:
   - [SECURITY REVIEW: APPROVED] or [SECURITY REVIEW: CHANGES REQUESTED]
   - List any findings with severity
4. Only after APPROVED comment can the PR be merged to staging

CyberSecurity review comment format (on GitHub PR):
[AGENT: CyberSecurity] - PR #{number} - {date}
Session: {session-id}

Checks performed:
- Auth bypass attempts: pass/fail
- Input validation review: pass/fail
- No secrets in code: pass/fail
- File upload safety (if applicable): pass/fail
- Dependency CVE scan: pass/fail - {findings or "none"}

Result: APPROVED / CHANGES REQUESTED

Findings:
- [HIGH] {description} - {file:line}
- [MEDIUM] {description} - {file:line}

Notion updated: /Security Reviews/{sprint}-{feature} yes/no

---

## Notion Pages (4 pages only) + docs/ADR.md

All other documentation lives in the repository.

Page 1: /RecruitFlow AI/API Contracts/
- Maintained by: Backend Dev
- One sub-page per feature module
- Updated whenever an endpoint is added or changed

Page 2: /RecruitFlow AI/Local Setup Guide
- Maintained by: DevOps Eng
- Step-by-step guide to run the full stack locally
- Updated whenever setup steps change

Page 3: /RecruitFlow AI/Environment Variables
- Maintained by: DevOps Eng
- Full list of all env vars, purpose, which service provides them
- No actual values, only names and descriptions

Page 4: /RecruitFlow AI/Security Reviews/
- Maintained by: CyberSecurity Eng

Architectural Decisions:
- docs/ADR.md - Maintained by: Architect
- One entry per significant architectural decision (new tool, provider switch, major dependency, pattern change)
- One sub-page per sprint per reviewed feature
- Updated after every staging review

---

## MCP Configuration

Config file location: .opencode/config.json (project root)
Tokens location: Doppler (never in config.json or any file, never committed)

MCP servers:
- GitHub: repo and PR read/write, CI status
- JIRA: Atlassian Rovo MCP (https://mcp.atlassian.com/v1/mcp)
- Notion: read/write scoped to RecruitFlow AI workspace

Per-agent MCP access:
- Backend Dev: JIRA (own stories), Notion (API Contracts write), GitHub (branches + commits)
- Frontend Dev: JIRA (own stories), Notion (API Contracts read), GitHub (branches + commits)
- Quality Analyst: JIRA (read all + create bugs), GitHub (read PRs + CI)
- DevOps Eng: JIRA (own stories), Notion (Setup Guide + Env Vars write), GitHub (full)
- CyberSecurity Eng: JIRA (read all + create security tasks), Notion (Security Reviews write), GitHub (PR review)
- Architect: GitHub (read only), Notion (read API Contracts)

Load only the MCP servers your role needs per session to preserve context window.

---

## Environment Variables - Doppler Only

This project has NO .env file, ever, under any circumstance. Do not search for one. Do not attempt to read one. Do not check if one exists. Do not create one. Do not suggest creating one.

All environment variables are already present in your shell environment automatically, injected by Doppler before your session starts (via `doppler run --`). Access them exactly as you would any normal environment variable -- using os.getenv() in Python, process.env in Node/TypeScript, or standard shell variable syntax. They are already there. Do not verify their existence via file system checks -- if a variable is missing, the command using it will fail naturally and that failure message is your signal, not a file search.

If you ever see a .env file in the project during any session, delete it immediately without asking, since its mere presence indicates prior drift from this convention and its contents should already be in Doppler.

---

## CI/CD Pipelines

Repository is public -- unlimited free GitHub Actions minutes.

All CI/CD runs on GitHub Actions.
- Lint and test: triggered on pull_request against staging + push to staging/main only (not every feature branch commit)
  - Path filter: backend/** (backend.yml) or frontend/** (frontend.yml)
  - Dependency caching: pip cache for backend, npm cache for frontend
- Deploy: backend-deploy.yml triggered on push to main (builds Docker image, pushes to Artifact Registry, deploys to Cloud Run)

Keep-warm: Not needed -- Cloud Run min-instances=1 prevents cold starts natively
- keepwarm.yml deleted as redundant

---

## Tracking Files - No Exceptions

Only these files exist for state tracking, ever:
- .agents/progress.md
- .agents/prompts.md
- .agents/agent-run-log.md

No agent may create a new tracking, notes, or status file under any name, for any reason. If you believe additional tracking is needed, write a note explaining why inside progress.md and wait for the project owner to decide -- never create the file yourself.

---

## Workflow Completion Boundaries

CI on push to staging/main triggers automatically as part of the branch protection setup -- this is expected pipeline behavior, not something any agent needs to manually re-trigger, re-verify, or comment on. If it passes, no action is needed. If it fails, only then does an agent investigate.

CyberSecurity review happens exactly ONCE per PR, before the PR is merged to staging. Once a PR is merged, that review is final and complete. No agent may re-open, re-run, or duplicate a CyberSecurity review on an already-merged PR unless the project owner explicitly reports a new issue found after the fact.

A merged PR is a terminal state for that story's workflow. No agent should take any further action on a story after its PR is merged to staging, beyond updating tracking files, unless a new prompt explicitly reopens it.

---

## Scope and Efficiency Discipline

Every agent must do exactly what the current prompt asks -- no more, no less. Before taking any action, check whether it has already been done by reviewing recent git log and JIRA comment history on the relevant story. Never repeat work that is already complete.

Do not proactively re-verify checks that already passed. Do not take exploratory or speculative actions beyond the literal scope of the assigned prompt. Do not add extra steps, extra validation passes, or extra reviews that were not requested, even if they seem helpful -- they cost real money in API tokens and CI minutes.

If you are unsure whether further action is needed after completing the literal task, STOP and note the question in your JIRA completion comment for the project owner to decide. Do not assume and act on that assumption.

Minimize tool calls and API round-trips. Batch file reads and edits where possible rather than making many small sequential calls. Every unnecessary tool call or LLM completion has a real dollar cost -- both GitHub Actions minutes and DeepSeek API tokens are metered.

A task is complete the moment its explicit acceptance criteria (from the JIRA story or prompt) are met. Do not continue "improving" past that point without being asked.

---

## Repository Structure

recruitflow-ai/
    frontend/
    backend/
        app/
            modules/
                auth/
                recruiter/
                candidate/
                documents/
                jobs/
                rag/
                chat/
                analytics/
            shared/
            core/
            api/
        alembic/
        tests/
        Dockerfile
        requirements.txt
    .agents/
        knowledge/
            design-system.md
            schema.md
        roles/
            backend-dev.md
            frontend-dev.md
            quality-analyst.md
            devops-eng.md
            cybersecurity-eng.md
            architect.md
        conventions.md
        progress.md
        prompts.md
        agent-run-log.md
    docs/
        ADR.md
        COMPONENTS.md
    docker/
    scripts/
    .github/
        workflows/
            backend.yml
            backend-deploy.yml
            frontend.yml
    docker-compose.yml
    .env.example
    AGENTS.md
    README.md