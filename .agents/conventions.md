# RecruitFlow AI - Agent Conventions
# All agents must read and follow this file in full before starting any work.

---

## Project Identity

- Project name: RecruitFlow AI
- JIRA project key: RF
- Active sprint: RF-Sprint-2 (2 Jul - 16 Jul 2026)
- Repository: github.com/akshatvardhan/recruitflow-ai (update with actual URL)
- GCP project: recruitflow-ai-500719

---

## Role Identity Verification

Before starting any work, every agent must verify that their system-assigned role matches the role file they read.

The check is defined in AGENTS.md Step 1.5 -- read it and execute it before outputting your confirmation block. If you read the wrong role file, you will operate under a false identity for the entire session, causing confusion and out-of-scope work.

If a mismatch is detected, stop, read the correct role file, and only then proceed.

---

## No Emojis Rule

Do not use emojis anywhere in this project unless explicitly requested by the project owner.
This applies without exception to:

- JIRA issue descriptions, comments, and summaries
- Code comments and inline documentation
- Git commit messages and PR descriptions
- All agent files: progress.md, prompts.md, agent-run-log.md
- README files and all markdown documentation

Use plain text, dashes, and standard punctuation instead.

---

## Agent Self-Attribution

Every JIRA comment and agent-run-log entry must begin with a signed header.

Format for JIRA comments:
[AGENT: Backend Dev] - RF-10 - 2026-06-30

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
- PR to main requires: CyberSecurity sign-off comment on the staging PR, OR --
  for solo-operator merges where no independent reviewer is available -- an
  explicit owner-approved exception noted in the PR description. This
  mirrors the existing `required_pull_request_reviews: null` exception
  already applied to branch protection for the same root cause (single-
  account repo, GitHub blocks self-approval; see the "Manual Override"
  commit that removed the required-approving-review-count gate). This does
  not waive required CI status checks (backend-ci/frontend-ci/security
  still must pass), and does not waive the underlying security review work
  when a reviewer is practically available -- it only removes the blocking
  gate when one genuinely isn't.

Branch push rule (non-negotiable):
- A branch is not complete when it is committed locally. It is complete only when it has been pushed to origin (git push -u origin <branch-name>).
- Every feature/, bugfix/, and hotfix/ branch MUST be pushed to GitHub before the session is considered done -- a local-only branch is invisible to QA, CyberSecurity, and the project owner, and blocks the entire downstream review pipeline.
- QA (not the coding agent) is responsible for raising the PR to staging once QA passes. The coding agent only pushes the branch; it does not open the PR unless explicitly instructed by the project owner.
- Verify the push succeeded (git status shows "Your branch is up to date with 'origin/...'") before writing "Branch pushed: yes" in any tracking file or JIRA comment.
- If the push fails (auth, network, protected-branch rejection), the session is Blocked, not Complete -- record the failure in progress.md and agent-run-log.md and stop.

Worktree isolation rule (non-negotiable):
- This repo's main working directory may be shared across multiple concurrent agent sessions. Never `git checkout`/switch branches directly in that shared root -- another session's in-progress, uncommitted work can be silently disturbed, and a session can find itself running against the wrong branch entirely (this has happened: a session once operated against `main` believing it was on `staging`, because the shared directory had been switched underneath it).
- Before starting work on any branch, create an isolated worktree instead: `git worktree add <path> -b <branch-name> origin/staging` (or without `-b` to check out an existing branch). Do all edits, commits, and pushes inside that worktree, not the shared root.
- Remove the worktree (`git worktree remove <path>`) once the branch is pushed and you're done with it, to avoid accumulating stale worktrees. Leaving one in place while a PR is still open and might need follow-up commits is fine.
- Read-only investigation (git log, diff, grep across a branch) does not require a worktree -- only checkouts and edits do.

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
- Backlog
- In Progress
- In Testing
- In Review
- Done
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
Expected unblock date: When RF-10 is in "Done"

Cancellation comment format:
[AGENT: DevOps] - RF-14 - 2026-06-30
Status: Cancelled
Reason: Manual completion by project owner outside the agent workflow. No further action needed.

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

Blockers encountered: {none / description}
Notes: {anything the project owner should know}

Use the full format above for coding sessions with commits. For low-stakes or process-only sessions, role files may instead call for a run-log entry (short format):

## Session: {session-id} - {date} {time}
Agent: {Agent Name}
JIRA story: {RF-XX / none}
Branch: {branch name / none}
Outcome: {one-line summary of what was done and its result}

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

CyberSecurity review process: see .agents/roles/cybersecurity-eng.md (Evidence Rule, Scope Rule, Severity Actions, Review Process).

---

## Architectural Decisions (docs/ADR.md)

All documentation lives in the repository.

- docs/ADR.md - Maintained by: Architect
- One entry per significant architectural decision (new tool, provider switch, major dependency, pattern change)
- Updated after every staging review

---

## MCP Configuration

Config file location: .opencode/config.json (project root)
Tokens location: Doppler (never in config.json or any file, never committed)

MCP servers:
- GitHub: repo and PR read/write, CI status
- JIRA: Atlassian Rovo MCP (https://mcp.atlassian.com/v1/mcp)

Per-agent MCP access:
- Backend Dev: JIRA (own stories), GitHub (branches + commits)
- Frontend Dev: JIRA (own stories), GitHub (branches + commits)
- Quality Analyst: JIRA (read all + create bugs), GitHub (read PRs + CI)
- DevOps Eng: JIRA (own stories), GitHub (full)
- CyberSecurity Eng: JIRA (read all + create security tasks), GitHub (PR review)
- Architect: GitHub (read only)

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

Additionally, these three read-only historical archive files are permitted -- they hold relocated (not summarized) content from the files above and must never be read during normal sessions:
- .agents/archive/prompts-archive.md
- .agents/archive/progress-archive.md
- .agents/archive/agent-run-log-archive.md

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

Minimize tool calls and API round-trips. Batch file reads and edits where possible rather than making many small sequential calls. Every unnecessary tool call or LLM completion has a real dollar cost -- both GitHub Actions minutes and LLM API tokens are metered.

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
        archive/
            prompts-archive.md
            progress-archive.md
            agent-run-log-archive.md
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
    .env.example
    AGENTS.md
    README.md