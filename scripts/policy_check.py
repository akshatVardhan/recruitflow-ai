#!/usr/bin/env python3
"""RecruitFlow policy checks - deterministic security invariants.

Run by .github/workflows/security.yml on every PR to staging/main.
Exit 1 on any non-waived violation.

WAIVERS: each entry downgrades matching failures to warnings. Every waiver
MUST carry a JIRA key and is reviewed by CyberSecurity Eng each sprint.
Remove the waiver when the referenced story merges.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (substring of failure message, JIRA key, note)
WAIVERS: list[tuple[str, str, str]] = []

failures: list[str] = []
warnings: list[str] = []


def fail(msg: str) -> None:
    for pattern, jira, note in WAIVERS:
        if pattern in msg:
            warnings.append(f"[WAIVED {jira}] {msg} ({note})")
            return
    failures.append(msg)


# 1. No .env files anywhere (only .env.example allowed) - Doppler-only convention
for p in ROOT.rglob(".env*"):
    if p.is_file() and p.name != ".env.example" and "node_modules" not in p.parts:
        fail(f".env file present: {p.relative_to(ROOT)}")

# 2. CORS: backend URL must not be used as an allowed origin
main_py = ROOT / "backend" / "app" / "main.py"
if main_py.exists():
    text = main_py.read_text()
    m = re.search(r"allow_origins\s*=\s*\[([^\]]*)\]", text, re.S)
    if m:
        block = m.group(1)
        if "next_public_api_base_url" in block:
            fail(
                "backend/app/main.py: allow_origins references next_public_api_base_url"
            )
        if "run.app" in block:
            fail("backend/app/main.py: allow_origins contains a run.app URL")

# 3. (removed, RF-68/ADR-009) - a prior version of this check failed any
# client_id accepted via Form(), on the assumption that tenancy would be a
# JWT claim and client_id should never be client-supplied at all. ADR-009
# (docs/ADR.md) made the opposite call: a user can own multiple clients, so
# client_id necessarily travels with the request, and tenancy is enforced
# via a per-request ownership check (get_client_for_user) instead. That
# pattern is now correct by design, not a lingering violation to wave away.

# 4. No tokens written to browser storage
for p in (ROOT / "frontend").rglob("*.ts*"):
    if "node_modules" in p.parts or ".next" in p.parts:
        continue
    for i, line in enumerate(p.read_text(errors="ignore").splitlines(), 1):
        if re.search(
            r"(localStorage|sessionStorage)\.setItem\([^)]*(token|jwt)", line, re.I
        ):
            fail(f"{p.relative_to(ROOT)}:{i}: token written to browser storage")

# 5. Endpoint auth enforcement - dormant until get_current_user exists
backend_files = list((ROOT / "backend" / "app").rglob("*.py"))
has_auth_dep = any(
    "def get_current_user" in p.read_text(errors="ignore") for p in backend_files
)
if has_auth_dep:
    EXEMPT_MODULES = {"auth"}
    for p in (ROOT / "backend" / "app" / "modules").rglob("router.py"):
        if p.parent.name in EXEMPT_MODULES:
            continue
        text = p.read_text()
        n = len(re.findall(r"@router\.(get|post|put|patch|delete)", text))
        if n and "get_current_user" not in text:
            fail(
                f"{p.relative_to(ROOT)}: {n} endpoint(s) with no get_current_user dependency"
            )
else:
    warnings.append(
        "get_current_user not implemented yet - endpoint auth check dormant, activates automatically"
    )

for w in warnings:
    print(f"WARN: {w}")
if failures:
    print(f"\nPOLICY VIOLATIONS ({len(failures)}):")
    for f in failures:
        print(f"FAIL: {f}")
    sys.exit(1)
print("Policy checks passed.")
