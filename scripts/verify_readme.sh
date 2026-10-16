#!/usr/bin/env bash
# scripts/verify_readme.sh - Validates README commands on clean runner
set -euo pipefail

echo "Starting Clawback README verification..."
python3 scripts/verify_readme.py
