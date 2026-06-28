# RecruitFlow AI - Database Schema

# Read by: Backend Developer before implementing any SQLAlchemy models or Alembic migrations.
# Maintained by: Backend Developer (update this file when schema changes are made).
# No separate DB Designer agent exists. The Backend Dev owns schema decisions.

---

## Conventions

All tables:
- Primary key: id UUID, default gen_random_uuid(), not null
- Created timestamp: created_at TIMESTAMP WITH TIME ZONE, default now(), not null
- Updated timestamp: updated_at TIMESTAMP WITH TIME ZONE, default now(), not null (use SQLAlchemy onupdate)
- Soft delete where noted: deleted_at TIMESTAMP WITH TIME ZONE, nullable

Naming:
- Tables: snake_case, plural (documents, pipeline_stages)
- Columns: snake_case (created_at, client_id)
- Foreign keys: {referenced_table_singular}_id (client_id, document_id)
- Indexes: idx_{table}_{column} (idx_documents_client_id)
- Enums: snake_case values (job_description, offer_letter)

All foreign key columns must have an index.
All columns used in WHERE clauses frequently must have an index.
Use JSONB for flexible metadata fields.
Use PostgreSQL native ENUM types for fixed-value fields.

---

## Enums

document_type:
  resume
  job_description
  offer_letter
  sop
  performance_report
  policy
  contract
  other

candidate_source:
  linkedin
  referral
  portal
  upload
  other

employment_type:
  full_time
  part_time
  contract
  internship
  freelance

job_status:
  open
  closed
  on_hold
  draft

pipeline_stage_default:
  screening
  interview
  assessment
  offer
  hired
  rejected

---

## Tables

### users
Maps to Supabase Auth (or custom auth users table).

id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
email             TEXT NOT NULL UNIQUE
full_name         TEXT NOT NULL
hashed_password   TEXT NOT NULL
is_active         BOOLEAN NOT NULL DEFAULT true
created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()

Indexes:
- idx_users_email on email

---

### clients
A client is a company or firm that the HR user manages.

id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
name              TEXT NOT NULL
industry          TEXT
is_active         BOOLEAN NOT NULL DEFAULT true
created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
deleted_at        TIMESTAMPTZ

Indexes:
- idx_clients_user_id on user_id

---

### documents
Every file uploaded to the system. Core of the document management feature.

id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
client_id         UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE
user_id           UUID NOT NULL REFERENCES users(id)
title             TEXT NOT NULL
doc_type          document_type NOT NULL
file_path         TEXT NOT NULL -- path in MinIO/GCS
file_name         TEXT NOT NULL -- original filename for display
file_size_kb      INTEGER
mime_type         TEXT
extracted_text    TEXT -- full text extracted from file
auto_tags         JSONB -- {document_type, candidate_name, role, company, skills: [], date}
manual_tags       TEXT[] -- user-added tags
created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
deleted_at        TIMESTAMPTZ

Indexes:
- idx_documents_client_id on client_id
- idx_documents_user_id on user_id
- idx_documents_doc_type on doc_type
- idx_documents_created_at on created_at DESC
- Full-text search index: CREATE INDEX idx_documents_fts ON documents USING gin(to_tsvector('english', title || ' ' || coalesce(extracted_text, '')))

---

### doc_chunks
Mirrors Qdrant entries for hybrid search without round-tripping to Qdrant.

id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
document_id       UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE
chunk_index       INTEGER NOT NULL
chunk_text        TEXT NOT NULL
qdrant_point_id   UUID NOT NULL UNIQUE -- the point ID in Qdrant
created_at        TIMESTAMPTZ NOT NULL DEFAULT now()

Indexes:
- idx_doc_chunks_document_id on document_id
- idx_doc_chunks_qdrant_point_id on qdrant_point_id

---

### jobs
A job opening posted or managed by the HR user for a client.

id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
client_id         UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE
title             TEXT NOT NULL
department        TEXT
location          TEXT
employment_type   employment_type
jd_document_id    UUID REFERENCES documents(id) ON DELETE SET NULL
status            job_status NOT NULL DEFAULT 'draft'
created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
deleted_at        TIMESTAMPTZ

Indexes:
- idx_jobs_client_id on client_id
- idx_jobs_status on status

---

### candidates
A person who has applied or been sourced for a role.

id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
client_id         UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE
full_name         TEXT NOT NULL
email             TEXT
phone             TEXT
linkedin_url      TEXT
resume_document_id UUID REFERENCES documents(id) ON DELETE SET NULL
source            candidate_source
created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
deleted_at        TIMESTAMPTZ

Indexes:
- idx_candidates_client_id on client_id
- idx_candidates_email on email

Note: email and phone are PII. Do not log these fields. Do not include in error messages.

---

### pipeline_stages
The columns in the ATS Kanban board. Each client can have custom stages.

