# RecruitFlow AI - Agent Bootstrap

## How This Works

You are an AI agent working on RecruitFlow AI. At the start of every session,
read the files listed below from the project directory before doing anything
else. These files are your complete operating context. Do not rely on
conversation history or assumptions from previous sessions.

---

## Step 1 - Read These Files (in this order, every session)

1. Read: .opencode/agents/conventions.md
   Defines your working rules, git conventions, JIRA workflow, story point
   scale, no-emoji rule, and session ID format.
   Non-negotiable for every agent.

2. Read: .opencode/agents/progress.md
   Tells you the current project phase, sprint, what is done, what is in
   progress, what is pending, and the last known state of every agent.
   This is your context reset anchor.

3. Read: .opencode/agents/prompts.md
   Contains all tasks for all agents across all phases. Find prompts addressed
   to your role with status Pending and no unresolved dependencies.
   That is your work queue.

4. Read your agent MD file based on your role:

   Backend Dev:      .opencode/agents/md/01_backend_dev_agent.md
                     also read: .opencode/agents/schema.md

   Frontend Dev:     .opencode/agents/md/02_frontend_dev_agent.md
                     also read: .opencode/agents/design-system.md

   QA Engineer:      .opencode/agents/md/03_qa_engineer_agent.md

   DevOps Engineer:  .opencode/agents/md/04_devops_engineer_agent.md

   CyberSecurity:    .opencode/agents/md/05_cybersecurity_engineer_agent.md

5. Read: .opencode/agents/code-changes.md (last 3 entries only)
   Gives you context on what was recently built so you do not duplicate work
   or break dependencies.

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
- Update .opencode/agents/progress.md (your agent row and completed item)
- Update .opencode/agents/code-changes.md (new entry for this session)
- Update .opencode/agents/agent-run-log.md (new session entry)
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
