from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/recruitflow"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection_resumes: str = "resumes"
    qdrant_collection_jds: str = "job_descriptions"
    qdrant_collection_hr: str = "hr_documents"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    doc_upload_bucket: str = "recruitflow-documents"

    gcs_bucket_name: str = ""
    gcs_credentials_json: str = ""

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    sentry_dsn_backend: str = ""

    litellm_api_key: str = ""
    deepinfra_api_key: str = ""
    proxycurl_api_key: str = ""

    next_public_api_base_url: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
