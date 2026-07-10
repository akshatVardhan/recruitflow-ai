#!/bin/bash
# RecruitFlow AI - sync .agents/, AGENTS.md
#
# These paths are gitignored in this repo and live instead in the private
# companion repo recruitflow-ai-agents (not secrets - just internal
# process docs kept off the public repo). Run this:
#   - once after cloning this repo fresh
#   - again after creating any new `git worktree` (worktrees only get
#     git-tracked files, so these paths won't exist there until this runs)
#   - again after any PR merges on recruitflow-ai-agents (the sync is
#     one-directional and does not run itself - an existing worktree keeps
#     reading a stale snapshot until this re-runs)
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

for path in .agents AGENTS.md; do
  rm -rf "${TARGET_DIR:?}/$path"
  cp -r "$CACHE_DIR/$path" "$TARGET_DIR/$path"
done

echo "Synced .agents/, AGENTS.md into $TARGET_DIR"
