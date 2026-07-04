#!/bin/bash
# RecruitFlow AI - GitHub Security Configuration
# Requires: gh CLI authenticated with admin access to the repository
# Run after PROMPT-010 to finalize branch protection.

set -euo pipefail

REPO="akshatVardhan/recruitflow-ai"

echo "=== 1. Branch Protection: main ==="
gh api repos/$REPO/branches/main/protection \
  --method PUT \
  --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": []
  },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null
}
EOF

echo "=== 2. Branch Protection: staging ==="
gh api repos/$REPO/branches/staging/protection \
  --method PUT \
  --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": []
  },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null
}
EOF

echo "=== 3. Enable Secret Scanning ==="
gh api repos/$REPO \
  --method PATCH \
  --input - <<EOF
{
  "security_and_analysis": {
    "secret_scanning": {
      "status": "enabled"
    },
    "secret_scanning_push_protection": {
      "status": "enabled"
    }
  }
}
EOF

echo "=== GitHub Security Configuration Complete ==="
echo ""
echo "Verify settings at: https://github.com/$REPO/settings/branches"
