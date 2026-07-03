"""Tests for Celery worker and ingestion pipeline."""

from unittest.mock import patch

from app.worker import ingest_document, celery_app


def test_celery_app_config():
    """Celery app should be configured with Redis broker."""
    assert celery_app.conf.broker_url is not None
    assert celery_app.conf.task_serializer == "json"


def test_ingest_task_registered():
    """ingest_document should be registered as a Celery task."""
    assert "ingest_document" in celery_app.tasks


@patch("app.worker._run_ingestion_pipeline")
def test_ingest_document_calls_pipeline(mock_pipeline):
    """ingest_document task should call the async pipeline."""
    result = ingest_document("test-doc-id")
    assert result["status"] == "completed"
    assert result["document_id"] == "test-doc-id"
