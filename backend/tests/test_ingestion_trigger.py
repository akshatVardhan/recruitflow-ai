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