id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
client_id         UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE
name              TEXT NOT NULL
position          INTEGER NOT NULL -- display order, 0-indexed
colour_hex        TEXT NOT NULL DEFAULT '#71717a' -- zinc-500 default
is_default        BOOLEAN NOT NULL DEFAULT false
created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()

Indexes:
- idx_pipeline_stages_client_id on client_id

Default stages seeded per client on creation:
position 0: Screening, colour #3b82f6 (blue-500), is_default true
position 1: Interview, colour #f59e0b (amber-500), is_default true
position 2: Assessment, colour #8b5cf6 (violet-500), is_default true
position 3: Offer, colour #10b981 (emerald-500), is_default true
position 4: Hired, colour #22c55e (green-500), is_default true
position 5: Rejected, colour #ef4444 (red-500), is_default true

---

### applications
Links a candidate to a job and tracks their current pipeline stage.

id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
job_id            UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE
candidate_id      UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE
stage_id          UUID NOT NULL REFERENCES pipeline_stages(id)
applied_at        TIMESTAMPTZ NOT NULL DEFAULT now()
last_stage_change_at TIMESTAMPTZ NOT NULL DEFAULT now()
is_active         BOOLEAN NOT NULL DEFAULT true
created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()

Indexes:
- idx_applications_job_id on job_id
- idx_applications_candidate_id on candidate_id
- idx_applications_stage_id on stage_id
- UNIQUE (job_id, candidate_id) -- one application per candidate per job

---

### application_notes
Free-text notes on an application.

id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
application_id    UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE
note_text         TEXT NOT NULL
created_at        TIMESTAMPTZ NOT NULL DEFAULT now()

Indexes:
- idx_application_notes_application_id on application_id

---

### activity_log
Audit trail for all state changes to applications, candidates, and jobs.

id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
entity_type       TEXT NOT NULL -- 'application', 'candidate', 'job'
entity_id         UUID NOT NULL
action            TEXT NOT NULL -- 'stage_changed', 'candidate_created', 'job_closed', etc.
old_value         JSONB
new_value         JSONB
user_id           UUID REFERENCES users(id)
created_at        TIMESTAMPTZ NOT NULL DEFAULT now()

Indexes:
- idx_activity_log_entity on (entity_type, entity_id)
- idx_activity_log_created_at on created_at DESC

---

### generation_requests
Records every AI document generation request.

id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id           UUID NOT NULL REFERENCES users(id)
client_id         UUID NOT NULL REFERENCES clients(id)
doc_type          document_type NOT NULL
reference_doc_ids TEXT[] -- list of document IDs used as RAG context
prompt_context    JSONB -- the context object sent to the LLM
output_text       TEXT -- the full generated text (populated when streaming completes)
output_file_path  TEXT -- path in MinIO/GCS if exported
model_used        TEXT NOT NULL DEFAULT 'deepseek-v4-flash'
created_at        TIMESTAMPTZ NOT NULL DEFAULT now()

Indexes:
- idx_generation_requests_user_id on user_id
- idx_generation_requests_client_id on client_id
- idx_generation_requests_created_at on created_at DESC

---

### talent_searches
Records talent finder search sessions.

id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id           UUID NOT NULL REFERENCES users(id)
client_id         UUID NOT NULL REFERENCES clients(id)
filters           JSONB NOT NULL -- {location, role_type, skills, experience_min, experience_max, ...}
result_count      INTEGER
created_at        TIMESTAMPTZ NOT NULL DEFAULT now()

---

### job_searches
Records job finder search sessions.

id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id           UUID NOT NULL REFERENCES users(id)
client_id         UUID NOT NULL REFERENCES clients(id)
resume_document_id UUID REFERENCES documents(id)
filters           JSONB NOT NULL
result_count      INTEGER
created_at        TIMESTAMPTZ NOT NULL DEFAULT now()

---

## Qdrant Collections

Collection: resumes
Vector size: 384 (BAAI/bge-small-en-v1.5 output dimension)
Distance: Cosine
Payload fields per point:
  doc_id: string (UUID)
  chunk_index: integer
  candidate_name: string
  skills: string[]
  experience_years: integer (nullable)
  location: string (nullable)
  client_id: string (UUID) -- REQUIRED for filtered retrieval

Collection: job_descriptions
Vector size: 384
Distance: Cosine
Payload fields:
  doc_id: string
  chunk_index: integer
  job_title: string
  department: string (nullable)
  location: string (nullable)
  client_id: string

Collection: hr_documents
Vector size: 384
Distance: Cosine
Payload fields:
  doc_id: string
  chunk_index: integer
  doc_type: string
  tags: string[]
  client_id: string

All Qdrant queries must include a filter on client_id.
Never return results from a different client's collection data.

---

## Migration Order

Implement Alembic migrations in this order to avoid FK constraint failures:

001: users table
002: clients table
003: documents table
004: doc_chunks table
005: jobs table
006: candidates table
007: pipeline_stages table
008: applications table
009: application_notes table
010: activity_log table
011: generation_requests table
012: talent_searches table
013: job_searches table
014: seed default pipeline stages function
