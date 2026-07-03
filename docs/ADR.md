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
