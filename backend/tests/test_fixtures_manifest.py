"""
Tests for Fixture Integrity & Manifest Verification.
Ensures that all replay fixtures match their recorded SHA-256 hashes in fixtures/manifest.json.
Fails if any fixture is modified or corrupted.
"""
import hashlib
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "fixtures"
MANIFEST_PATH = FIXTURES_DIR / "manifest.json"


def test_manifest_exists():
    assert MANIFEST_PATH.exists(), f"Manifest file missing at {MANIFEST_PATH}"


def test_fixtures_sha256_integrity():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert "fixtures" in manifest
    fixtures = manifest["fixtures"]
    assert len(fixtures) > 0

    for fname, meta in fixtures.items():
        fixture_path = FIXTURES_DIR / fname
        assert fixture_path.exists(), f"Fixture file {fname} declared in manifest does not exist on disk"

        file_bytes = fixture_path.read_bytes()
        computed_sha = hashlib.sha256(file_bytes).hexdigest()

        assert computed_sha == meta["sha256"], (
            f"Integrity check failed for {fname}! Expected SHA-256 {meta['sha256']}, but got {computed_sha}. "
            "Fixture has been modified or corrupted."
        )
        assert meta["endpoint_host"] is not None
        assert meta["model"] is not None
        assert meta["request_id"] is not None
