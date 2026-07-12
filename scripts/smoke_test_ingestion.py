#!/usr/bin/env python3
"""RF-55: real end-to-end ingestion smoke test against a deployed backend.

Registers a throwaway user, creates a client, uploads a real (extractable)
PDF, and polls document status until the Celery worker finishes the job -
proving the worker actually picked up and completed a queued job, not just
that the API accepted an upload.

Usage:
    python scripts/smoke_test_ingestion.py [--base-url URL] [--timeout SECONDS]
"""

import argparse
import sys
import time
import uuid

import httpx

DEFAULT_BASE_URL = "https://recruitflow-backend-424745949201.asia-south1.run.app"

# Same minimal-but-genuinely-valid PDF fixture as backend/tests/test_extraction.py -
# real bytes the extractor can parse, so a failure here means the pipeline
# actually broke, not that mock content got rejected.
MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
    b"xref\n"
    b"0 4\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\n"
    b"startxref\n"
    b"190\n"
    b"%%EOF"
)


def run(base_url: str, timeout: float) -> bool:
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        email = f"rf55-smoke-{uuid.uuid4()}@example.com"
        password = "smoke-test-pass-123"

        print(f"[smoke] registering {email}")
        r = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "full_name": "RF-55 Smoke Test",
                "password": password,
            },
        )
        r.raise_for_status()

        r = client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        r.raise_for_status()
        headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

        print("[smoke] creating client")
        r = client.post(
            "/api/v1/clients",
            json={"name": "RF-55 Smoke Test Client"},
            headers=headers,
        )
        r.raise_for_status()
        client_id = r.json()["id"]

        print("[smoke] uploading document")
        r = client.post(
            "/api/v1/documents/upload",
            data={
                "client_id": client_id,
                "title": "RF-55 smoke test doc",
                "doc_type": "resume",
            },
            files={"file": ("smoke-test.pdf", MINIMAL_PDF, "application/pdf")},
            headers=headers,
        )
        r.raise_for_status()
        upload = r.json()
        document_id = upload["id"]
        print(f"[smoke] uploaded document {document_id}, status={upload['status']}")

        deadline = time.monotonic() + timeout
        status = None
        while time.monotonic() < deadline:
            r = client.get(f"/api/v1/documents/{document_id}/status", headers=headers)
            r.raise_for_status()
            status = r.json()["status"]
            print(f"[smoke] status={status}")
            if status in ("completed", "failed"):
                break
            time.sleep(3)

        if status == "completed":
            print("[smoke] PASS: worker picked up and completed the queued ingestion job")
            return True
        print(f"[smoke] FAIL: final status={status!r} (expected 'completed')")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()
    ok = run(args.base_url, args.timeout)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
