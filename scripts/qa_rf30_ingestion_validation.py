#!/usr/bin/env python3
"""RF-30: end-to-end ingestion pipeline QA validation against a live backend.

Uploads a resume and a job description with distinctive, extractable text,
polls each to completion, then verifies via the API surface (no raw DB/Qdrant
creds needed):
  - extraction: GET /documents/{id} extracted_text contains the known content
  - tagging:    GET /documents/{id} auto_tags is populated
  - chunking + embedding: POST /rag/search for the known content returns a
    semantic hit whose id matches the uploaded document (proof a DocChunk +
    Qdrant point exist for it, not just that the document row was created)

Usage:
    python scripts/qa_rf30_ingestion_validation.py [--base-url URL] [--timeout SECONDS]
"""

import argparse
import sys
import time
import uuid

import fitz  # PyMuPDF
import httpx

DEFAULT_BASE_URL = "https://recruitflow-backend-424745949201.asia-south1.run.app"


def _pdf_with_text(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


DOCS = [
    {
        "doc_type": "resume",
        "title": "RF-30 QA resume",
        "marker": f"QARF30RESUME{uuid.uuid4().hex[:8]}",
        "text_suffix": "Skills: Python, Kubernetes, distributed systems.",
    },
    {
        "doc_type": "job_description",
        "title": "RF-30 QA job description",
        "marker": f"QARF30JD{uuid.uuid4().hex[:8]}",
        "text_suffix": "Seeking a backend engineer with Python and cloud experience.",
    },
]


def poll_status(client: httpx.Client, headers: dict, document_id: str, timeout: float) -> str:
    deadline = time.monotonic() + timeout
    status = None
    while time.monotonic() < deadline:
        r = client.get(f"/api/v1/documents/{document_id}/status", headers=headers)
        r.raise_for_status()
        status = r.json()["status"]
        if status in ("completed", "failed"):
            return status
        time.sleep(3)
    return status or "timeout"


def run(base_url: str, timeout: float) -> bool:
    all_ok = True
    with httpx.Client(base_url=base_url, timeout=60.0) as client:
        email = f"rf30-qa-{uuid.uuid4()}@example.com"
        password = "qa-test-pass-123"

        print(f"[rf30] registering {email}")
        client.post(
            "/api/v1/auth/register",
            json={"email": email, "full_name": "RF-30 QA", "password": password},
        ).raise_for_status()
        r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        r.raise_for_status()
        headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

        r = client.post(
            "/api/v1/clients", json={"name": "RF-30 QA Client"}, headers=headers
        )
        r.raise_for_status()
        client_id = r.json()["id"]

        for spec in DOCS:
            text = f"{spec['marker']} {spec['text_suffix']}"
            print(f"\n[rf30] uploading {spec['doc_type']}: {spec['title']}")
            r = client.post(
                "/api/v1/documents/upload",
                data={
                    "client_id": client_id,
                    "title": spec["title"],
                    "doc_type": spec["doc_type"],
                },
                files={"file": (f"{spec['doc_type']}.pdf", _pdf_with_text(text), "application/pdf")},
                headers=headers,
            )
            r.raise_for_status()
            document_id = r.json()["id"]

            status = poll_status(client, headers, document_id, timeout)
            print(f"[rf30] final status={status}")
            if status != "completed":
                print(f"[rf30] FAIL ({spec['doc_type']}): ingestion did not complete")
                all_ok = False
                continue

            r = client.get(f"/api/v1/documents/{document_id}", headers=headers)
            r.raise_for_status()
            detail = r.json()

            extracted_ok = bool(detail.get("extracted_text")) and spec["marker"] in detail["extracted_text"]
            print(f"[rf30] extraction check: {'PASS' if extracted_ok else 'FAIL'}")
            all_ok &= extracted_ok

            tags_ok = bool(detail.get("auto_tags"))
            print(f"[rf30] tagging check ({detail.get('auto_tags')}): {'PASS' if tags_ok else 'FAIL'}")
            all_ok &= tags_ok

            r = client.post(
                "/api/v1/rag/search",
                json={"query": text, "client_id": client_id, "limit": 10},
                headers=headers,
            )
            r.raise_for_status()
            results = r.json()["results"]
            semantic_hit = any(
                res.get("id") == document_id and str(res.get("source", "")).startswith("semantic")
                for res in results
            )
            print(f"[rf30] chunking+embedding check (semantic hit found): {'PASS' if semantic_hit else 'FAIL'}")
            all_ok &= semantic_hit

    return all_ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()
    ok = run(args.base_url, args.timeout)
    print(f"\n[rf30] {'PASS' if ok else 'FAIL'}: ingestion pipeline validation")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
