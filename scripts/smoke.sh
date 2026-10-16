#!/usr/bin/env bash
# scripts/smoke.sh - Smoke test runner for Clawback deployment
set -euo pipefail

TARGET_URL="${1:-http://localhost:8000}"

echo "Executing Clawback smoke test against: $TARGET_URL"
python3 scripts/smoke.py "$TARGET_URL"
