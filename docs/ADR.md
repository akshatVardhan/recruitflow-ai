# RecruitFlow AI - Architectural Decision Records

# Maintained by: no single owner (2026-07-11: the Architect role that used
# to own this file was dissolved in a role consolidation - any role records
# a decision here via the /adr skill when making one).
# Updated whenever a significant architectural decision is made.
# Each ADR is permanent - never delete or overwrite an existing entry.
# If a decision is reversed, add a new ADR superseding the old one.

---

## ADR-001 - Modular Monolith over Microservices
Date: 2026-06-30
Status: Accepted
Agent: Backend Dev

Decision:
Use a modular monolith architecture for the backend rather than microservices.

Reasoning:
Single developer and AI agent team. Microservices add deployment and
operational complexity that is not justified at this scale. The modular
monolith gives clean module boundaries that can be extracted into services
later if needed, without the overhead of inter-service communication now.

Consequences:
All modules run in a single FastAPI process. Celery handles async workloads.
If the project grows to need separate scaling per module, the module boundaries
are already clean enough to extract.

---

## ADR-002 - LlamaIndex over LangChain for RAG
Date: 2026-06-30
Status: Accepted
Agent: Backend Dev

Decision:
Use LlamaIndex as the RAG framework rather than LangChain.

Reasoning:
LlamaIndex is purpose-built for document ingestion, chunking, and retrieval.
The project's core value is document intelligence. LlamaIndex handles
connectors, chunkers, and retrievers out of the box. LangChain is broader
but requires more assembly for document-heavy use cases.
LangGraph (LangChain's agent orchestration layer) remains on the roadmap
for future multi-agent workflows.

Consequences:
LlamaIndex handles the RAG pipeline. LiteLLM handles the LLM abstraction
layer above it. If LangGraph is introduced later it will sit alongside
LlamaIndex, not replace it.

---

## ADR-003 - Local Embeddings over Voyage AI
Date: 2026-06-30
Status: Accepted
Agent: Backend Dev

Decision:
Use Sentence Transformers (BAAI/bge-small-en-v1.5) running locally rather
than Voyage AI cloud embeddings.

Reasoning:
Cost optimisation. Voyage AI charges per token embedded. For a tool
processing many resumes and documents daily, this adds up. BAAI/bge-small
runs on CPU with acceptable performance for this use case. The 384-dimension
output is smaller than Voyage AI's models but retrieval quality is sufficient
for HR document search.

Tradeoff accepted:
Slightly lower retrieval quality than Voyage AI voyage-3. Cold start on
Cloud Run loads the model (~500MB). Mitigated by Cloud Run min-instances=1.

---

## ADR-004 - LiteLLM as LLM Abstraction Layer
Date: 2026-06-30
Status: Accepted
Agent: Backend Dev

Decision:
All LLM calls go through LiteLLM rather than calling DeepSeek API directly.

Reasoning:
Provider lock-in prevention. If DeepSeek V4-Flash becomes unavailable,
expensive, or underperforms, switching providers requires changing one
config value rather than rewriting call sites. LiteLLM supports OpenAI,
Anthropic, DeepSeek, and 100+ others with a unified interface.

Consequences:
Model string format: "deepseek/deepseek-v4-flash"
All streaming, structured output, and tool use goes through LiteLLM.
Never import the DeepSeek SDK directly.

---

## ADR-006 - Z.AI GLM 5.2 over DeepSeek V4-Flash
Date: 2026-07-04
Status: Accepted
Agent: Frontend Dev (recorded by FD; decision owner: Backend Dev / DevOps Eng)

Decision:
Replace DeepSeek V4-Flash with Z.AI GLM 5.2 as the LLM provider for all AI features (auto-tagging, document generation, resume scoring).

Reasoning:
Z.AI GLM 5.2 offers 1M-token context window, superior reasoning capabilities for long-horizon tasks, and competitive pricing. The switch is made possible by LiteLLM abstraction -- no code changes beyond updating the model string and API key configuration.

Consequences:
Model string changed from "deepseek/deepseek-v4-flash" to "zai/glm-5.2".
API key env var changed from DEEPSEEK_API_KEY to ZAI_API_KEY.
All existing DeepSeek-specific configuration fields retained in config.py for backward compatibility during transition.
All LLM interactions continue to go through LiteLLM -- no provider SDK imported directly.

Amendment (2026-07-05):
GLM 5.2 is not accessed directly through Z.AI's own API in this project -
access is through a third-party host, DeepInfra, which is also how the
coding-agent tooling already routes GLM 5.2 (see ANTHROPIC_BASE_URL/
ANTHROPIC_MODEL in Doppler). The original migration incorrectly assumed a
direct Z.AI integration and configured the model string as "zai/glm-5.2"
with a ZAI_API_KEY - litellm's "zai/" prefix targets Z.AI's own endpoint,
which rejected the DeepInfra-issued key that had been placed in that slot
(same value as DEEPINFRA_API_KEY, copied in by mistake during the original
migration). This broke auto-tagging, document generation, and resume
scoring end-to-end in every environment until fixed.
Corrected model string: "deepinfra/zai-org/GLM-5.2" (matches the exact
model slug already used for ANTHROPIC_MODEL).
Corrected API key env var: DEEPINFRA_API_KEY (already existed in Doppler
for the agent-tooling use case; the stray ZAI_API_KEY entry should be
removed once nothing references it).
GLM 5.2 is a reasoning model - it emits hidden reasoning_content before
the visible answer, so max_tokens must budget for both, not just the
visible output size.

---

## ADR-005 - MinIO for Local Storage, GCS for Production
Date: 2026-06-30
Status: Accepted
Agent: DevOps

Decision:
Use MinIO in local development and Google Cloud Storage in production.
Both are accessed via the same S3-compatible boto3 interface.

Reasoning:
MinIO runs as a Docker container with zero cost and zero internet dependency.
GCS is used in production within GCP credits. The S3-compatible API means
zero code changes between environments - only the endpoint URL and
credentials change via environment variables.

Consequences:
core/storage.py uses boto3 with configurable endpoint_url.
Local: endpoint_url points to localhost:9000 (MinIO).
Production: endpoint_url is None (boto3 defaults to AWS S3 format,
overridden by GCS credentials via google-cloud-storage library or
a GCS-compatible S3 endpoint).

Amendment (2026-07-10):
The original implementation pointed boto3 at
https://storage.googleapis.com with aws_access_key_id hardcoded to "_"
and aws_secret_access_key set to a GCS service-account JSON blob
(gcs_credentials_json). This is the wrong credential type for that slot
- boto3's aws_secret_access_key expects an HMAC secret key, not a JSON
document - so every real upload/download/delete against GCS failed at
the storage layer in every environment (RF-56).

Fixed via a real GCS HMAC key pair (Option A: keep the single boto3
S3-compatible client for both MinIO and GCS, no second code path). The
existing recruitflow-agents service account (already granted
roles/storage.objectAdmin) was reused via `gcloud storage hmac create`.
Corrected config: gcs_hmac_access_key and gcs_hmac_secret_key
(config.py Settings), replacing gcs_credentials_json entirely.
core/storage.py now passes these as aws_access_key_id /
aws_secret_access_key instead of the hardcoded "_" and the JSON blob.
GOOGLE_APPLICATION_CREDENTIALS_JSON (a separate, unrelated
service-account key that was never referenced anywhere in the app or
CI/CD - the deploy pipeline authenticates via keyless Workload Identity
Federation) was found alongside this work and is unrelated to storage
auth; it's tracked separately.

Key rotation policy: HMAC keys do not expire automatically. Rotate
quarterly (owner duty) - create a new key pair via `gcloud storage hmac
create`, update GCS_HMAC_ACCESS_KEY/GCS_HMAC_SECRET_KEY in Doppler
(dev and prd), confirm the new key works, then deactivate and delete
the old key via `gcloud storage hmac update ACCESS_ID --deactivate`
followed by `gcloud storage hmac delete ACCESS_ID`. Never delete the
old key before the new one is confirmed working end-to-end.

---

## ADR-007 - Upstash for Redis, Qdrant Cloud for Qdrant (dev and prod, both environments)
Date: 2026-07-06
Status: Accepted
Agent: Backend Dev / DevOps Eng

Decision:
Use Upstash (managed serverless Redis) for the Celery broker/result backend,
and Qdrant Cloud's free tier (GCP-hosted, Frankfurt region) for the vector
store, in both dev and prod. Neither is GCP-native.

Reasoning:
Redis in this project only serves as the Celery broker/result backend for
async document ingestion (RF-25) - a background job queue, not a
latency-sensitive request-path cache. GCP Memorystore for Redis was
considered (available GCP credits, ~$300 expiring ~Sept 2026) but has no
free tier and bills for provisioned capacity 24/7 regardless of usage
(~$36/mo for the smallest 1GiB Basic tier) - the credits would only defer
that cost by ~2 months, not eliminate it, and Memorystore's real value
(private VPC networking, managed HA/failover) targets a problem this
project doesn't have at its current scale. Upstash's free tier (500K
commands/month) almost certainly covers this project's actual traffic
(a solo recruiter's document uploads) at $0/month indefinitely.

Qdrant is different: it sits on the live request path (hybrid_search/
semantic_search are called synchronously during RAG retrieval), so network
locality actually matters here. Qdrant Cloud's free tier was chosen over
self-hosting on a GCP Compute Engine VM for zero ops overhead; the GCP
provider option was picked within Qdrant Cloud (confirmed available on the
free tier) for cloud locality, with Frankfurt chosen over the only
Asia-Pacific option offered (Sydney) based on great-circle distance to
Mumbai (~6,600km vs ~10,000km) and typical India-Europe submarine cable
routing (SEA-ME-WE) - not measured with a live ping test, worth confirming
if latency ever becomes a concern.

Redis eviction is disabled on the Upstash instance: it's a message queue,
and silent LRU eviction of an unprocessed task message means a document
upload vanishes with zero trace. A loud out-of-memory error on a full
queue is the safer failure mode than silent data loss.

Consequences:
REDIS_URL and QDRANT_URL/QDRANT_API_KEY wired into Doppler's dev config.
Both use TLS (rediss:// / https://).
Discovered and fixed a real bug during validation: Celery's Redis result
backend requires ssl_cert_reqs set explicitly for rediss:// URLs, which
nothing in worker.py configured - see the fix commit on
fix/celery-redis-ssl-backend (PR #50) for detail. Qdrant's 3 collections
(resumes, job_descriptions, hr_documents) were recreated on the fresh
cluster via the existing idempotent ensure_collections() in
core/qdrant.py - no code changes needed there, just running it against
the new instance.

Update (2026-07-10, RF-54): prod Doppler config populated too - same
Redis/Qdrant instances as dev, shared rather than separately
provisioned (owner-approved, simplest at this project's scale). See
RF-54's agent-run-log.md entry for the full prod-deploy fix chain this
required (Workload Identity Federation, Cloud Run memory sizing, etc.)
- out of scope for this ADR, which is about the provider choice, not
the deploy pipeline.

---

## ADR-008 - JWT via python-jose, Bearer Access Token + Cookie Refresh Token
Date: 2026-07-10 (retroactive - written after RF-63 implementation shipped,
not before it as RF-62's acceptance criteria intended; see Process note below)
Status: Accepted
Agent: DevOps Eng (Claude Code), documenting Backend Dev's shipped implementation

Decision:
JWT-based auth using python-jose for encode/decode, HS256 signing, a
short-lived access token (60 min default) returned in the response body
and sent as a Bearer header, and a longer-lived refresh token (7 days
default) set as an httpOnly cookie scoped to /api/v1/auth.

Reasoning:
python-jose was already the dependency in place when this ADR was
written retroactively - RF-48's original plan called for a PyJWT
migration instead, but the shipped code (backend/app/modules/auth/
service.py) uses jose.jwt throughout and there is no indication a
migration was ever done. Recorded here as the actual decision rather
than the originally planned one; revisiting the PyJWT switch is a
separate, optional future task if a concrete reason to migrate ever
appears (python-jose has had past CVEs - see the pip-audit exchange
history in the sprint-state memory for the pyasn1/python-jose version
pinning saga - but the currently pinned version has no known open
vulnerabilities as of this writing).
Access-token-in-body + refresh-token-in-cookie is a standard split:
the access token is short-lived enough that XSS exposure risk is
bounded, while the refresh token needs httpOnly protection since it's
long-lived and higher-value. is_production toggles the refresh
cookie's SameSite/Secure attributes (Lax+non-secure for same-origin
local dev, None+Secure for the real cross-origin Vercel+Cloud Run
production split) - see config.py's is_production field comment.

Consequences:
Token payload: {sub: user_id, type: "access"|"refresh", iat, exp} -
no tenancy/role claims, see ADR-009 for why.
Refresh tokens are currently stateless: decode_token() only checks the
JWT's own signature and type claim, there is no server-side token
store. This means logout only clears the client-side cookie - a
stolen or previously-issued refresh token remains valid until it
naturally expires, it cannot be revoked. RF-64's acceptance criteria
already tracks this as open work (a refresh_tokens table with rotation
and server-side revocation) - not done as of this ADR, do not assume
otherwise without checking RF-64's current status first.

Process note: RF-62 asked for this ADR to be written and reviewed
*before* RF-63's implementation started. That did not happen - RF-63
(and RF-64) shipped first (PR #63, 2026-07-06), and this ADR is being
written after the fact to document what was actually built. Not
correcting the history, just being honest that the intended
architect-reviews-before-implementation sequencing didn't hold here.

---

## ADR-009 - Tenancy via Per-Request client_id Ownership Check, Not a JWT Claim
Date: 2026-07-10 (retroactive, same caveat as ADR-008)
Status: Accepted
Agent: DevOps Eng (Claude Code), documenting Backend Dev's shipped implementation

Decision:
A user can own multiple Clients (backend/app/modules/clients/models.py:
Client.user_id is a foreign key to User, one-to-many). Every
client-scoped request (documents, uploads, etc.) carries its own
client_id explicitly - as a path parameter or request body field - and
the backend checks ownership (the requested client's user_id matches
the authenticated user from get_current_user) per request. There is no
"active client" claim baked into the JWT, and no switch-client
endpoint - a user simply addresses whichever client they own on each
request.

Reasoning:
This differs from RF-62's original proposal (a single client_id claim
in the JWT plus a switch-client endpoint that reissues tokens when the
user changes context). The per-request-ownership-check model is
simpler for a multi-client user: no token reissuance needed to operate
across clients in the same session, no risk of a stale client_id claim
in a still-valid access token after a switch. The tradeoff is an
ownership check on every client-scoped endpoint instead of a single
claim decode - a real but small per-request cost, not a security
concern (the check itself is a straightforward equality comparison
against an already-fetched row).

Consequences:
Every new endpoint that operates on a specific client's data must
remember to check ownership explicitly - this is not automatically
enforced by a shared JWT claim the way the original design would have
been. Worth a shared dependency/decorator if the number of
client-scoped endpoints grows large enough that repeating the check
becomes error-prone; not done yet, not clearly needed yet either given
the current endpoint count.
This ADR does not change RF-64's still-open refresh-token-revocation
gap (see ADR-008) - they're related (both are auth/tenancy hardening)
but distinct pieces of work.

---

## ADR-010 - Keep PyMuPDF (AGPL) for PDF Extraction
Date: 2026-07-10
Status: Accepted
Agent: DevOps Eng (Claude Code)

Decision:
Keep PyMuPDF (imported as `fitz`, pinned at 1.28.0 in requirements.txt,
used in backend/app/modules/documents/extractor.py) for PDF text
extraction rather than switching to pypdf or another permissively
licensed alternative.

Reasoning:
PyMuPDF's open-source distribution is AGPL-3.0 licensed. AGPL's network-use
clause (section 13) requires offering the complete corresponding source
to users who interact with the software over a network - relevant here
since RecruitFlow is a network-accessed SaaS product, not
locally-distributed software. However: this repository is already
public (a deliberate decision made 2026-07-03, verified via a full git
history secret scan before doing so - see progress.md's "Pre-Publication
Git History Secret Scan" section), meaning the actual source code AGPL
cares about making available is already available, to anyone, not just
to users of the deployed service. This substantially satisfies AGPL's
practical intent even if it doesn't tick every formal compliance box a
lawyer might want (e.g. an explicit in-app "source code" link, a formal
written offer). PyMuPDF's extraction quality (particularly for
complex/scanned resume layouts, tables, and multi-column text) is also
meaningfully better than pypdf's in informal testing during earlier
sprints - not benchmarked rigorously, but the gap was visible enough
that switching has a real product-quality cost, not just a licensing
question.

This is not legal advice and this ADR does not constitute a formal
compliance review - if RecruitFlow's business model ever requires the
repository to go private, or if a customer/investor due-diligence
process specifically flags this, revisit then. Artifex (PyMuPDF's
maintainer) also sells a commercial (non-AGPL) license, which is the
fallback if the public-repo rationale ever stops applying.

Consequences:
No code or requirements.txt change from this ADR - it documents an
already-made, already-shipped choice. If this decision is ever
reversed, pypdf is the most likely replacement (already evaluated
informally, pure-Python, no AGPL concerns) - budget for a real
extraction-quality regression test against a sample of actual resume
PDFs before swapping, not just a "does it run without crashing" check.

---

## ADR-011 - Migrate Before Deploy, Abort on Migration Failure
Date: 2026-07-11
Status: Accepted
Agent: DevOps Eng (Claude Code)

Decision:
In .github/workflows/backend-deploy.yml, run the recruitflow-migrate
Cloud Run Job (`alembic upgrade head`) before deploying either
recruitflow-backend or recruitflow-worker, and use `gcloud run jobs
update --wait` (not `--execute-now`) so the workflow step's own exit
code reflects the migration container's real result.

Reasoning:
The job previously ran migrations last, after both services were
already serving the new image - meaning new code could hit a not-yet-
migrated schema for the entire deploy window. It also used
`--execute-now` alone, which only waits for the Cloud Run Job execution
to *start*, not finish; a container that exited non-zero still left
gcloud (and the GitHub Actions step) reporting success, so a broken
migration would never have blocked the deploy even after reordering.
`--wait` implies `--execute-now` and blocks until the execution
completes, surfacing the container's real exit code. With that in
place, GitHub Actions' default fail-fast behavior (no
`continue-on-error` is set anywhere in this job) means a failed
migration step fails the job and skips every remaining step - both
`gcloud run deploy` calls simply never run, so no traffic is ever
promoted to a revision expecting a schema that isn't there. No custom
abort logic was needed beyond correct step ordering + `--wait`.

Consequences:
Rollback path if a bad migration lands anyway (e.g. it succeeded but
the resulting schema is wrong in a way alembic couldn't catch):
1. Revert the migrating revision:
   `gcloud run jobs update recruitflow-migrate --region=asia-south1 --project=recruitflow-ai-500719 --command=alembic --args=downgrade,-1 --wait`
   downgrades one revision. For a specific target instead of one step
   back, pass `--args=downgrade,<revision_id>`. If the migration isn't
   cleanly reversible (e.g. it dropped a column and data was lost),
   alembic downgrade can't recover the data - restore via Cloud SQL
   point-in-time recovery instead
   (recruitflow-ai-500719:asia-south1:recruitflow-db), which needs a
   manual decision on acceptable data loss window and is not
   automated here.
2. Roll back the deployed image independently of the schema: Cloud Run
   keeps prior revisions, so
   `gcloud run services update-traffic recruitflow-backend --region=asia-south1 --project=recruitflow-ai-500719 --to-revisions=<prior-revision>=100`
   (and the same for recruitflow-worker) repoints traffic without a
   rebuild. Since migrations now always run before deploy, the prior
   revision was validated against the pre-migration schema - only use
   this to revert a bad *code* change, not to dodge a bad migration
   (the schema is likely already forward-migrated and the old code may
   not be compatible with it).
3. In both cases, a fixed job name (recruitflow-migrate) and fixed
   service names mean no lookup is needed - the names above are the
   only ones that exist in this project.

---

## ADR-012 - Keyless Workload Identity Federation for GitHub Actions -> GCP Auth
Date: 2026-07-09 (retroactive - written after RF-54's fix already shipped)
Status: Accepted
Agent: DevOps Eng (Claude Code), documenting a decision made during RF-54

Decision:
`backend-deploy.yml` authenticates to GCP via `google-github-actions/auth@v2`
using Workload Identity Federation (WIF) - a workload identity pool +
GitHub OIDC provider scoped to this exact repo, with the IAM binding on
`recruitflow-agents@recruitflow-ai-500719.iam.gserviceaccount.com`
further restricted to `refs/heads/main` only (the provider's own
attribute-condition). No static GCP credential (service-account key
JSON) exists anywhere in this repo, its secrets, or Doppler.

Reasoning:
Not a preference between two working options - a static SA key was not
available at all. Every push-to-main deploy had been silently failing
at the auth step since 2026-07-03 (`GCP_SERVICE_ACCOUNT_KEY` never
existed as a repo secret). Attempting to generate a new key for either
`recruitflow-agents` or the project's default compute SA was rejected
by GCP itself: this project enforces
`constraints/iam.disableServiceAccountKeyCreation` as an org policy,
project-wide, tested against both service accounts. WIF was therefore
the only viable path, not a hardening choice made among alternatives -
though it's also the objectively safer one: no long-lived secret to
leak, rotate, or scope-creep, and the `refs/heads/main`
attribute-condition means even a compromised workflow file on another
branch can't mint a token this identity would accept.

Consequences:
`backend-deploy.yml`'s "Authenticate to GCP" step passes
`workload_identity_provider:
projects/424745949201/locations/global/workloadIdentityPools/github-actions/providers/github`
and `service_account:
recruitflow-agents@recruitflow-ai-500719.iam.gserviceaccount.com` -
these two values are the actual identity of this setup; if the pool,
provider, or service account is ever recreated, both need to change
together, in this file, or the deploy pipeline's auth step fails
closed with no fallback (there is no key to fall back to on purpose).
Any *future* CI/CD job needing GCP access in this project should use
WIF the same way, not attempt an SA key - the org policy blocks it
project-wide, not just for this one service account. Discovered as
one of a 7-bug chain the first time the full deploy pipeline was
actually run end-to-end (see `progress.md`'s "Main Branch State" /
RF-54 entry in the agents-repo for the other 6: `workflow_dispatch`
trigger, runner disk space, Doppler installer sudo, Cloud Run
self-actAs IAM grant, 2GiB memory bump, migration job service account -
those are operational fixes, not architectural decisions, so they
don't get their own ADR entries).

---

## ADR-013 - Worker Service Needs min-instances=1, Not Scale-to-Zero
Date: 2026-07-12
Status: Accepted
Agent: DevOps Eng (Claude Code), discovered while closing out RF-55

Decision:
`recruitflow-worker` is deployed with `--min-instances=1`, keeping one
Cloud Run instance running at all times instead of the default
scale-to-zero behavior.

Reasoning:
Cloud Run Services autoscale on inbound HTTP request volume, not on
background work - but `recruitflow-worker` has no legitimate external
HTTP callers (`--no-allow-unauthenticated`, only Cloud Run's own health
probe), so it had no signal ever keeping an instance warm. Meanwhile
`app.worker`'s import chain pulls in the same heavy ML stack
(torch/sentence-transformers) that required the API service's 2GiB
memory bump - confirmed via Cloud Logging, Celery took ~6-9 minutes
from container start to logging "ready" and connecting to the Upstash
broker. A deploy's own startup probe passes almost instantly (the
stdlib http.server binds `$PORT` immediately), so Cloud Run considered
the instance healthy and then scaled it back down as idle long before
Celery finished booting. Net effect: queued ingestion jobs were very
unlikely to ever be picked up, regardless of health-check quality -
confirmed live during RF-55's smoke test, where a queued job sat in
`status: "uploaded"` for a full 2-minute poll window with zero Celery
log lines anywhere in that revision's history.

Consequences:
Real recurring cost: an always-on 2GiB instance instead of
scale-to-zero. Accepted because a Celery worker that isn't running
defeats the point of deploying it. If cost becomes a concern, the
alternative is restructuring ingestion as a Cloud Run Job triggered
per-upload (e.g. via Pub/Sub or a direct `jobs run` call from the
upload endpoint) instead of a long-lived consumer - not attempted here,
would be a larger redesign. Revisit if `app.worker`'s import footprint
is ever slimmed down enough that cold start reliably beats Cloud Run's
idle-scale-down window, since that would remove the need for
`min-instances=1` entirely.
