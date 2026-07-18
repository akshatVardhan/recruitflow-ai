# Design: Retire Celery/Redis ingestion worker in favor of Cloud Run Jobs

Date: 2026-07-12
Status: Approved (design), pending implementation
Related: RF-89, RF-90, RF-91, ADR-013, ADR-015, RF-92 (this work)

## Background

RF-89/90/91 (2026-07-12) made document ingestion reliable in production by
making the Celery worker's Cloud Run service always-on: `--min-instances=1`
(ADR-013) plus `--no-cpu-throttling` (ADR-015). Both were accepted live,
mid-incident, without checking them against the project's actual budget
constraint: **GCP spend must not exceed ₹1000/month** (a standing decision
from the original project plan, confirmed 2026-07-12).

The always-on worker alone costs an estimated **~₹8,500/month** (1 vCPU +
2GiB billed continuously in asia-south1). Root cause: Celery consumes jobs by
continuously polling a Redis broker, which inherently requires an
always-on, always-listening instance — fundamentally incompatible with
Cloud Run's scale-to-zero pricing model, regardless of which throttling or
min-instance flags get tuned. Getting under budget requires replacing the
polling consumer with a push-triggered, pay-per-execution model, not a
config change.

The project currently has ~₹24,000 in GCP credits valid until 2026-09-13,
so there is no immediate out-of-pocket emergency — but the correct
architecture should ship well before that runway ends, and Celery/Redis
was always a poor fit for Cloud Run regardless of the credit situation.

## Decision

Retire Celery and Redis entirely for ingestion. Replace the
`ingest_document.delay(...)` dispatch with a direct invocation of a Cloud
Run **Job** (`recruitflow-ingest`) per uploaded document, via the Cloud Run
Admin API. The job runs the existing ingestion pipeline
(`_run_ingestion_pipeline`, unchanged since RF-89) as a plain async
function call — no broker, no queue product, no long-lived consumer.

### Approaches considered

- **Cloud Run Jobs, invoked directly from the upload endpoint (chosen).**
  No new GCP product to provision. True zero idle cost — pay only for
  actual execution seconds. Retry via the job's own `--max-retries`,
  safe because ingestion is idempotent per `document_id` (driven off
  persisted DB status). At the confirmed volume (≤100 docs/month), this
  keeps ingestion under ~₹100/month.
- **Cloud Tasks (push, OIDC-authenticated) → scale-to-zero Cloud Run
  Service, rejected for now.** Gives Cloud Tasks' built-in
  retry/backoff/dead-letter and warm-instance reuse across bursts, but
  requires provisioning and securing a new GCP product (queue + an
  authenticated internal HTTP endpoint) for headroom this project doesn't
  need yet at ≤100 docs/month. Revisit if volume grows enough that
  cold-start-per-document latency or Cloud Run Jobs' coarser retry model
  becomes a real problem.

### Explicitly out of scope

- **Cloud SQL / Postgres hosting.** Evaluated moving off Cloud SQL
  (`db-f1-micro`, ~₹1,150–1,500/month, the single largest remaining cost)
  to Neon or Supabase. Both would require zero application code changes
  (just a `DATABASE_URL` swap). Deferred to closer to 2026-09-13 when the
  GCP credit runway ends — not part of this work.
- **Artifact Registry cleanup.** Already done separately (2026-07-12):
  deleted 10 unreferenced old images, added a `keep 5 most recent`
  cleanup policy. Not part of this design.

## Architecture

`documents/router.py`'s upload handler currently ends with
`ingest_document.delay(str(document.id))`. That becomes a call to a new
`trigger_ingestion(document_id)` wrapper (in a new
`app/core/ingestion_trigger.py`), which invokes the Cloud Run Admin API's
job-run method against `recruitflow-ingest`, passing `document_id` as a
container environment override. No broker, no queue — the Job invocation
itself is the dispatch mechanism.

The worker image gains a second, lightweight entrypoint alongside (soon:
instead of) the Celery one: `app/ingest_once.py`, a script that reads
`DOCUMENT_ID` from the environment, calls
`asyncio.run(_run_ingestion_pipeline(document_id))` once, and exits 0/1
based on the result.

