import boto3
from botocore.config import Config

from app.core.config import settings

_s3_client = None


def get_storage_client():
    global _s3_client
    if _s3_client is not None:
        return _s3_client

    # botocore >=1.36 defaults to attaching S3 checksum headers/trailers
    # (CRC32 etc.) to every request - GCS's S3-compatible XML API doesn't
    # support that scheme, and including the header breaks SigV4 signing
    # with SignatureDoesNotMatch. "when_required" keeps checksums opt-in,
    # matching pre-1.36 behavior. Harmless no-op against MinIO too.
    storage_config = Config(
        signature_version="s3v4",
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    )

    if settings.gcs_bucket_name:
        _s3_client = boto3.client(
            "s3",
            region_name="auto",
            endpoint_url="https://storage.googleapis.com",
            aws_access_key_id=settings.gcs_hmac_access_key,
            aws_secret_access_key=settings.gcs_hmac_secret_key,
            config=storage_config,
        )
    else:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=f"http://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=storage_config,
            use_ssl=settings.minio_secure,
        )
    return _s3_client


async def upload_file(bucket: str, key: str, data: bytes, content_type: str) -> str:
    client = get_storage_client()
    client.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
    return key


async def download_file(bucket: str, key: str) -> bytes:
    client = get_storage_client()
    response = client.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()


async def delete_file(bucket: str, key: str) -> None:
    client = get_storage_client()
    client.delete_object(Bucket=bucket, Key=key)
