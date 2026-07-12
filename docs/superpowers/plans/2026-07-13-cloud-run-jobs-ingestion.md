# Retire Celery/Redis Worker for Cloud Run Jobs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the always-on Celery/Redis ingestion worker (ADR-013/ADR-015, ~₹8,500/month) with a Cloud Run Job invoked directly per upload, cutting ingestion compute cost to ~₹30–60/month while keeping the reliability RF-89/90/91 already proved.

**Architecture:** The upload endpoint calls a new `trigger_ingestion()` function instead of `ingest_document.delay()`. In production it invokes the Cloud Run Admin API to run a one-shot Job execution (`recruitflow-ingest`) with `document_id` passed as a container env override; in local/test environments (no `gcp_project_id` configured) it calls the ingestion pipeline directly, in-process. The pipeline function itself (`run_ingestion_pipeline`, RF-89's fixed FK-registration + event-loop-safe engine logic, unchanged) moves out of the Celery-specific `worker.py` into a shared `app/core/ingestion_pipeline.py` so both the new Job entrypoint (`app/ingest_once.py`) and the trigger's local-dev fallback can call it without any Celery dependency.

**Tech Stack:** FastAPI, SQLAlchemy async, `google-cloud-run` (new dependency, `google.cloud.run_v2.JobsAsyncClient`), pytest/pytest-asyncio, existing Doppler/Cloud Run/GitHub Actions deploy pipeline.

## Global Constraints

- GCP project: `recruitflow-ai-500719`, region `asia-south1` (verbatim from every existing deploy step — do not vary).
- The runtime service account for `recruitflow-backend` is `recruitflow-agents@recruitflow-ai-500719.iam.gserviceaccount.com`, which **already has `roles/run.developer` at the project level** (verified live via `gcloud projects get-iam-policy`) — this role includes `run.jobs.run` and `run.jobs.get`. **No new IAM grant is required** for the backend to invoke `recruitflow-ingest`; do not add one speculatively.
- Assertion standard for tests: strict. Never `status_code in (x, 500)` or any tolerance-of-failure pattern.
- Mock external dependencies (GCS, the ingestion Cloud Run Job trigger, LLM) for determinism in tests — never make real network/GCP calls from the test suite.
- Every commit message: `type(scope): description RF-92` (or the relevant subtask key once created).
- Do NOT delete `backend/app/worker.py`, `backend/worker-entrypoint.sh`, `backend/app/worker_health.py`, the `recruitflow-worker` Cloud Run service, or the `celery`/`redis` dependencies until Task 9 — the old path must stay intact and deployable until the new path is live-verified in production (Task 8).
- Repo is public (unlimited GitHub Actions minutes); branch protection on `staging` and `main` requires `backend-ci`, `frontend-ci`, `security` — these are BLOCKING gates, never bypass with `|| true` or `continue-on-error`.
- This branch (`feature/RF-92-cloud-run-jobs-ingestion`) was created from `origin/main`, NOT `origin/staging` — `staging` is currently 8 commits behind `main` (RF-90/91/121 hotfixes went straight to main). Target the PR at `main`, matching that precedent, not `staging`.

---

### Task 1: Create JIRA tracking (RF-92 parent + subtasks)

No code — this is a tool-call task, per this project's convention that every unit of work has a JIRA ticket before implementation starts.

**Files:** None.

- [ ] **Step 1: Create the parent task**

Use the JIRA MCP tool (`createJiraIssue`) with:
- Project: `RF`
- Issue type: `Task`
- Summary: `Retire Celery/Redis ingestion worker for Cloud Run Jobs (budget fix, supersedes ADR-013/015)`
- Description: reference `docs/superpowers/specs/2026-07-12-cloud-run-jobs-ingestion-design.md`, the ₹1000/month budget cap, and that ADR-013/015's always-on worker cost ~8.5x that.

Record the returned key (expected `RF-92` given RF-91 is the last-used key, but confirm the actual returned key and use it for all subsequent steps/commits in this plan instead of assuming).

- [ ] **Step 2: Create three subtasks under the parent**, story points per `.agents/conventions/jira-workflow.md`'s 1–2 point scale:
  1. "Build the Cloud Run Job ingestion path (pipeline module, trigger, entrypoint, router swap)" — 2 points
  2. "Deploy pipeline change + IAM/ADR + live verification" — 2 points
  3. "Remove Celery/Redis worker code and dependencies" — 1 point

- [ ] **Step 3: Transition the parent and first subtask to "In Progress"**

Use the JIRA MCP tool (`transitionJiraIssue`) on the parent and subtask 1.

---

### Task 2: Add settings and dependencies

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/requirements.txt`
- Test: `backend/tests/test_config.py` (create if it doesn't already exist as a dedicated file — check first with a repo search; if settings are tested inline elsewhere, add to that location instead)

**Interfaces:**
- Produces: `settings.gcp_project_id: str` (default `""`), `settings.gcp_region: str` (default `"asia-south1"`), `settings.ingest_job_name: str` (default `"recruitflow-ingest"`) — consumed by Task 4's `ingestion_trigger.py`.

- [ ] **Step 1: Check for an existing config test file**

Run: `find backend/tests -iname "*config*"` (or equivalent) to see if settings already have dedicated tests. If none exists, Step 2's test goes in a new `backend/tests/test_config.py`; if one exists, add to it instead of creating a duplicate.

- [ ] **Step 2: Write the failing test**

```python
from app.core.config import Settings


def test_gcp_settings_have_sensible_defaults():
    s = Settings(_env_file=None)
    assert s.gcp_project_id == ""
    assert s.gcp_region == "asia-south1"
    assert s.ingest_job_name == "recruitflow-ingest"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_config.py -v` (or the file chosen in Step 1)
Expected: FAIL with `AttributeError` or pydantic validation error — `gcp_project_id` doesn't exist yet.

- [ ] **Step 3: Add the settings**

In `backend/app/core/config.py`, add after the `sentry_dsn_backend` line:

```python
    # RF-92: which GCP project/region/job to invoke for ingestion. Empty
    # gcp_project_id (the default, and what local/test use) means
    # trigger_ingestion() calls the pipeline directly in-process instead of
    # dispatching a real Cloud Run Job - see app/core/ingestion_trigger.py.
    gcp_project_id: str = ""
    gcp_region: str = "asia-south1"
    ingest_job_name: str = "recruitflow-ingest"
```

Also remove the now-unused `redis_url` field (it will have no remaining callers after Task 9, but leave it in place until Task 9 — Celery still imports it until then). **Do not remove `redis_url` in this task.**

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Add the `google-cloud-run` dependency**

Run: `pip index versions google-cloud-run` and note the latest stable version returned.

Add to `backend/requirements.txt`, alphabetically placed near the other `google`-prefixed or client-library entries (there are none yet — place it near `qdrant-client` since both are external service clients):

```
google-cloud-run==<version from pip index versions>
```

Do NOT remove `celery==5.4.0` or `redis==5.1.1` yet — Task 9 removes those once the old path is deleted.

- [ ] **Step 6: Install and verify the app still boots**

Run: `cd backend && pip install -r requirements.txt && python -c "import app.main"`
Expected: no import errors.

- [ ] **Step 7: Commit**

```bash
git add backend/app/core/config.py backend/requirements.txt backend/tests/test_config.py
git commit -m "feat(config): add GCP job-trigger settings for Cloud Run Jobs ingestion RF-92"
```

---

### Task 3: Move the ingestion pipeline to a shared, Celery-free module

**Files:**
- Create: `backend/app/core/ingestion_pipeline.py`
- Modify: `backend/app/worker.py` (import `run_ingestion_pipeline` from the new location instead of defining it — keeps the Celery task working unchanged until Task 9 removes it)
- Test: `backend/tests/test_ingestion_pipeline.py` (new file — ports the three `_run_ingestion_pipeline`-testing cases out of `backend/tests/test_worker.py`)

**Interfaces:**
- Consumes: nothing new (same extractor/auto_tagger/chunker/embeddings calls `_run_ingestion_pipeline` already made in `worker.py`).
- Produces: `async def run_ingestion_pipeline(document_id: str) -> str` (renamed from the private `_run_ingestion_pipeline` — it's now a shared public entrypoint, not a `worker.py`-private helper). Returns `"completed"`, `"failed"`, or `"not_found"`. Consumed by Task 4 (`ingestion_trigger.py`'s local-dev fallback) and Task 5 (`ingest_once.py`).

- [ ] **Step 1: Read the current implementation**

Read `backend/app/worker.py` in full (already fetched during design — it contains the RF-89 model-registration imports at module level, then `_run_ingestion_pipeline`'s body doing extract → auto-tag → chunk → embed, persisting `doc.status` at each stage). Copy its exact body — do not paraphrase or "improve" it, this logic is already RF-89/RF-58-verified correct.

- [ ] **Step 2: Write the failing test**

Create `backend/tests/test_ingestion_pipeline.py`, porting the three pipeline tests from `backend/tests/test_worker.py` (`test_pipeline_persists_doc_chunks_with_qdrant_point_ids`, `test_pipeline_marks_document_failed_on_extraction_failure`, `test_pipeline_marks_document_failed_on_unexpected_exception`), changing only the import line and the patch targets' module path:

```python
"""Tests for the shared ingestion pipeline (RF-92: moved out of worker.py)."""

import uuid
from unittest.mock import patch, AsyncMock

import pytest

from app.core.ingestion_pipeline import run_ingestion_pipeline
from app.modules.auth.models import User
from app.modules.clients.models import Client
from app.modules.documents.chunker import chunk_document
from app.modules.documents.models import Document
from app.modules.documents.service import get_document_chunks


async def _create_test_document(db_session, **overrides) -> Document:
    user = User(
        email=f"{uuid.uuid4()}@example.com",
        full_name="Test User",
        hashed_password="x",
    )
    db_session.add(user)
    await db_session.flush()

    client_row = Client(user_id=user.id, name="Test Client")
    db_session.add(client_row)
    await db_session.flush()

    fields = dict(
        title="Policy",
        doc_type="policy",
        file_path="documents/x/x.pdf",
        file_name="policy.pdf",
    )
    fields.update(overrides)
    doc = Document(client_id=client_row.id, user_id=user.id, **fields)
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc


@pytest.mark.anyio
async def test_pipeline_persists_doc_chunks_with_qdrant_point_ids(db_session):
    """RF-57: after ingestion, each chunk must be persisted as a DocChunk row
    carrying the exact Qdrant point ID embed_and_store_chunks returned for it,
    so RF-58's delete/re-ingest flow can find the points to remove."""
    doc = await _create_test_document(
        db_session,
        extracted_text="Paragraph one.\n\n" + ("filler " * 600) + "\n\nParagraph two.",
    )

    expected_chunks = chunk_document(doc)
    assert len(expected_chunks) > 1
    fake_point_ids = [uuid.uuid4() for _ in expected_chunks]

    with (
        patch(
            "app.modules.documents.extractor.extract_document_text",
            new=AsyncMock(return_value=doc.extracted_text),
        ),
        patch(
            "app.modules.documents.auto_tagger.auto_tag_document_text",
            new=AsyncMock(return_value={}),
        ),
        patch(
            "app.core.embeddings.embed_and_store_chunks",
            new=AsyncMock(return_value=fake_point_ids),
        ),
    ):
        await run_ingestion_pipeline(str(doc.id))

    persisted = await get_document_chunks(db_session, doc.id)
    assert [c.qdrant_point_id for c in persisted] == fake_point_ids
    assert [c.chunk_index for c in persisted] == [
        c["chunk_index"] for c in expected_chunks
    ]
    assert [c.chunk_text for c in persisted] == [
        c["chunk_text"] for c in expected_chunks
    ]

    await db_session.refresh(doc)
    assert doc.status == "completed"


@pytest.mark.anyio
async def test_pipeline_marks_document_failed_on_extraction_failure(db_session):
    """RF-58: a failed extraction step must leave the document status as
    'failed', not silently stuck wherever it last was."""
    doc = await _create_test_document(db_session)
    assert doc.status == "uploaded"

    with patch(
        "app.modules.documents.extractor.extract_document_text",
        new=AsyncMock(return_value=None),
    ):
        await run_ingestion_pipeline(str(doc.id))

    await db_session.refresh(doc)
    assert doc.status == "failed"


@pytest.mark.anyio
async def test_pipeline_marks_document_failed_on_unexpected_exception(db_session):
    """RF-58: an exception anywhere in the pipeline (e.g. the embedding call
    blowing up) must still land the document in 'failed', and propagate so
    the caller's own retry logic (Cloud Run Job --max-retries as of RF-92)
    still sees it."""
    doc = await _create_test_document(db_session, extracted_text="Some text.")

    with (
        patch(
            "app.modules.documents.extractor.extract_document_text",
            new=AsyncMock(return_value=doc.extracted_text),
        ),
        patch(
            "app.modules.documents.auto_tagger.auto_tag_document_text",
            new=AsyncMock(return_value={}),
        ),
        patch(
            "app.core.embeddings.embed_and_store_chunks",
            new=AsyncMock(side_effect=RuntimeError("qdrant is down")),
        ),
        pytest.raises(RuntimeError),
    ):
        await run_ingestion_pipeline(str(doc.id))

    await db_session.refresh(doc)
    assert doc.status == "failed"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && pytest tests/test_ingestion_pipeline.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.core.ingestion_pipeline'`

- [ ] **Step 4: Create `app/core/ingestion_pipeline.py`**

Move the RF-89 model-registration imports and the pipeline body out of `worker.py` verbatim, renaming `_run_ingestion_pipeline` to `run_ingestion_pipeline`:

```python
"""Shared document ingestion pipeline.

RF-92: extracted out of the Celery-specific worker.py so both the Cloud Run
Job entrypoint (app/ingest_once.py) and ingestion_trigger.py's local-dev
fallback can call it without depending on Celery.
"""

import logging

from sqlalchemy import select

# RF-89: whatever process calls run_ingestion_pipeline() first (Celery's
# worker.py previously, app/ingest_once.py now) must import these for their
# side effect of populating SQLAlchemy's declarative registry before the
# first query compiles a FK against them - app.main's router imports do
# this for FastAPI, but neither the old Celery entrypoint nor the new Job
# entrypoint import app.main. Do not remove as unused.
from app.modules.auth import models as _auth_models  # noqa: F401
from app.modules.clients import models as _client_models  # noqa: F401
from app.modules.documents import models as _document_models  # noqa: F401

logger = logging.getLogger(__name__)


async def run_ingestion_pipeline(document_id: str) -> str:
    """Run the full ingestion pipeline for a document: extract -> auto-tag
    -> chunk -> embed. Returns the document's final status string
    ('completed', 'failed', or 'not_found')."""
    # <PASTE THE EXACT BODY OF worker.py's _run_ingestion_pipeline HERE -
    # this plan does not repeat it verbatim to avoid drift from whatever
    # RF-89/RF-58 last shipped; copy it byte-for-byte from worker.py during
    # this step, changing only the function name in its own signature line
    # and any internal self-recursive references (there should be none).>
```

**Do not write new pipeline logic** — the comment above is an instruction to copy, not a placeholder for new behavior. Read `backend/app/worker.py`'s current `_run_ingestion_pipeline` body in full before this step and transplant it exactly.

- [ ] **Step 5: Update `worker.py` to import from the new location**

In `backend/app/worker.py`, remove the model-registration imports and the `_run_ingestion_pipeline` function body (now living in `ingestion_pipeline.py`), and add:

```python
from app.core.ingestion_pipeline import run_ingestion_pipeline as _run_ingestion_pipeline
```

placed where the old function definition was, so `ingest_document`'s `asyncio.run(_run_ingestion_pipeline(document_id))` call keeps working unchanged (the local alias preserves the existing name so this task's diff to `worker.py` is minimal — just import shuffling, not touching the Celery task body at all).

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && pytest tests/test_ingestion_pipeline.py -v`
Expected: PASS (all 3 tests)

- [ ] **Step 7: Run the full existing test suite to confirm nothing broke**

Run: `cd backend && pytest tests/ -v`
Expected: PASS. `test_worker.py`'s three pipeline tests will now be **duplicates** of the ones just added (they still pass, since `worker.py` still re-exports the same function under its old name) — that's expected and fine; Task 9 deletes `test_worker.py` entirely once the old path is removed. Do not delete it yet.

- [ ] **Step 8: Commit**

```bash
git add backend/app/core/ingestion_pipeline.py backend/app/worker.py backend/tests/test_ingestion_pipeline.py
git commit -m "refactor: extract ingestion pipeline out of worker.py into a shared module RF-92"
```

---

### Task 4: Build `trigger_ingestion()` with the local/prod branch

**Files:**
- Create: `backend/app/core/ingestion_trigger.py`
- Test: `backend/tests/test_ingestion_trigger.py`

**Interfaces:**
- Consumes: `settings.gcp_project_id`, `settings.gcp_region`, `settings.ingest_job_name` (Task 2), `run_ingestion_pipeline` (Task 3).
- Produces: `async def trigger_ingestion(document_id: str) -> None` — consumed by Task 6 (`documents/router.py`).

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for RF-92's ingestion trigger: local direct-call vs real Cloud Run Job dispatch."""

from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from app.core.ingestion_trigger import trigger_ingestion


@pytest.mark.anyio
async def test_trigger_calls_pipeline_directly_when_no_gcp_project_configured():
    """Local/test default: gcp_project_id is empty, so trigger_ingestion
    must call the pipeline in-process rather than trying to reach GCP."""
    with (
        patch("app.core.ingestion_trigger.settings") as mock_settings,
        patch(
            "app.core.ingestion_trigger.run_ingestion_pipeline",
            new=AsyncMock(return_value="completed"),
        ) as mock_pipeline,
    ):
        mock_settings.gcp_project_id = ""
        await trigger_ingestion("doc-123")

    mock_pipeline.assert_awaited_once_with("doc-123")


@pytest.mark.anyio
async def test_trigger_dispatches_cloud_run_job_when_gcp_project_configured():
    """Production: gcp_project_id set, must call JobsAsyncClient.run_job
    with the document_id passed as a container env override, and must NOT
    call the pipeline directly (that would defeat the whole point of
    dispatching to a separate Job)."""
    mock_client = MagicMock()
    mock_client.run_job = AsyncMock()

    with (
        patch("app.core.ingestion_trigger.settings") as mock_settings,
        patch(
            "app.core.ingestion_trigger.run_ingestion_pipeline",
            new=AsyncMock(),
        ) as mock_pipeline,
        patch(
            "app.core.ingestion_trigger.run_v2.JobsAsyncClient",
            return_value=mock_client,
        ),
    ):
        mock_settings.gcp_project_id = "recruitflow-ai-500719"
        mock_settings.gcp_region = "asia-south1"
        mock_settings.ingest_job_name = "recruitflow-ingest"

        await trigger_ingestion("doc-456")

    mock_pipeline.assert_not_awaited()
    mock_client.run_job.assert_awaited_once()
    request = mock_client.run_job.call_args.kwargs["request"]
    assert request.name == (
        "projects/recruitflow-ai-500719/locations/asia-south1/jobs/recruitflow-ingest"
    )
    env_override = request.overrides.container_overrides[0].env[0]
    assert env_override.name == "DOCUMENT_ID"
    assert env_override.value == "doc-456"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/test_ingestion_trigger.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.core.ingestion_trigger'`

