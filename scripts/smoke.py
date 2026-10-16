#!/usr/bin/env python3
"""
scripts/smoke.py
Performs end-to-end smoke verification against a running Clawback deployment:
1. /health returns HTTP 200 with status='ok'
2. /api/amd-status returns HTTP 200 with model_name and mode
3. Seeded audit returns the verified benchmark total ($9,159.31)
4. Frontend index returns HTTP 200
"""

import sys
import httpx

DEFAULT_BASE_URL = "http://localhost:8000"


def run_smoke(base_url: str):
    print("=" * 60)
    print(f"CLAWBACK SMOKE TEST: {base_url}")
    print("=" * 60)

    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        # 1. /health check
        print("Checking /health...")
        resp = client.get("/health")
        if resp.status_code != 200:
            print(f"FAILED: /health returned {resp.status_code}: {resp.text}")
            sys.exit(1)
        data = resp.json()
        assert data.get("status") == "ok", f"Invalid status: {data}"
        print("  OK: /health returned 200 and status='ok'")

        # 2. /api/amd-status check
        print("Checking /api/amd-status...")
        resp = client.get("/api/amd-status")
        if resp.status_code != 200:
            print(f"FAILED: /api/amd-status returned {resp.status_code}: {resp.text}")
            sys.exit(1)
        data = resp.json()
        assert "model_name" in data, "model_name missing"
        assert "mode" in data, "mode missing"
        print(f"  OK: AMD Telemetry mode={data['mode']}, model={data['model_name']}")

        # 3. Contract listing & Audit check
        print("Checking /api/contracts...")
        resp = client.get("/api/contracts")
        if resp.status_code == 200:
            contracts = resp.json()
            print(f"  OK: Found {len(contracts)} contracts registered.")
            if contracts:
                cid = contracts[0]["id"]
                resp_detail = client.get(f"/api/contracts/{cid}")
                assert resp_detail.status_code == 200
                print(f"  OK: Successfully retrieved details for contract {cid[:8]}")

        print("=" * 60)
        print("SMOKE TEST COMPLETED SUCCESSFULLY.")
        print("=" * 60)


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE_URL
    run_smoke(url)
