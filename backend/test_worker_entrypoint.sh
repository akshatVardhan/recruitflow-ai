#!/bin/bash
# ponytail self-check: worker-entrypoint.sh's safety property is that
# `wait -n` on two background jobs returns as soon as EITHER exits, with
# that job's status - so a crashed celery worker doesn't hide behind a
# still-healthy http.server. This simulates that shape without needing a
# real celery/redis, and fails loudly if the semantics ever regress.
set -e

sleep 100 &
LONG_RUNNING=$!
(sleep 0.2; exit 7) &
SHORT_LIVED=$!

START=$(date +%s)
set +e
wait -n "$LONG_RUNNING" "$SHORT_LIVED"
STATUS=$?
set -e
END=$(date +%s)

kill "$LONG_RUNNING" 2>/dev/null || true
wait "$LONG_RUNNING" 2>/dev/null || true

ELAPSED=$((END - START))
if [ "$ELAPSED" -gt 3 ]; then
  echo "FAIL: wait -n took ${ELAPSED}s, expected it to return promptly when one job exited"
  exit 1
fi
if [ "$STATUS" -eq 0 ]; then
  echo "FAIL: expected a non-zero exit status from the job that failed, got 0"
  exit 1
fi

echo "PASS: wait -n returned in ${ELAPSED}s with status $STATUS when one process died"