- [ ] **Step 3: Write the implementation**

```python
"""RF-92: dispatch ingestion to a Cloud Run Job in production, or call the
pipeline directly in-process for local dev/tests (no real GCP call)."""

import logging

from google.cloud import run_v2

from app.core.config import settings
from app.core.ingestion_pipeline import run_ingestion_pipeline

logger = logging.getLogger(__name__)


async def trigger_ingestion(document_id: str) -> None:
    if not settings.gcp_project_id:
        # Local dev / tests: no GCP project configured, so run the pipeline
        # directly instead of trying to reach a real Cloud Run Job. This
        # blocks the calling request until ingestion finishes, which is
        # fine for local single-user dev and is never hit in production
        # (gcp_project_id is always set there via Doppler).
        await run_ingestion_pipeline(document_id)
        return

    client = run_v2.JobsAsyncClient()
    job_name = (
        f"projects/{settings.gcp_project_id}/locations/{settings.gcp_region}"
        f"/jobs/{settings.ingest_job_name}"
    )
    request = run_v2.RunJobRequest(
        name=job_name,
        overrides=run_v2.RunJobRequest.Overrides(
            container_overrides=[
                run_v2.RunJobRequest.Overrides.ContainerOverride(
                    env=[run_v2.EnvVar(name="DOCUMENT_ID", value=document_id)]
                )
            ]
        ),
    )
    # run_job returns once the execution is CREATED, not once it finishes -
    # this is the async equivalent of Celery's old .delay() fire-and-forget
    # dispatch, not a blocking wait for ingestion to complete.
    await client.run_job(request=request)
    logger.info(f"Dispatched Cloud Run Job execution for document {document_id}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_ingestion_trigger.py -v`
