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
