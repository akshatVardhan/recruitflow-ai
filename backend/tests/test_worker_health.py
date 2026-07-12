from unittest.mock import patch

from app.worker_health import check_worker_health


def test_check_worker_health_true_when_worker_responds():
    with patch("app.worker_health.celery_app") as mock_app:
        mock_app.control.ping.return_value = [{"worker@host": {"ok": "pong"}}]
        assert check_worker_health() is True


def test_check_worker_health_false_when_no_worker_responds():
    with patch("app.worker_health.celery_app") as mock_app:
        mock_app.control.ping.return_value = []
        assert check_worker_health() is False


def test_check_worker_health_false_on_broker_error():
    with patch("app.worker_health.celery_app") as mock_app:
        mock_app.control.ping.side_effect = Exception("broker unreachable")
        assert check_worker_health() is False
