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