Expected: PASS

If the second test fails on the exact `request.overrides.container_overrides[...]` attribute path (the `google-cloud-run` client's generated message field names can differ slightly by version), inspect the actual installed version's `RunJobRequest`/`Overrides`/`ContainerOverride` field names via `python -c "from google.cloud import run_v2; help(run_v2.RunJobRequest.Overrides)"` and adjust both the implementation and test to match — this is exactly the kind of thing to verify against the installed library, not assume.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/ingestion_trigger.py backend/tests/test_ingestion_trigger.py
git commit -m "feat: add trigger_ingestion for Cloud Run Job dispatch RF-92"
```

---

### Task 5: Build the Job entrypoint (`ingest_once.py`) and port the FK-registration regression test

**Files:**
- Create: `backend/app/ingest_once.py`
- Test: `backend/tests/test_ingest_once.py`

**Interfaces:**
- Consumes: `run_ingestion_pipeline` (Task 3).
- Produces: a standalone script, invoked as `python -m app.ingest_once`, reading `DOCUMENT_ID` from the environment. Consumed by Task 7's deploy step (`--command=python --args=-m,app.ingest_once`).

- [ ] **Step 1: Write the failing test**

Port `test_worker.py`'s subprocess-isolated FK-registration test, targeting the new module:

```python
"""Tests for RF-92's Cloud Run Job entrypoint."""

import subprocess
import sys
from pathlib import Path


def test_ingest_once_module_resolves_foreign_keys_in_isolation():
    """RF-89/RF-92: the real Job entrypoint (`python -m app.ingest_once`)
    must resolve Document.user_id's FK to users without ever importing
    app.main - reproduces the exact NoReferencedTableError RF-89 fixed,
    now against the new entrypoint instead of the retired Celery one."""
    backend_dir = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import app.ingest_once; from app.modules.documents.models import Document; "
            "list(Document.__table__.c.user_id.foreign_keys)[0].column",
        ],
        cwd=str(backend_dir),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_ingest_once_exits_nonzero_without_document_id_env_var(monkeypatch):
    """The Job entrypoint must fail loudly (nonzero exit -> Cloud Run Jobs
    marks the execution Failed and retries per --max-retries) rather than
    silently no-op if DOCUMENT_ID wasn't set as a container override."""
    backend_dir = Path(__file__).resolve().parent.parent
    import os

    env = {k: v for k, v in os.environ.items() if k != "DOCUMENT_ID"}
    result = subprocess.run(
        [sys.executable, "-m", "app.ingest_once"],
        cwd=str(backend_dir),
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode != 0
    assert "DOCUMENT_ID" in result.stderr
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/test_ingest_once.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.ingest_once'`

- [ ] **Step 3: Write the implementation**

```python
"""RF-92: Cloud Run Job entrypoint for document ingestion.

Invoked as `python -m app.ingest_once` by the recruitflow-ingest Job,
triggered per upload via app/core/ingestion_trigger.py. Reads DOCUMENT_ID
from the environment (set as a per-execution container override, not baked
into the job's static config) and runs the shared ingestion pipeline once.
"""

import asyncio
import logging
import os
import sys

from app.core.ingestion_pipeline import run_ingestion_pipeline

logger = logging.getLogger(__name__)


def main() -> int:
    document_id = os.environ.get("DOCUMENT_ID")
    if not document_id:
        print("DOCUMENT_ID environment variable is required", file=sys.stderr)
        return 1

    final_status = asyncio.run(run_ingestion_pipeline(document_id))
    if final_status != "completed":
        logger.error(
            f"Ingestion did not complete for document {document_id}: "
            f"status={final_status}"
        )
        return 1

    logger.info(f"Ingestion complete for document {document_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_ingest_once.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/ingest_once.py backend/tests/test_ingest_once.py
git commit -m "feat: add Cloud Run Job entrypoint for ingestion RF-92"
```

---

### Task 6: Swap the router's dispatch call

**Files:**
- Modify: `backend/app/modules/documents/router.py:1-25` (imports), and the `upload_document` handler (currently ends with `ingest_document.delay(str(document.id))`)
- Modify: `backend/tests/test_documents.py` (find and update whatever test currently asserts `.delay` was called on upload)

**Interfaces:**
- Consumes: `trigger_ingestion` (Task 4).

- [ ] **Step 1: Find the existing upload test asserting Celery dispatch**

Run: `grep -n "delay\|ingest_document" backend/tests/test_documents.py`

Read the matched test(s) in full before editing — likely something like `mock_ingest.delay.assert_called_once_with(...)` patching `app.modules.documents.router.ingest_document`.

- [ ] **Step 2: Update the failing test first**

Change the patch target from `app.modules.documents.router.ingest_document` to `app.modules.documents.router.trigger_ingestion`, and the assertion from `.delay.assert_called_once_with(str(doc_id))` to an async-aware assertion, e.g.:

```python
@patch("app.modules.documents.router.trigger_ingestion", new_callable=AsyncMock)
async def test_upload_triggers_ingestion(mock_trigger, ...):
    # ... existing upload request setup ...
    response = await client.post("/upload", ...)
    assert response.status_code == 201
    mock_trigger.assert_awaited_once_with(str(created_document_id))
```

Adapt exactly to whatever the existing test's fixture/assertion style already is in `test_documents.py` — do not introduce a different test structure than the file already uses.

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && pytest tests/test_documents.py -k upload -v`
Expected: FAIL (still patching/asserting the old Celery call, or `trigger_ingestion` doesn't exist in router.py yet).

- [ ] **Step 4: Update the router**

In `backend/app/modules/documents/router.py`, change:

```python
from app.worker import ingest_document
```

to:

```python
from app.core.ingestion_trigger import trigger_ingestion
```

And change the upload handler's dispatch line from:

```python
    # Trigger async ingestion via Celery
    ingest_document.delay(str(document.id))
```

to:

```python
    # Trigger ingestion via Cloud Run Job (RF-92)
    await trigger_ingestion(str(document.id))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_documents.py -k upload -v`
Expected: PASS

- [ ] **Step 6: Run the full test suite**

Run: `cd backend && pytest tests/ -v`
Expected: PASS. `backend/app/worker.py` still exists and is still imported by `test_worker.py`, but nothing in the live request path calls it anymore.

- [ ] **Step 7: Commit**

```bash
git add backend/app/modules/documents/router.py backend/tests/test_documents.py
git commit -m "feat: dispatch ingestion via Cloud Run Job instead of Celery RF-92"
```

---

### Task 7: Deploy workflow change and ADR-016

**Files:**
- Modify: `.github/workflows/backend-deploy.yml`
- Create: append to `docs/ADR.md`

**Interfaces:** None (infra/docs only).

- [ ] **Step 1: Replace the "Deploy Celery worker to Cloud Run" step**

In `.github/workflows/backend-deploy.yml`, replace the entire `Deploy Celery worker to Cloud Run` step (the one running `gcloud run deploy recruitflow-worker ...`) with:

```yaml
      - name: Deploy ingestion Cloud Run Job
        # RF-92: replaces the always-on recruitflow-worker Service (Celery
        # polling Redis, ADR-013/015) with a Job invoked once per upload via
        # app/core/ingestion_trigger.py - pay-per-execution instead of an
        # always-on instance, since Celery's poll-based consumer required
        # min-instances=1 + no-cpu-throttling to work reliably, which cost
        # ~8.5x the project's ₹1000/month budget cap. Jobs don't take
        # --min-instances or --no-cpu-throttling (they don't apply to
        # pay-per-execution resources) and always get full CPU during their
        # run, so RF-91's CPU-starvation bug structurally cannot recur here.
        # Same image as the API and migration job, different entrypoint -
        # no separate Dockerfile needed, same pattern as recruitflow-migrate.
        # --service-account explicit for the same first-creation reason as
        # the migration job: a brand-new Job has no prior revision to
        # inherit a runtime identity from. recruitflow-agents already has
        # roles/run.developer at the project level (includes run.jobs.run),
        # so recruitflow-backend can invoke this job with no further IAM
        # grant - verified live 2026-07-13, do not add a speculative grant.
        run: |
          if gcloud run jobs describe recruitflow-ingest --region=asia-south1 --project=recruitflow-ai-500719 >/dev/null 2>&1; then
            ACTION=update
          else
            ACTION=create
          fi
          gcloud run jobs $ACTION recruitflow-ingest \
            --image=asia-south1-docker.pkg.dev/recruitflow-ai-500719/recruitflow/backend:${{ github.sha }} \
            --region=asia-south1 \
            --project=recruitflow-ai-500719 \
            --service-account=recruitflow-agents@recruitflow-ai-500719.iam.gserviceaccount.com \
            --set-cloudsql-instances=recruitflow-ai-500719:asia-south1:recruitflow-db \
            --env-vars-file=/tmp/prod-env-vars.yaml \
            --command=python \
            --args=-m,app.ingest_once \
            --max-retries=3 \
            --task-timeout=600
```

Leave the old `recruitflow-worker` Service deploy step's surrounding structure otherwise untouched for now if any other step depends on its output — check for that before removing; if none, this replacement is the only change to this file in this task (Task 9 will additionally add a one-off cleanup step to delete the `recruitflow-worker` service itself, not in this task).

- [ ] **Step 2: Validate the workflow YAML locally**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/backend-deploy.yml'))"`
Expected: no exception (valid YAML).

- [ ] **Step 3: Write ADR-016**

Append to `docs/ADR.md`:

```markdown
## ADR-016 - Retire Celery/Redis Worker for Cloud Run Jobs (supersedes ADR-013, ADR-015)
Date: 2026-07-13
Status: Accepted
Agent: Implementer (Claude Code), RF-92

Decision:
`recruitflow-worker` (the always-on Celery/Redis polling Service) is
retired. Ingestion is now dispatched via `recruitflow-ingest`, a Cloud Run
Job invoked directly per upload through the Cloud Run Admin API
(`app/core/ingestion_trigger.py`), running `python -m app.ingest_once`
against the same backend image. Celery and Redis (Upstash) are fully
removed from the ingestion path - see RF-92's task list for the exact
files removed.

Reasoning:
ADR-013 (`--min-instances=1`) and ADR-015 (`--no-cpu-throttling`) fixed
RF-89/91's reliability bugs but cost an estimated ~₹8,500/month - roughly
8.5x the project's standing ₹1000/month GCP budget cap, discovered and
confirmed by the owner on 2026-07-12. Both were accepted live, mid-incident,
without checking the budget - a process gap now called out explicitly in
`.agents/roles/implementer.md`'s cost-affecting-changes rule.

The root cause is structural, not a tuning problem: Celery consumes jobs by
continuously polling a Redis broker, which requires an always-on,
always-listening instance - fundamentally incompatible with Cloud Run's
scale-to-zero pricing model at any flag setting. Cloud Run Jobs, invoked
directly from the upload endpoint, remove the always-on requirement
entirely: no broker, no polling consumer, pay only for actual execution
seconds. At the confirmed volume (~100 docs/month), this is estimated at
~₹30-60/month.

A push-based alternative (Cloud Tasks -> authenticated Cloud Run Service)
was considered and rejected for now: it would add a new GCP product (a
queue) and a new authenticated internal HTTP endpoint's attack surface for
retry/backoff sophistication this project doesn't need at its current
volume. Revisit if volume grows enough that Cloud Run Jobs' coarser
whole-container retry (vs Cloud Tasks' configurable backoff) becomes a
real problem.

Consequences:
Ingestion now cold-starts on every single document (no warm-instance reuse
across bursts) - acceptable at current volume, and specifically *desired*
behavior for a pay-per-execution resource (a warm Job would just be a
Service with extra steps). RF-91's CPU-throttling bug cannot recur:
Cloud Run Jobs always get full CPU during their run, unlike a Service
under default throttling. If ingestion volume grows enough that per-upload
cold start latency or Cloud Run Jobs' retry model becomes limiting, the
Cloud Tasks alternative above is the documented next step, not another
tuning pass on Job flags.
```

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/backend-deploy.yml docs/ADR.md
git commit -m "chore(deploy): switch ingestion to Cloud Run Job, add ADR-016 RF-92"
```

---

### Task 8: Deploy and live-verify (manual — not TDD code)

**Files:** None (this task is deploy + verification against real production, following the exact pattern RF-89/90/91 already established).

- [ ] **Step 1: Push the branch and open the PR**

```bash
git push -u origin feature/RF-92-cloud-run-jobs-ingestion
gh pr create --base main --title "feat: retire Celery/Redis worker for Cloud Run Jobs RF-92" --body "..."
```

Body should summarize the change, link the design spec and ADR-016, and note the deliberate two-phase rollout (this PR wires the new path in and deploys `recruitflow-ingest`; a follow-up PR removes the now-dead `recruitflow-worker` Service and Celery code once this is live-verified).

- [ ] **Step 2: Wait for CI to pass**

`backend-ci`, `frontend-ci`, `security` must all be green (branch protection requires this on `main`).

- [ ] **Step 3: Merge and wait for the deploy workflow**

Once merged, `backend-deploy.yml` runs automatically (push to `main`, `backend/**` changed). Confirm via `gh run list --branch main --limit 5` that `Deploy Backend to Cloud Run` succeeds, and that `recruitflow-ingest` now exists: `gcloud run jobs describe recruitflow-ingest --region=asia-south1 --project=recruitflow-ai-500719`.

- [ ] **Step 4: Run the live smoke test**

```bash
python scripts/smoke_test_ingestion.py --base-url https://recruitflow-backend-x6sbyylkwq-el.a.run.app
```

Expected output ends with `[smoke] PASS: worker picked up and completed the queued ingestion job` — same pass criterion RF-89/90/91 already used, now exercising the new Job path instead of the old Celery worker.

- [ ] **Step 5: If it fails, fix forward — do not immediately revert**

`recruitflow-worker` (the old Service) is still deployed and untouched at this point per the Global Constraints — if `trigger_ingestion`'s live dispatch has a bug (e.g. the `google-cloud-run` request schema mismatch flagged as a risk in Task 4), the fastest safe fix is correcting `ingestion_trigger.py` and redeploying, not reverting to Celery (that would just reintroduce the ₹8,500/month cost this whole task exists to remove). Only revert if a fix isn't achievable within a reasonable session.

- [ ] **Step 6: Confirm in JIRA**

Transition subtask 2 ("Deploy pipeline change + IAM/ADR + live verification") to Done, with a comment citing the smoke test's pass output — same evidence format RF-89/90/91 used in their closing comments.

---

### Task 9: Remove Celery/Redis (only after Task 8 passes)

**Files:**
- Delete: `backend/app/worker.py`
- Delete: `backend/worker-entrypoint.sh`
- Delete: `backend/app/worker_health.py`
- Delete: `backend/tests/test_worker.py`
- Modify: `backend/app/core/config.py` (remove `redis_url`)
- Modify: `backend/requirements.txt` (remove `celery`, `redis`)
- Modify: `.github/workflows/backend-deploy.yml` (remove any leftover worker-Service-specific step/comment not already replaced in Task 7)

**Interfaces:** None (pure removal — nothing left in the codebase references any of these after Task 6).

- [ ] **Step 1: Confirm nothing still references the files being deleted**

Run: `grep -rn "from app.worker import\|app\.worker\b\|worker-entrypoint\|worker_health" backend/ --include=*.py --include=*.sh --include=*.yml`

Expected: only matches inside the files about to be deleted themselves (and this plan/ADR-016's own prose, which isn't code). If anything else matches, stop and investigate before deleting.

- [ ] **Step 2: Delete the files**

```bash
git rm backend/app/worker.py backend/worker-entrypoint.sh backend/app/worker_health.py backend/tests/test_worker.py
```

- [ ] **Step 3: Remove `redis_url` from config.py**

In `backend/app/core/config.py`, delete the line:
```python
    redis_url: str = "redis://localhost:6379/0"
```

- [ ] **Step 4: Remove Celery/Redis from requirements.txt**

Delete these two lines from `backend/requirements.txt`:
```
celery==5.4.0
redis==5.1.1
```

- [ ] **Step 5: Run the full test suite**

Run: `cd backend && pytest tests/ -v`
Expected: PASS, with `test_worker.py`'s tests gone (their coverage now lives in `test_ingestion_pipeline.py` and `test_ingest_once.py` from Tasks 3 and 5).

- [ ] **Step 6: Run mypy and bandit**

Run: `cd backend && mypy app --ignore-missing-imports && bandit -r app -ll`
Expected: both clean.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore: remove Celery/Redis worker code, now replaced by Cloud Run Jobs RF-92"
```

- [ ] **Step 8: Delete the live `recruitflow-worker` Cloud Run service and the `REDIS_URL` Doppler secret**

```bash
gcloud run services delete recruitflow-worker --region=asia-south1 --project=recruitflow-ai-500719 --quiet
```

Then remove `REDIS_URL` from the `prd` Doppler config via the Doppler dashboard or CLI (owner action if CLI access isn't available in the session) — this is the step that actually stops the ~₹8,500/month billing; deleting the code alone doesn't stop a still-running Service.

- [ ] **Step 9: Push, open PR, merge**

```bash
git push -u origin feature/RF-92-cloud-run-jobs-ingestion
gh pr create --base main --title "chore: remove Celery/Redis worker, replaced by Cloud Run Jobs RF-92" --body "Follow-up to the already-merged/deployed Cloud Run Job migration (live-verified via smoke test). Removes the now-dead recruitflow-worker Service and Celery/Redis code."
```

Wait for CI, merge.

- [ ] **Step 10: Final JIRA close-out**

Run the `/story-complete` skill (per this project's convention) for the parent RF-92 and subtask 3, with the signed completion comment citing: PR links, the smoke test pass evidence, the deleted `recruitflow-worker` service, and the final cost figure (~₹30–60/month for ingestion, down from ~₹8,500/month).

---

## Self-Review Notes

- **Spec coverage:** every "Components changed" bullet in the design spec maps to a task above (new `ingest_once.py`/`ingestion_trigger.py` → Tasks 4–5; router swap → Task 6; deploy workflow → Task 7; removed Celery/Redis/Service → Task 9; new ADR → Task 7; ported regression test → Task 5; testing approach for `trigger_ingestion` mocking → Task 4/6).
- **Known verification risk, flagged not hidden:** the exact `google-cloud-run` `RunJobRequest.Overrides` field names (Task 4) are written from general knowledge of the client library's shape, not verified against a live install in this planning session. Task 4 Step 4 and Task 8 Step 4/5 both explicitly call out checking this against the real installed version and fixing forward rather than assuming it's correct.
- **IAM:** verified live (not assumed) that no new grant is needed — `recruitflow-agents` already has `roles/run.developer` project-wide. Documented in Global Constraints so no task speculatively adds a redundant grant.
- **Rollout safety:** old Celery/worker code and the `recruitflow-worker` Service are explicitly left untouched through Task 8, deleted only in Task 9 after live verification — matches the design spec's requirement.
