# RecruitFlow AI - Architectural Decision Records

# Maintained by: Architect
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
REDIS_URL and QDRANT_URL/QDRANT_API_KEY wired into Doppler's dev config
(prod not yet done - RF-54 scope). Both use TLS (rediss:// / https://).
Discovered and fixed a real bug during validation: Celery's Redis result
backend requires ssl_cert_reqs set explicitly for rediss:// URLs, which
nothing in worker.py configured - see the fix commit on
fix/celery-redis-ssl-backend (PR #50) for detail. Qdrant's 3 collections
(resumes, job_descriptions, hr_documents) were recreated on the fresh
cluster via the existing idempotent ensure_collections() in
core/qdrant.py - no code changes needed there, just running it against
the new instance.
