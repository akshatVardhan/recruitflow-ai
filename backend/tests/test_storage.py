from unittest.mock import patch

import app.core.storage as storage


def _reset_client_cache():
    storage._s3_client = None


def test_get_storage_client_uses_gcs_hmac_credentials():
    """When gcs_bucket_name is set, boto3 must be given the HMAC access/secret
    key pair (RF-56) - never the hardcoded "_" placeholder or a JSON blob."""
    _reset_client_cache()
    with patch.object(storage, "boto3") as mock_boto3, patch.object(
        storage, "settings"
    ) as mock_settings:
        mock_settings.gcs_bucket_name = "recruitflow-ai-documents"
        mock_settings.gcs_hmac_access_key = "GOOG1EFAKEACCESSID"
        mock_settings.gcs_hmac_secret_key = "fake-hmac-secret"

        storage.get_storage_client()

        _, kwargs = mock_boto3.client.call_args
        assert kwargs["endpoint_url"] == "https://storage.googleapis.com"
        assert kwargs["aws_access_key_id"] == "GOOG1EFAKEACCESSID"
        assert kwargs["aws_secret_access_key"] == "fake-hmac-secret"
    _reset_client_cache()


def test_get_storage_client_falls_back_to_minio():
    _reset_client_cache()
    with patch.object(storage, "boto3") as mock_boto3, patch.object(
        storage, "settings"
    ) as mock_settings:
        mock_settings.gcs_bucket_name = ""
        mock_settings.minio_endpoint = "localhost:9000"
        mock_settings.minio_access_key = "minioadmin"
        mock_settings.minio_secret_key = "minioadmin"
        mock_settings.minio_secure = False

        storage.get_storage_client()

        _, kwargs = mock_boto3.client.call_args
        assert kwargs["endpoint_url"] == "http://localhost:9000"
        assert kwargs["aws_access_key_id"] == "minioadmin"
    _reset_client_cache()
