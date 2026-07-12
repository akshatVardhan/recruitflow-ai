#!/bin/bash
# Cloud Run services require a $PORT listener for health checks, but a
# Celery worker doesn't serve HTTP on its own. Run both as background jobs
# and exit (non-zero) the moment either one dies, so Cloud Run sees the
# container as unhealthy and restarts it instead of a wedged worker
# quietly failing behind a health check that only proves the HTTP server
# is still up.
# RF-55: the health listener (app/worker_health.py) calls
# celery_app.control.ping() on every request, so a hung-but-alive worker
# (stuck broker reconnect, deadlocked task) now fails the check instead of
# silently passing.
set -e

celery -A app.worker worker --loglevel=info &
CELERY_PID=$!

python -m app.worker_health &
HTTP_PID=$!

wait -n "$CELERY_PID" "$HTTP_PID"
exit $?
