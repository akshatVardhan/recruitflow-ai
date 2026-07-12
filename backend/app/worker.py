"""Celery worker configuration and ingestion tasks."""

import asyncio
import logging
import ssl

from celery import Celery

from app.core.config import settings
from app.core.ingestion_pipeline import run_ingestion_pipeline as _run_ingestion_pipeline

logger = logging.getLogger(__name__)

celery_app = Celery(
    "recruitflow",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # RF-89: with late acks and no visibility timeout, Redis redelivers an
    # unacked task fresh whenever the worker container restarts for reasons
    # unrelated to the task itself (e.g. Cloud Run cycling the instance) -
    # and each redelivery resets Celery's own per-task retry counter, so
    # max_retries=3 above never actually capped total attempts across
    # restarts. This bounds redelivery to genuinely stuck/crashed tasks
    # instead of ordinary restarts; it doesn't eliminate redelivery
    # entirely (inherent to at-least-once broker delivery). Set well above
    # a realistic worst-case ingestion run (large doc + embedding).
    broker_transport_options={"visibility_timeout": 3600},
    # Required whenever redis_url uses rediss:// (Upstash and most managed
    # Redis do) - Celery's redis result backend raises at task-send time
    # without this, even though the broker connection alone works fine.
    # No-op for plain redis:// (e.g. local fallback), safe to always set.
    broker_use_ssl={"ssl_cert_reqs": ssl.CERT_REQUIRED},
    redis_backend_use_ssl={"ssl_cert_reqs": ssl.CERT_REQUIRED},
)


@celery_app.task(
    bind=True, name="ingest_document", max_retries=3, default_retry_delay=60
)
def ingest_document(self, document_id: str):
    """Celery task: run full ingestion pipeline for a document.

    Orchestrates: extract -> auto-tag -> chunk -> embed.
    Runs inside an async event loop since all pipeline steps are async.
    """
    try:
        final_status = asyncio.run(_run_ingestion_pipeline(document_id))
        if final_status != "completed":
            # Not an exception - _run_ingestion_pipeline already persisted
            # doc.status="failed" itself (e.g. extraction yielded no text).
            # Report that here too, so this task's own return value/logs
            # don't claim "completed" for a document that's actually failed.
            logger.error(
                f"Ingestion did not complete for document {document_id}: "
                f"status={final_status}"
            )
            return {"status": final_status, "document_id": document_id}
        logger.info(f"Ingestion complete for document {document_id}")
        return {"status": "completed", "document_id": document_id}
    except Exception as e:
        logger.error(f"Ingestion failed for document {document_id}: {e}")
        self.retry(exc=e)
