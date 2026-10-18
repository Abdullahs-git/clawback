"""
Demo and Benchmark API Router.
Provides endpoints for seeding synthetic demo data and exposing audited benchmark results.
"""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

from backend.app.seed import seed_database

router = APIRouter(prefix="/api", tags=["Demo & Benchmark"])

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RESULTS_FILE = REPO_ROOT / "benchmark" / "results.json"


@router.post("/demo/seed")
def seed_demo_workspace():
    """Seeds the database with synthetic carrier contracts, rules, and audited invoices."""
    try:
        seed_database()
        return {
            "status": "success",
            "message": "Demo workspace seeded successfully with synthetic carrier contracts, verified rules, and audited invoices."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed demo workspace: {str(e)}")


@router.get("/benchmark")
def get_benchmark_results():
    """Returns the latest deterministic benchmark results and provenance."""
    if not RESULTS_FILE.exists():
        raise HTTPException(status_code=404, detail="Benchmark results not found")
    try:
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read benchmark results: {str(e)}")
