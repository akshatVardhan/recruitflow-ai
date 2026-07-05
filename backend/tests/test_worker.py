"""Tests for Celery worker and ingestion pipeline."""

import ssl
from unittest.mock import patch

from app.worker import ingest_document, celery_app


def test_celery_app_config():
    """Celery app should be configured with Redis broker."""
    assert celery_app.conf.broker_url is not None
    assert celery_app.conf.task_serializer == "json"


def test_celery_app_configures_redis_ssl():
    """rediss:// backends (Upstash, most managed Redis) need ssl_cert_reqs set
    explicitly or the result backend raises ValueError at task-send time."""
    assert celery_app.conf.broker_use_ssl == {"ssl_cert_reqs": ssl.CERT_REQUIRED}
    assert celery_app.conf.redis_backend_use_ssl == {"ssl_cert_reqs": ssl.CERT_REQUIRED}


def test_ingest_task_registered():
    """ingest_document should be registered as a Celery task."""
    assert "ingest_document" in celery_app.tasks


@patch("app.worker._run_ingestion_pipeline")
def test_ingest_document_calls_pipeline(mock_pipeline):
    """ingest_document task should call the async pipeline."""
    result = ingest_document("test-doc-id")
    assert result["status"] == "completed"
    assert result["document_id"] == "test-doc-id"
