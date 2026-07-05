#!/bin/bash
# RecruitFlow AI - sync .agents/, .opencode/, opencode.json, AGENTS.md
#
# These paths are gitignored in this repo and live instead in the private
# companion repo recruitflow-ai-agents (not secrets - just internal
# process docs kept off the public repo). Run this:
#   - once after cloning this repo fresh
#   - again after creating any new `git worktree` (worktrees only get
#     git-tracked files, so these paths won't exist there until this runs)
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

for path in .agents .opencode opencode.json AGENTS.md; do
  rm -rf "${TARGET_DIR:?}/$path"
  cp -r "$CACHE_DIR/$path" "$TARGET_DIR/$path"
done

echo "Synced .agents/, .opencode/, opencode.json, AGENTS.md into $TARGET_DIR"
