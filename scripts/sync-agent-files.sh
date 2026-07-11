#!/bin/bash
# RecruitFlow AI - sync .agents/, CLAUDE.md, .claude/skills
#
# These paths are gitignored in this repo and live instead in the private
# companion repo recruitflow-ai-agents (not secrets - just internal
# process docs kept off the public repo). Run this:
#   - once after cloning this repo fresh
#   - again after creating any new `git worktree` (worktrees only get
#     git-tracked files, so these paths won't exist there until this runs)
#   - again after any PR merges on recruitflow-ai-agents (the sync is
#     one-directional and does not run itself - an existing worktree keeps
#     reading a stale snapshot until this re-runs; CLAUDE.md's bootstrap
#     also runs a soft freshness check for this at session start)
#
# Requires: gh CLI authenticated with access to akshatVardhan/recruitflow-ai-agents

set -euo pipefail

COMPANION_REPO="akshatVardhan/recruitflow-ai-agents"
CACHE_DIR="${RECRUITFLOW_AGENTS_CACHE:-$HOME/.cache/recruitflow-ai-agents}"
TARGET_DIR="$(git rev-parse --show-toplevel)"

if [ -d "$CACHE_DIR/.git" ]; then
  git -C "$CACHE_DIR" pull --quiet origin main
else
  mkdir -p "$(dirname "$CACHE_DIR")"
  gh repo clone "$COMPANION_REPO" "$CACHE_DIR" -- --quiet
fi

# Existence-tolerant: a path that stops existing on the companion side is
# skipped, not a fatal error. Without this, adding/removing a synced path
# there (as this exact commit does, twice) breaks every worktree's sync
# until this script itself catches up - same failure class as the
# .opencode sync break this project already hit twice.
for path in .agents CLAUDE.md .claude/skills; do
  [ -e "$CACHE_DIR/$path" ] || continue
  rm -rf "${TARGET_DIR:?}/$path"
  mkdir -p "$(dirname "$TARGET_DIR/$path")"
  cp -r "$CACHE_DIR/$path" "$TARGET_DIR/$path"
done

# Stale AGENTS.md cleanup: AGENTS.md was gitignored (never git-tracked), so
# every worktree synced before 2026-07-11 has a physical copy on disk that
# the loop above (which no longer lists AGENTS.md) would otherwise never
# touch again - two conflicting bootstrap docs sitting side by side
# forever. Runs every time, so it also catches worktrees created later from
# a stale base.
rm -f "${TARGET_DIR:?}/AGENTS.md"

# Freshness marker, read by CLAUDE.md's bootstrap staleness check.
git -C "$CACHE_DIR" rev-parse HEAD > "$TARGET_DIR/.agents/.synced-commit"

echo "Synced .agents/, CLAUDE.md, .claude/skills/ into $TARGET_DIR"
