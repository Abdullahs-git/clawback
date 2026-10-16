#!/usr/bin/env python3
"""
benchmark/run_extraction_replay_gate.py
Extraction Replay Quality Gate (CI-safe, runs certified replay outputs).
Validates:
- Extraction precision >= min_extraction_precision
- Extraction recall >= min_extraction_recall
- Quote verification rate == min_quote_verification_rate (100%)
"""

import asyncio
import json
from pathlib import Path
import sys

from backend.app.services.extraction import extract_contract_rules

BENCHMARK_DIR = Path(__file__).resolve().parent
DATA_DIR = BENCHMARK_DIR / "data"
THRESHOLDS_FILE = BENCHMARK_DIR / "thresholds.json"


async def main_async():
    print("=" * 65)
    print("   CLAWBACK EXTRACTION REPLAY GATE (CERTIFIED REPLAY)")
    print("=" * 65)

    gt_file = DATA_DIR / "ground_truth.json"
    if not gt_file.exists():
        print(f"ERROR: Ground truth file not found at {gt_file}")
        sys.exit(1)

    with open(gt_file, "r", encoding="utf-8") as f:
        gt = json.load(f)

    thresholds = {
        "min_extraction_precision": 0.95,
        "min_extraction_recall": 0.95,
        "min_quote_verification_rate": 1.00,
    }
    if THRESHOLDS_FILE.exists():
        with open(THRESHOLDS_FILE, "r", encoding="utf-8") as f:
            thresholds.update(json.load(f))

    contracts_gt = gt["contracts"]
    print(f"Evaluating {len(contracts_gt)} contract profiles in certified replay mode...")
    print("-" * 65)

    total_true_rules = 0
    total_extracted_rules = 0
    total_matched_rules = 0
    total_verified_quotes = 0

    for c in contracts_gt:
        pdf_path = DATA_DIR / "contracts" / c["pdf_filename"]
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        ext = await extract_contract_rules(
            pdf_bytes=pdf_bytes,
            filename=c["pdf_filename"],
            carrier_hint=c["carrier_name"]
        )

        ext_rules = ext.get("rules", [])
        gt_rules = c["rules"]

        total_true_rules += len(gt_rules)
        total_extracted_rules += len(ext_rules)

        gt_types = [r["type"] for r in gt_rules]
        for er in ext_rules:
            if er.get("status") != "rejected":
                total_verified_quotes += 1
                if er["type"] in gt_types:
                    total_matched_rules += 1

    precision = total_matched_rules / total_extracted_rules if total_extracted_rules > 0 else 0.0
    recall = total_matched_rules / total_true_rules if total_true_rules > 0 else 0.0
    quote_rate = total_verified_quotes / total_extracted_rules if total_extracted_rules > 0 else 0.0

    print(f"Ground Truth Rules:      {total_true_rules}")
    print(f"Extracted Rules:         {total_extracted_rules}")
    print(f"Matched Rules:           {total_matched_rules}")
    print(f"Verified Quotes:         {total_verified_quotes}")
    print(f"Extraction Precision:    {precision * 100:.2f}% (Threshold: {thresholds['min_extraction_precision'] * 100:.1f}%)")
    print(f"Extraction Recall:       {recall * 100:.2f}% (Threshold: {thresholds['min_extraction_recall'] * 100:.1f}%)")
    print(f"Quote Verification Rate: {quote_rate * 100:.2f}% (Threshold: {thresholds['min_quote_verification_rate'] * 100:.1f}%)")
    print("-" * 65)

    failures = []
    if precision < thresholds["min_extraction_precision"]:
        failures.append(f"Precision {precision:.4f} < {thresholds['min_extraction_precision']}")
    if recall < thresholds["min_extraction_recall"]:
        failures.append(f"Recall {recall:.4f} < {thresholds['min_extraction_recall']}")
    if quote_rate < thresholds["min_quote_verification_rate"]:
        failures.append(f"Quote verification rate {quote_rate:.4f} < {thresholds['min_quote_verification_rate']}")

    if failures:
        print("\nEXTRACTION REPLAY GATE FAILED:")
        for fail in failures:
            print(f"  - {fail}")
        sys.exit(1)
    else:
        print("\nEXTRACTION REPLAY GATE PASSED.")
        sys.exit(0)


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
