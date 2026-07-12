"""HTTP health-check listener for the Celery worker's Cloud Run service.

RF-55: replaces a plain `python -m http.server` (which only proved *some*
process was bound to $PORT, not that Celery itself was alive) with a check
backed by `celery_app.control.ping()` - a real round-trip over the broker
to the running worker.
"""

import http.server
import os
import socketserver

from app.worker import celery_app


def check_worker_health(timeout: float = 3.0) -> bool:
    try:
        pong = celery_app.control.ping(timeout=timeout)
    except Exception:
        return False
    return bool(pong)


class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        ok = check_worker_health()
        self.send_response(200 if ok else 503)
        self.end_headers()
        self.wfile.write(b"ok" if ok else b"unhealthy")

    def log_message(self, *args: object) -> None:
        pass


def main() -> None:
    port = int(os.environ.get("PORT", 8080))
    with socketserver.TCPServer(("0.0.0.0", port), HealthHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
