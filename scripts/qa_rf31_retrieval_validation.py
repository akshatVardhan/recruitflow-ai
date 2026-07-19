#!/usr/bin/env python3
"""RF-31: hybrid search retrieval accuracy + client isolation QA validation.

Two independent tenants (own user, own client) each upload a resume with
distinctive, non-overlapping content. Verifies:
  - relevance: a tenant's own search for their document's content returns it
  - ownership isolation: tenant A searching tenant B's client_id gets 404
    (app/modules/rag/router.py's get_client_for_user check)
  - vector-layer isolation: tenant B's search, scoped to B's own client_id,
    never returns tenant A's document even when queried with A's exact terms
    (proves the Qdrant `must` client_id filter, not just the HTTP ownership
    check, is what prevents cross-client leakage)

Usage:
    python scripts/qa_rf31_retrieval_validation.py [--base-url URL] [--timeout SECONDS]
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


def register_tenant(client: httpx.Client, label: str) -> dict:
    email = f"rf31-qa-{label}-{uuid.uuid4()}@example.com"
    password = "qa-test-pass-123"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": f"RF-31 QA {label}", "password": password},
    ).raise_for_status()
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    r.raise_for_status()
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.post(
        "/api/v1/clients", json={"name": f"RF-31 QA Client {label}"}, headers=headers
    )
    r.raise_for_status()
    return {"headers": headers, "client_id": r.json()["id"]}


def upload_and_wait(client: httpx.Client, tenant: dict, marker: str, content: str, timeout: float) -> str:
    text = f"{marker} {content}"
    r = client.post(
        "/api/v1/documents/upload",
        data={"client_id": tenant["client_id"], "title": marker, "doc_type": "resume"},
        files={"file": ("resume.pdf", _pdf_with_text(text), "application/pdf")},
        headers=tenant["headers"],
    )
    r.raise_for_status()
    document_id = r.json()["id"]

    deadline = time.monotonic() + timeout
    status = None
    while time.monotonic() < deadline:
        r = client.get(f"/api/v1/documents/{document_id}/status", headers=tenant["headers"])
        r.raise_for_status()
        status = r.json()["status"]
        if status in ("completed", "failed"):
            break
        time.sleep(3)
    if status != "completed":
        raise RuntimeError(f"ingestion for {marker} ended in status={status!r}")
    return document_id


def search(client: httpx.Client, tenant: dict, client_id: str, query: str) -> httpx.Response:
    return client.post(
        "/api/v1/rag/search",
        json={"query": query, "client_id": client_id, "limit": 10},
        headers=tenant["headers"],
    )


def run(base_url: str, timeout: float) -> bool:
    all_ok = True
    with httpx.Client(base_url=base_url, timeout=60.0) as client:
        print("[rf31] provisioning tenant A and tenant B")
        tenant_a = register_tenant(client, "a")
        tenant_b = register_tenant(client, "b")

        marker_a = f"QARF31TENANTA{uuid.uuid4().hex[:8]}"
        marker_b = f"QARF31TENANTB{uuid.uuid4().hex[:8]}"

        print("[rf31] uploading tenant A resume (Kubernetes/distributed systems)")
        doc_a = upload_and_wait(
            client, tenant_a, marker_a,
            "Kubernetes distributed systems platform engineer.", timeout,
        )
        print("[rf31] uploading tenant B resume (pastry chef/watercolor)")
        doc_b = upload_and_wait(
            client, tenant_b, marker_b,
            "Pastry chef with a watercolor painting hobby.", timeout,
        )

        # Relevance: tenant A's own search finds their own document.
        r = search(client, tenant_a, tenant_a["client_id"], f"{marker_a} Kubernetes distributed systems")
        r.raise_for_status()
        results_a = r.json()["results"]
        relevance_ok = any(res.get("id") == doc_a for res in results_a)
        print(f"[rf31] relevance check (A finds own doc): {'PASS' if relevance_ok else 'FAIL'}")
        all_ok &= relevance_ok

        # Ownership isolation: A can't even query B's client_id.
        r = search(client, tenant_a, tenant_b["client_id"], marker_b)
        ownership_ok = r.status_code == 404
        print(f"[rf31] ownership isolation check (A queries B's client_id -> {r.status_code}): "
              f"{'PASS' if ownership_ok else 'FAIL'}")
        all_ok &= ownership_ok

        # Vector-layer isolation: B searching B's own client_id with A's exact
        # terms must never surface A's document.
        r = search(client, tenant_b, tenant_b["client_id"], f"{marker_a} Kubernetes distributed systems")
        r.raise_for_status()
        results_b = r.json()["results"]
        leak_ok = not any(res.get("id") == doc_a for res in results_b)
        print(f"[rf31] cross-client leakage check (B's search never returns A's doc): "
              f"{'PASS' if leak_ok else 'FAIL'}")
        all_ok &= leak_ok

    return all_ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()
    ok = run(args.base_url, args.timeout)
    print(f"\n[rf31] {'PASS' if ok else 'FAIL'}: retrieval accuracy + isolation validation")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