## Components changed

- **New:** `backend/app/ingest_once.py` — run-once entrypoint, no Celery.
- **New:** `backend/app/core/ingestion_trigger.py` — `trigger_ingestion()`
  wrapper around the Cloud Run Admin API job-run call. Mirrors the
  existing GCS/MinIO conditional pattern in `storage.py`: in
  local/test environments, calls `_run_ingestion_pipeline` directly
  instead of dispatching a real Cloud Run Job.
- **Changed:** `documents/router.py` — swap `ingest_document.delay(...)`
  for `trigger_ingestion(str(document.id))`.
- **Changed:** `.github/workflows/backend-deploy.yml` — the "Deploy Celery
  worker to Cloud Run" step becomes `gcloud run jobs deploy
  recruitflow-ingest` (no `--min-instances`, no `--no-cpu-throttling` —
  Jobs don't have those flags; pure pay-per-execution). Add an IAM step
  granting the backend's service account permission to run the job
  (exact narrowest role to be confirmed during implementation — likely
  `roles/run.developer` scoped to the job resource, or a custom role
  limited to `run.jobs.run`).
- **Removed:** `backend/app/worker.py` (Celery app + task),
  `backend/worker-entrypoint.sh`, `backend/app/worker_health.py` (RF-55's
  health-check listener — meaningless for a Job), the `recruitflow-worker`
  Cloud Run *Service*, the `redis_url` setting and `REDIS_URL` Doppler
  secret, `broker_transport_options`/`task_acks_late` config.
- **New ADR:** documents this decision, explicitly marked as
  **superseding ADR-013 and ADR-015** — their "Accepted" always-on
  decision no longer stands.

## Data flow

Upload → validation (unchanged) → `create_document` (unchanged) →
`trigger_ingestion(document.id)` → Cloud Run Admin API creates a Job
execution → cold container starts, imports the auth/clients/documents
models (still required for the same FK-registration reason RF-89 fixed —
`ingest_once.py` inherits this from the shared pipeline code, not
something to re-break) → runs extract → tag → chunk → embed → persists
final status → exits. Frontend polling of `/documents/{id}/status`
(RF-58/RF-29) is unaffected — it reads whatever status the run-once
script's DB writes leave behind, same contract as today.

## Error handling

Job-level `--max-retries=3`, restarting the container from scratch on
failure. Safe because ingestion is idempotent per `document_id`. RF-89's
`broker_transport_options` visibility-timeout fix and Celery's
`task_acks_late` become moot — there is no broker redelivery to reason
about anymore, which retires an entire class of bug (the retry-counter
reset RF-89 Bug 3 fixed) along with Celery itself. `--task-timeout` set
generously (~10 minutes) to bound a wedged execution without needing
RF-91's CPU-throttling workaround — Jobs always get full CPU for their
execution, so RF-91's starvation bug structurally cannot recur here.

## Testing

- Port `test_worker.py`'s subprocess-isolated FK-registration regression
  test to import `ingest_once` instead of `worker` — same reasoning
  (worker/job entrypoints must independently trigger full model
  registration, not rely on `app.main`'s import chain), same test shape.
- Delete the Celery-specific tests (retry/serialization) — nothing left
  to test there.
- Mock `trigger_ingestion`'s Cloud Run Job dispatch in router tests, same
  approach already used for storage's GCS/MinIO branch.
- Manual live verification after deploy: `scripts/smoke_test_ingestion.py`
  against production, same script RF-89/90/91 already used.

## Cost impact

| | Before (always-on worker) | After (Cloud Run Jobs) |
|---|---|---|
| Worker/ingestion compute | ~₹8,500/month | ~₹30–60/month (≤100 docs/month) |

Combined with the already-completed Artifact Registry cleanup
(~₹350–450/month → ~₹170/month), GCP spend drops from an estimated
~₹10,000–10,600/month to ~₹1,350–1,900/month. The remaining gap to the
₹1000/month target is Cloud SQL (~₹1,150–1,500/month), deliberately
deferred — see "Explicitly out of scope" above.
