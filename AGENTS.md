# RecruitFlow AI - Agent Bootstrap

## How This Works

You are an AI agent working on RecruitFlow AI. At the start of every session,
read the files listed below from the project directory before doing anything
else. These files are your complete operating context. Do not rely on
conversation history or assumptions from previous sessions.

---

## Step 1 - Read These Files (in this order, every session)

1. Read: .agents/conventions.md
   Defines your working rules, git conventions, JIRA workflow, story point
   scale, no-emoji rule, and session ID format.
   Non-negotiable for every agent.

2. Read: .agents/progress.md
   Tells you the current project phase, sprint, what is done, what is in
   progress, what is pending, and the last known state of every agent.
   This is your context reset anchor.

3. Read: .agents/prompts.md
   Contains all tasks for all agents across all phases. Find prompts addressed
   to your role with status Pending and no unresolved dependencies.
   That is your work queue.

4. Read your agent role file based on your role:

   Backend Dev:      .agents/roles/backend-dev.md
                     also read: .agents/knowledge/schema.md

   Frontend Dev:     .agents/roles/frontend-dev.md
                     also read: .agents/knowledge/design-system.md

   Quality Analyst:  .agents/roles/quality-analyst.md

   DevOps Eng:       .agents/roles/devops-eng.md

   CyberSecurity Eng: .agents/roles/cybersecurity-eng.md

   Architect:        .agents/roles/architect.md
                     also read: .agents/knowledge/schema.md

5. Read: .agents/agent-run-log.md (last 3 entries only)
   Gives you context on what was recently built so you do not duplicate work
   or break dependencies.

**Before doing anything, also read the "Tracking Files - No Exceptions", "Workflow Completion Boundaries", and "Scope and Efficiency Discipline" sections of conventions.md. These govern when to stop, what not to repeat, and what files you may create. Violating these wastes real money.**

---

## Step 1.5 - Verify Your Identity (Mandatory)

After reading all files but before outputting your confirmation block, perform this identity check:

```
Your system-assigned role (from the "Agent:" header in this file at session
start) must match the role file you just read in Step 4. For example, if
the system says "Agent: Backend Dev" you must have read backend-dev.md,
not devops-eng.md or any other role file.

If the role in the "Agent:" header does not match the file you read:
  STOP. Say: "System assigned me as [X] but I read the role file for [Y].
  I will read .agents/roles/[X].md now." Then read the correct file.
  Do not proceed until the files match.
```

This prevents the identity confusion that occurs when an agent reads the wrong role file. Every session starts with one correct identity.

---

## Step 2 - Confirm Before Acting

After reading all files, output exactly this block before starting any work:

Agent: [your role]
Session ID: [YYYYMMDD-XX-PXXX]
Sprint: [sprint name]
Phase: [phase number and name]
My next task: [PROMPT-XXX - one sentence description]
Depends on: [done / not applicable]
Branch I will create: [feature/RF-XX-description]

Do not skip this confirmation. Do not start working before outputting it.
If your next prompt has an unresolved dependency, state what is blocking
you and stop.

---

## Step 3 - Execute

Execute your pending prompt exactly as written in prompts.md.
Follow all rules in conventions.md without exception.

After completing the task:
- Update .agents/progress.md (your agent row and completed item)
- Update .agents/agent-run-log.md (new session entry)
- Update JIRA via MCP (transition story, add completion comment)

---

## Always Active Rules

- No emojis anywhere in any output, comment, commit, or documentation
- No direct commits to main or staging branches ever
- Every commit message: type(scope): description RF-XX
- Session ID appears in every commit footer, JIRA comment, and log entry
- Story points: 1 for small tasks, 2 for medium tasks, subtasks for anything larger
- If blocked: update JIRA to Blocked, note the blocking story, update progress.md, stop
- If a prompt is unclear: add a JIRA comment asking for clarification, stop
- If you discover something that affects another agent: note it in progress.md
- No .env file exists or should ever exist in this project. Never search for, read, or create one. All secrets come from Doppler-injected environment variables already present in your shell session.
