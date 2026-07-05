# RecruitFlow AI - Agent Prompts

Retired 2026-07-06. This file was an async task queue: agents would read it
at session start and autonomously pull pending work addressed to their
role. In practice, task specs have been handed to agents synchronously
(written and given directly for the session at hand) rather than
discovered from a file, so the capability this queue provided was not
being exercised - see conventions.md for the current process.

All entries that were still live in this file at retirement (including the
3 genuinely still-pending specs for RF-29/30/31) are preserved in
.agents/archive/prompts-archive.md for reference. JIRA remains the source
of truth for those tickets' actual status.
