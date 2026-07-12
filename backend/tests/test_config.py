import pytest

from app.core.config import JWTSecretMisconfigured, Settings, validate_jwt_secret


def test_validate_jwt_secret_allows_placeholder_outside_production():
    validate_jwt_secret("change-me-in-production", is_production=False)


def test_validate_jwt_secret_rejects_placeholder_in_production():
    with pytest.raises(JWTSecretMisconfigured):
        validate_jwt_secret("change-me-in-production", is_production=True)


def test_validate_jwt_secret_rejects_empty_in_production():
    with pytest.raises(JWTSecretMisconfigured):
        validate_jwt_secret("", is_production=True)


def test_validate_jwt_secret_rejects_short_secret_in_production():
    with pytest.raises(JWTSecretMisconfigured):
        validate_jwt_secret("too-short", is_production=True)


def test_validate_jwt_secret_accepts_real_secret_in_production():
    validate_jwt_secret("a" * 40, is_production=True)


def test_gcp_settings_have_sensible_defaults():
    s = Settings(_env_file=None)
    assert s.gcp_project_id == ""
    assert s.gcp_region == "asia-south1"
    assert s.ingest_job_name == "recruitflow-ingest"
