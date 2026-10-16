#!/usr/bin/env python3
"""
benchmark/run_audit_gate.py
Deterministic Audit Quality Gate (CI-safe, Zero GPU / Zero LLM calls).
Validates rules engine and synthetic invoice batches together:
- Recall of planted errors must be 100%
- Precision must be >= 99%
- Dollar variance must be $0.00
"""

from decimal import Decimal
import json
from pathlib import Path
import sys
from typing import List

from backend.app.api.invoices import parse_csv_invoices
from rules_engine.engine import AuditEngine
from rules_engine.types import RuleDefinition, NormalizedInvoiceLine

BENCHMARK_DIR = Path(__file__).resolve().parent
DATA_DIR = BENCHMARK_DIR / "data"
THRESHOLDS_FILE = BENCHMARK_DIR / "thresholds.json"


def to_dec(val):
    if val is not None and str(val).strip() != "":
        try:
            return Decimal(str(val).strip())
        except Exception:
            return None
    return None


def main():
    print("=" * 65)
    print("   CLAWBACK DETERMINISTIC AUDIT GATE (NO GPU REQUIRED)")
    print("=" * 65)

    gt_file = DATA_DIR / "ground_truth.json"
    if not gt_file.exists():
        print(f"ERROR: Ground truth file not found at {gt_file}")
        sys.exit(1)

    with open(gt_file, "r", encoding="utf-8") as f:
        gt = json.load(f)

    thresholds = {
        "min_audit_recall": 1.00,
        "min_audit_precision": 0.99,
        "max_dollar_variance_percentage": 0.00,
    }
    if THRESHOLDS_FILE.exists():
        with open(THRESHOLDS_FILE, "r", encoding="utf-8") as f:
            thresholds.update(json.load(f))

    contracts_gt = gt["contracts"]
    batches_meta = gt["batches"]
    planted_gt = gt["planted_discrepancies"]

    print(f"Contracts: {len(contracts_gt)} | Batches: {len(batches_meta)}")
    print(f"Total Lines: {gt['metadata']['total_invoice_lines']}")
    print(f"Planted Errors: {len(planted_gt)} | Target Dollars: ${gt['metadata']['total_planted_overcharge_dollars']}")
    print("-" * 65)

    # Convert ground-truth contractual rules into approved RuleDefinitions
    carrier_rules = {}
    for c in contracts_gt:
        carrier_name = c["carrier_name"]
        rules = []
        for r in c["rules"]:
            rules.append(
                RuleDefinition(
                    id=r["id"],
                    type=r["type"],
                    description=r.get("description", ""),
                    parameters=r.get("parameters", {}),
                    source_page=r.get("source_page", 1),
                    source_quote=r.get("source_quote", ""),
                    status="approved",
                )
            )
        carrier_rules[carrier_name] = rules

    total_findings = 0
    total_recovered_dollars = Decimal("0.00")
    detected_discrepancies = []

    for b in batches_meta:
        fname = b.get("filename") or b.get("csv_filename")
        csv_path = DATA_DIR / "invoices" / fname
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_content = f.read()

        db_lines = parse_csv_invoices(csv_content, batch_id=b.get("batch_id", "BATCH-001"))
        carrier_name = b["carrier_name"]
        rules = carrier_rules.get(carrier_name, [])

        engine_lines: List[NormalizedInvoiceLine] = []
        for l in db_lines:
            engine_lines.append(
                NormalizedInvoiceLine(
                    line_id=l.id,
                    invoice_number=l.invoice_number,
                    invoice_date=l.invoice_date,
                    shipment_id=l.shipment_id,
                    charge_code=l.charge_code,
                    amount_billed=Decimal(l.amount_billed),
                    charge_description=l.charge_description,
                    service_level=l.service_level,
                    origin_zip=l.origin_zip,
                    destination_zip=l.destination_zip,
                    zone=l.zone,
                    weight_actual_lbs=to_dec(l.weight_actual_lbs),
                    dim_length_in=to_dec(l.dim_length_in),
                    dim_width_in=to_dec(l.dim_width_in),
                    dim_height_in=to_dec(l.dim_height_in),
                    billed_weight_lbs=to_dec(l.billed_weight_lbs),
                    published_rate=to_dec(l.published_rate),
                    discount_applied_percent=to_dec(l.discount_applied_percent),
                    fuel_surcharge_percent=to_dec(l.fuel_surcharge_percent),
                )
            )

        engine = AuditEngine(rules)
        audit_res = engine.audit(engine_lines)

        total_findings += len(audit_res.discrepancies)
        total_recovered_dollars += audit_res.total_overcharge

        for d in audit_res.discrepancies:
            detected_discrepancies.append(d)

    # Compare against ground truth planted discrepancies
    true_positives = 0
    false_positives = 0
    matched_gt_ids = set()

    for d in detected_discrepancies:
        # Match line ID
        matched_gt = next(
            (p for p in planted_gt if p["line_id"] in d.line_id or d.line_id.endswith(p["line_id"])),
            None
        )
        if matched_gt:
            true_positives += 1
            matched_gt_ids.add(matched_gt["line_id"])
        else:
            false_positives += 1

    false_negatives = len(planted_gt) - len(matched_gt_ids)
    recall = true_positives / len(planted_gt) if planted_gt else 1.0
    precision = true_positives / len(detected_discrepancies) if detected_discrepancies else 1.0

    planted_dollars = Decimal(str(gt["metadata"]["total_planted_overcharge_dollars"]))
    dollar_variance = abs(total_recovered_dollars - planted_dollars)
    variance_pct = (dollar_variance / planted_dollars) if planted_dollars > 0 else Decimal("0")

    print(f"\nRESULTS:")
    print(f"  Planted Discrepancies: {len(planted_gt)}")
    print(f"  Detected Findings:     {total_findings}")
    print(f"  True Positives:        {true_positives}")
    print(f"  False Positives:       {false_positives}")
    print(f"  False Negatives:       {false_negatives}")
    print(f"  Audit Recall:          {recall * 100:.2f}% (Threshold: {thresholds['min_audit_recall'] * 100:.1f}%)")
    print(f"  Audit Precision:       {precision * 100:.2f}% (Threshold: {thresholds['min_audit_precision'] * 100:.1f}%)")
    print(f"  Planted Dollars:       ${planted_dollars:,.2f}")
    print(f"  Recovered Dollars:     ${total_recovered_dollars:,.2f}")
    print(f"  Dollar Variance:       ${dollar_variance:,.2f} ({variance_pct * 100:.2f}%)")
    print("-" * 65)

    failures = []
    if recall < thresholds["min_audit_recall"]:
        failures.append(f"Recall {recall * 100:.2f}% < required {thresholds['min_audit_recall'] * 100:.1f}%")
    if precision < thresholds["min_audit_precision"]:
        failures.append(f"Precision {precision * 100:.2f}% < required {thresholds['min_audit_precision'] * 100:.1f}%")
    if variance_pct > Decimal(str(thresholds["max_dollar_variance_percentage"])):
        failures.append(f"Dollar variance {variance_pct * 100:.2f}% exceeds allowed limit")

    if failures:
        print(f"\nAUDIT GATE FAILED:")
        for fail in failures:
            print(f"  - {fail}")
        sys.exit(1)
    else:
        print("\nAUDIT GATE PASSED: 100% recall, >=99% precision, $0.00 variance.")
        sys.exit(0)


if __name__ == "__main__":
    main()
