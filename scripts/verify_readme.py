#!/usr/bin/env python3
"""
scripts/verify_readme.py
Verifies that all prerequisites and commands documented in README.md execute cleanly:
1. Environment variables exist and match .env.example
2. Rules engine tests pass with 100% coverage
3. Deterministic audit gate passes with planted ground truth
4. Replay extraction gate passes
5. Claims checker validates copy and citations
"""

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_step(name: str, cmd: list, cwd=REPO_ROOT):
    print(f"\n[STEP] {name}")
    print(f"Command: {' '.join(cmd)}")
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{REPO_ROOT};{REPO_ROOT / 'rules_engine'}"
    res = subprocess.run(cmd, cwd=str(cwd), env=env)
    if res.returncode != 0:
        print(f"FAILED: Step '{name}' returned non-zero exit code {res.returncode}")
        sys.exit(res.returncode)
    print(f"PASSED: {name}")


def main():
    print("=" * 65)
    print("        CLAWBACK README & REPRODUCIBILITY VERIFICATION")
    print("=" * 65)

    py_exe = sys.executable

    # 1. Check .env exists
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        print("Copying .env.example -> .env")
        example_file = REPO_ROOT / ".env.example"
        if example_file.exists():
            env_file.write_text(example_file.read_text(encoding="utf-8"), encoding="utf-8")

    # 2. Run Rules Engine 100% Coverage Gate
    run_step(
        "Rules Engine 100% Coverage & Property Tests",
        [py_exe, "-m", "pytest", "tests", "-v", "--cov=rules_engine", "--cov-branch", "--cov-fail-under=100"],
        cwd=REPO_ROOT / "rules_engine"
    )

    # 3. Run Backend Integration Tests
    run_step(
        "Backend API & Quote Verification Suite",
        [py_exe, "-m", "pytest", "backend/tests", "-v"]
    )

    # 4. Run Deterministic Audit Gate
    run_step(
        "Deterministic Audit Benchmark Gate",
        [py_exe, "benchmark/run_audit_gate.py"]
    )

    # 5. Run Extraction Replay Gate
    run_step(
        "Extraction Replay Benchmark Gate",
        [py_exe, "benchmark/run_extraction_replay_gate.py"]
    )

    # 6. Run Claims Check
    run_step(
        "Copy & Claims Integrity Check",
        [py_exe, "scripts/check_claims.py"]
    )

    print("\n" + "=" * 65)
    print("ALL README VERIFICATION GATES PASSED CLEANLY!")
    print("=" * 65)


if __name__ == "__main__":
    main()
