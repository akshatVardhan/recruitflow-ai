#!/bin/bash
# Cloud Run services require a $PORT listener for health checks, but a
# Celery worker doesn't serve HTTP on its own. Run both as background jobs
# and exit (non-zero) the moment either one dies, so Cloud Run sees the
# container as unhealthy and restarts it instead of a wedged worker
# quietly failing behind a health check that only proves the HTTP server
# is still up.
# ponytail: stdlib http.server as the health-check listener, no real
# liveness signal from Celery itself (just proves the process tree is
# alive). Upgrade to a proper /health endpoint backed by celery_app.control.ping()
# if silent-but-stuck workers become a real problem.
set -e

celery -A app.worker worker --loglevel=info &
CELERY_PID=$!

python -m http.server "${PORT:-8080}" &
HTTP_PID=$!

wait -n "$CELERY_PID" "$HTTP_PID"
exit $?
