from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/recruitflow"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection_resumes: str = "resumes"
    qdrant_collection_jds: str = "job_descriptions"
    qdrant_collection_hr: str = "hr_documents"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    # The single source of truth for "which bucket documents live in" -
    # used for both GCS and MinIO. There used to be a second,
    # GCS-specific `gcs_bucket_name` setting that only ever fed a
    # truthiness check for client routing (never the actual bucket param),
    # and it drifting out of sync with this one caused a real prod outage
    # (NoSuchBucket) - removed in favor of gating GCS-vs-MinIO routing on
    # whether GCS HMAC credentials are actually configured.
    doc_upload_bucket: str = "recruitflow-documents"

    gcs_hmac_access_key: str = ""
    gcs_hmac_secret_key: str = ""

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # Dev/CI runs the frontend and backend over plain http on the same host
    # (different ports only), so the refresh cookie can use SameSite=Lax
    # without Secure. Production serves them from different domains
    # (Vercel + Cloud Run), which requires SameSite=None + Secure for the
    # browser to send the cookie cross-site at all. Set to true via Doppler
    # in the real production config.
    is_production: bool = False

    sentry_dsn_backend: str = ""

    # RF-92: which GCP project/region/job to invoke for ingestion. Empty
    # gcp_project_id (the default, and what local/test use) means
    # trigger_ingestion() calls the pipeline directly in-process instead of
    # dispatching a real Cloud Run Job - see app/core/ingestion_trigger.py.
    gcp_project_id: str = ""
    gcp_region: str = "asia-south1"
    ingest_job_name: str = "recruitflow-ingest"

    deepinfra_api_key: str = ""
    proxycurl_api_key: str = ""

    # RF-77: shared per-user budget for upload/reingest, since both dispatch
    # paid ingestion work (LLM/embedding calls, and a billed Cloud Run Job
    # execution once RF-92 lands).
    ingest_rate_limit_per_minute: int = 10

    # The frontend's own origin, for CORS allow_origins - NOT
    # next_public_api_base_url (that's the frontend's env var naming the
    # backend's URL, a different value entirely - see RF-70/ADR-009).
    frontend_origin: str = "http://localhost:3000"

    model_config = {"extra": "ignore"}


settings = Settings()

_PLACEHOLDER_JWT_SECRETS = {"change-me-in-production", ""}


class JWTSecretMisconfigured(RuntimeError):
    pass


def validate_jwt_secret(secret_key: str, is_production: bool) -> None:
    """RF-65: refuse to start in production with a missing/placeholder JWT
    secret - a weak/default secret lets anyone forge access tokens."""
    if not is_production:
        return
    if not secret_key or secret_key in _PLACEHOLDER_JWT_SECRETS or len(secret_key) < 32:
        raise JWTSecretMisconfigured(
            "JWT_SECRET_KEY is missing, a placeholder value, or too short "
            "(min 32 chars) - refusing to start in production. Set a real "
            "secret via Doppler."
        )
