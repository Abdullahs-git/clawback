"""
Synthetic Carrier Data & Ground Truth Generator.
Generates 3 synthetic carrier contract PDFs, thousands of invoice lines across batches,
and plants deterministic errors with exact ground-truth records.
All money logic strictly uses Decimal.
"""
import csv
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import random
from typing import Any, Dict, List
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

BENCHMARK_DIR = Path(__file__).resolve().parent
DATA_DIR = BENCHMARK_DIR / "data"
INVOICES_DIR = DATA_DIR / "invoices"
CONTRACTS_DIR = DATA_DIR / "contracts"

TWO_PLACES = Decimal("0.01")


def generate_contract_pdf(filepath: Path, carrier_name: str, contract_ref: str, clauses: List[Dict[str, Any]]):
    """Generates a professional synthetic carrier contract PDF with a verifiable text layer."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(filepath), pagesize=letter)

    # Page 1: Cover & Agreement Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 740, "MASTER TRANSPORTATION SERVICES AGREEMENT")
    c.setFont("Helvetica", 10)
    c.drawString(50, 720, f"Contract Reference: {contract_ref} | SYNTHETIC DEMO DATA")
    c.drawString(50, 705, f"Carrier: {carrier_name}")
    c.drawString(50, 690, "Effective Date: January 1, 2026   Expiration Date: December 31, 2026")
    c.line(50, 680, 560, 680)

    c.drawString(50, 650, "This Agreement governs all commercial transportation, freight handling, and billing terms")
    c.drawString(50, 635, "between Carrier and Shipper. All rates and discounts specified herein are legally binding.")
    c.showPage()

    # Subsequent pages: One page per major commercial clause group
    page_num = 2
    for item in clauses:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 740, f"Page {page_num} - {item['title']}")
        c.line(50, 730, 560, 730)
        c.setFont("Helvetica", 10)

        y = 700
        for line in item["paragraphs"]:
            c.drawString(50, y, line)
            y -= 20

        c.setFont("Helvetica-Oblique", 8)
        c.drawString(50, 50, f"Contract {contract_ref} | Page {page_num} of {len(clauses)+1} | Synthetic Demo Contract")
        c.showPage()
        page_num += 1

    c.save()


def build_synthetic_contracts_and_ground_truth():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    INVOICES_DIR.mkdir(parents=True, exist_ok=True)
    CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)

    contracts_config = [
        {
            "carrier_name": "Apex Freight Logistics",
            "ref": "AFL-2026-MSA-088",
            "pdf_filename": "apex_freight_contract.pdf",
            "rules": [
                {
                    "id": "AFL-RULE-001",
                    "type": "base_discount",
                    "description": "45% discount off standard published baseline freight rates",
                    "parameters": {"percentage": 0.45, "service_level": "Standard LTL"},
                    "source_page": 2,
                    "source_quote": "Shipper shall receive an agreed base discount of forty-five percent (45.0%) off all published standard linehaul rates.",
                    "confidence": 0.98,
                    "status": "proposed"
                },
                {
                    "id": "AFL-RULE-002",
                    "type": "accessorial_rule",
                    "description": "Residential delivery surcharge waived entirely",
                    "parameters": {"fee_type": "residential", "allowed": False},
                    "source_page": 3,
                    "source_quote": "Residential delivery surcharges shall be waived in full and shall not be assessed on any shipment.",
                    "confidence": 0.99,
                    "status": "proposed"
                },
                {
                    "id": "AFL-RULE-003",
                    "type": "accessorial_rule",
                    "description": "Liftgate service fee capped at $40.00",
                    "parameters": {"fee_type": "liftgate", "allowed": True, "cap": "40.00"},
                    "source_page": 3,
                    "source_quote": "Where requested, liftgate service charges shall not exceed forty dollars ($40.00) per occurrence.",
                    "confidence": 0.97,
                    "status": "proposed"
                },
                {
                    "id": "AFL-RULE-004",
                    "type": "fuel_surcharge",
                    "description": "Fuel surcharge fixed at 11.5% for contract term",
                    "parameters": {"fixed_percentage": 0.115},
                    "source_page": 4,
                    "source_quote": "The applicable fuel surcharge index is agreed and fixed at eleven and one-half percent (11.5%) of net linehaul freight.",
                    "confidence": 0.96,
                    "status": "proposed"
                },
                {
                    "id": "AFL-RULE-005",
                    "type": "dim_weight_divisor",
                    "description": "Dimensional weight divisor established at 166 cubic inches per pound",
                    "parameters": {"divisor": 166},
                    "source_page": 4,
                    "source_quote": "Cubic dimensional weight calculations shall strictly utilize a divisor of one hundred sixty-six (166).",
                    "confidence": 0.98,
                    "status": "proposed"
                },
                {
                    "id": "AFL-RULE-006",
                    "type": "minimum_charge",
                    "description": "Absolute minimum linehaul charge floor of $45.00",
                    "parameters": {"amount": "45.00"},
                    "source_page": 5,
                    "source_quote": "The minimum charge floor per shipment after discount application shall be forty-five dollars ($45.00).",
                    "confidence": 0.95,
                    "status": "proposed"
                },
                {
                    "id": "AFL-RULE-007",
                    "type": "duplicate_charge",
                    "description": "Prohibition of redundant or duplicate line item billing",
                    "parameters": {"enabled": True},
                    "source_page": 5,
                    "source_quote": "Carrier warrants that no individual shipment BOL or tracking number shall be invoiced more than once.",
                    "confidence": 0.99,
                    "status": "proposed"
                },
                {
                    "id": "AFL-RULE-008",
                    "type": "claim_window_days",
                    "description": "180 calendar days dispute submission window from invoice date",
                    "parameters": {"days": 180},
                    "source_page": 6,
                    "source_quote": "Disputes and overcharge claims must be formally submitted in writing within one hundred eighty (180) days of invoice date.",
                    "confidence": 0.99,
                    "status": "proposed"
                }
            ],
            "clauses": [
                {
                    "title": "Section 3: Baseline Rate Discounts",
                    "paragraphs": [
                        "3.1 Freight Pricing Schedules",
                        "Shipper shall receive an agreed base discount of forty-five percent (45.0%) off all published standard linehaul rates.",
                        "Discounts apply across all standard interstate and intrastate origin and destination lanes."
                    ]
                },
                {
                    "title": "Section 4: Accessorial Fees & Waivers",
                    "paragraphs": [
                        "4.1 Surcharge Accommodations",
                        "Residential delivery surcharges shall be waived in full and shall not be assessed on any shipment.",
                        "4.2 Specialized Equipment",
                        "Where requested, liftgate service charges shall not exceed forty dollars ($40.00) per occurrence."
                    ]
                },
                {
                    "title": "Section 5: Fuel Surcharge & DIM Rating",
                    "paragraphs": [
                        "5.1 Fuel Stabilization Program",
                        "The applicable fuel surcharge index is agreed and fixed at eleven and one-half percent (11.5%) of net linehaul freight.",
                        "5.2 Density Rating Criteria",
                        "Cubic dimensional weight calculations shall strictly utilize a divisor of one hundred sixty-six (166)."
                    ]
                },
                {
                    "title": "Section 6: Minimum Floor & Billing Standards",
                    "paragraphs": [
                        "6.1 Absolute Billing Minimums",
                        "The minimum charge floor per shipment after discount application shall be forty-five dollars ($45.00).",
                        "6.2 Auditing Protections",
                        "Carrier warrants that no individual shipment BOL or tracking number shall be invoiced more than once."
                    ]
                },
                {
                    "title": "Section 7: Dispute Resolution and Filing Deadlines",
                    "paragraphs": [
                        "7.1 Overcharge Auditing Protocol",
                        "Disputes and overcharge claims must be formally submitted in writing within one hundred eighty (180) days of invoice date.",
                        "Carrier shall provide credit memos within thirty (30) days of receipt."
                    ]
                }
            ]
        },
        {
            "carrier_name": "Beacon Express Transport",
            "ref": "BET-2026-MSA-104",
            "pdf_filename": "beacon_express_contract.pdf",
            "rules": [
                {
                    "id": "BET-RULE-001",
                    "type": "base_discount",
                    "description": "50% discount on Express Ground services",
                    "parameters": {"percentage": 0.50, "service_level": "Ground"},
                    "source_page": 2,
                    "source_quote": "Shipper is granted a fifty percent (50.0%) discount from Carrier standard ground rate baseline.",
                    "confidence": 0.98,
                    "status": "proposed"
                },
                {
                    "id": "BET-RULE-002",
                    "type": "accessorial_rule",
                    "description": "Address correction fee fixed at $10.00 per package",
                    "parameters": {"fee_type": "address_correction", "allowed": True, "rate": "10.00"},
                    "source_page": 3,
                    "source_quote": "Address correction charges shall be billed at a flat rate of ten dollars ($10.00) per corrected package.",
                    "confidence": 0.97,
                    "status": "proposed"
                },
                {
                    "id": "BET-RULE-003",
                    "type": "fuel_surcharge",
                    "description": "Fuel surcharge fixed at 13.0%",
                    "parameters": {"fixed_percentage": 0.130},
                    "source_page": 4,
                    "source_quote": "Fuel surcharge will be pegged at thirteen percent (13.0%) throughout the contract period.",
                    "confidence": 0.95,
                    "status": "proposed"
                },
                {
                    "id": "BET-RULE-004",
                    "type": "duplicate_charge",
                    "description": "Prohibition of redundant billing",
                    "parameters": {"enabled": True},
                    "source_page": 5,
                    "source_quote": "Carrier agrees that no consignment shall be subject to duplicate invoicing.",
                    "confidence": 0.98,
                    "status": "proposed"
                },
                {
                    "id": "BET-RULE-005",
                    "type": "claim_window_days",
                    "description": "90 calendar days claim submission window",
                    "parameters": {"days": 90},
                    "source_page": 5,
                    "source_quote": "All billing adjustments and claims must be submitted within ninety (90) days from the invoice date.",
                    "confidence": 0.99,
                    "status": "proposed"
                }
            ],
            "clauses": [
                {
                    "title": "Section 2: Parcel Rate Matrix",
                    "paragraphs": [
                        "2.1 Ground Service Tiers",
                        "Shipper is granted a fifty percent (50.0%) discount from Carrier standard ground rate baseline."
                    ]
                },
                {
                    "title": "Section 3: Ancillary Accessorials",
                    "paragraphs": [
                        "3.1 Exception Surcharges",
                        "Address correction charges shall be billed at a flat rate of ten dollars ($10.00) per corrected package."
                    ]
                },
                {
                    "title": "Section 4: Energy Index",
                    "paragraphs": [
                        "4.1 Petroleum Adjustment Program",
                        "Fuel surcharge will be pegged at thirteen percent (13.0%) throughout the contract period."
                    ]
                },
                {
                    "title": "Section 5: Claim Procedures and Billing Integrity",
                    "paragraphs": [
                        "5.1 Duplicate Billing",
                        "Carrier agrees that no consignment shall be subject to duplicate invoicing.",
                        "5.2 Time Limitations",
                        "All billing adjustments and claims must be submitted within ninety (90) days from the invoice date."
                    ]
                }
            ]
        },
        {
            "carrier_name": "Crestline Cargo Partners",
            "ref": "CCP-2026-MSA-312",
            "pdf_filename": "crestline_cargo_contract.pdf",
            "rules": [
                {
                    "id": "CCP-RULE-001",
                    "type": "base_discount",
                    "description": "38% linehaul freight discount",
                    "parameters": {"percentage": 0.38},
                    "source_page": 2,
                    "source_quote": "Net freight charges will reflect a thirty-eight percent (38.0%) reduction from benchmark tariff.",
                    "confidence": 0.98,
                    "status": "proposed"
                },
                {
                    "id": "CCP-RULE-002",
                    "type": "accessorial_rule",
                    "description": "Liftgate charge capped at $50.00",
                    "parameters": {"fee_type": "liftgate", "allowed": True, "cap": "50.00"},
                    "source_page": 3,
                    "source_quote": "Liftgate equipment assistance will not exceed fifty dollars ($50.00) per bill of lading.",
                    "confidence": 0.97,
                    "status": "proposed"
                },
                {
                    "id": "CCP-RULE-003",
                    "type": "minimum_charge",
                    "description": "Minimum freight charge of $60.00",
                    "parameters": {"amount": "60.00"},
                    "source_page": 4,
                    "source_quote": "Shipment floor shall be established at sixty dollars ($60.00) per consignment.",
                    "confidence": 0.96,
                    "status": "proposed"
                },
                {
                    "id": "CCP-RULE-004",
                    "type": "duplicate_charge",
                    "description": "No duplicate billings",
                    "parameters": {"enabled": True},
                    "source_page": 5,
                    "source_quote": "Consignments will not be billed more than once.",
                    "confidence": 0.99,
                    "status": "proposed"
                },
                {
                    "id": "CCP-RULE-005",
                    "type": "claim_window_days",
                    "description": "120 days dispute window",
                    "parameters": {"days": 120},
                    "source_page": 5,
                    "source_quote": "Disputes must be raised within one hundred twenty (120) days of shipment dispatch.",
                    "confidence": 0.99,
                    "status": "proposed"
                }
            ],
            "clauses": [
                {
                    "title": "Section 2: Heavy Haul Tariff",
                    "paragraphs": [
                        "2.1 Freight Reductions",
                        "Net freight charges will reflect a thirty-eight percent (38.0%) reduction from benchmark tariff."
                    ]
                },
                {
                    "title": "Section 3: Accessorial Operations",
                    "paragraphs": [
                        "3.1 Mechanical Assistance",
                        "Liftgate equipment assistance will not exceed fifty dollars ($50.00) per bill of lading."
                    ]
                },
                {
                    "title": "Section 4: Shipment Minimums",
                    "paragraphs": [
                        "4.1 Revenue Floor",
                        "Shipment floor shall be established at sixty dollars ($60.00) per consignment."
                    ]
                },
                {
                    "title": "Section 5: Administrative Claims and Audits",
                    "paragraphs": [
                        "5.1 Duplicate Billings",
                        "Consignments will not be billed more than once.",
                        "5.2 Dispute Period",
                        "Disputes must be raised within one hundred twenty (120) days of shipment dispatch."
                    ]
                }
            ]
        }
    ]

    # Generate the 3 PDF contracts and save replay fixtures
    replay_dir = Path("backend/replay_cache")
    replay_dir.mkdir(parents=True, exist_ok=True)

    for cfg in contracts_config:
        pdf_path = CONTRACTS_DIR / cfg["pdf_filename"]
        generate_contract_pdf(pdf_path, cfg["carrier_name"], cfg["ref"], cfg["clauses"])

        # Cache replay fixture for instant offline demo resilience
        cache_key = f"contract_{cfg['carrier_name'].lower().replace(' ', '_')}.json"
        with open(replay_dir / cache_key, "w", encoding="utf-8") as f:
            json.dump({
                "data": {
                    "carrier_name": cfg["carrier_name"],
                    "contract_reference": cfg["ref"],
                    "effective_date": "2026-01-01",
                    "expiration_date": "2026-12-31",
                    "rules": cfg["rules"]
                },
                "metrics": {
                    "prompt_tokens": 1400,
                    "completion_tokens": 580,
                    "latency_ms": 610.0,
                    "tokens_per_second": 55.4
                }
            }, f, indent=2)

    # Generate 25 invoice batches (totaling ~1,250 invoice lines) with planted errors
    random.seed(42)
    planted_ground_truth: List[Dict[str, Any]] = []
    total_planted_overcharge = Decimal("0.00")

    batches_meta = []
    for batch_idx in range(1, 26):
        carrier_cfg = contracts_config[(batch_idx - 1) % len(contracts_config)]
        carrier_name = carrier_cfg["carrier_name"]
        batch_id = f"BATCH-{batch_idx:03d}"
        batch_filename = f"invoices_{carrier_name.lower().replace(' ', '_')}_b{batch_idx:02d}.csv"
        csv_path = INVOICES_DIR / batch_filename

        rows = []
        inv_base_date = date(2026, 8, 1) + timedelta(days=batch_idx)

        # 50 lines per batch = 1,250 lines total
        for line_idx in range(1, 51):
            line_id = f"L-{batch_idx:03d}-{line_idx:03d}"
            inv_num = f"INV-{carrier_name[:3].upper()}-{1000 + batch_idx*10 + (line_idx // 5)}"
            ship_id = f"TRK-{carrier_name[:3].upper()}-{50000 + batch_idx*100 + line_idx}"
            inv_date = inv_base_date.strftime("%Y-%m-%d")

            # Default clean line
            charge_code = "FRT"
            published = Decimal(f"{random.randint(80, 450)}.00")
            discount_pct = Decimal(str(carrier_cfg["rules"][0]["parameters"]["percentage"]))
            expected_amt = (published * (Decimal("1.0") - discount_pct)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            billed_amt = expected_amt
            fuel_pct = None
            is_planted = False
            planted_type = None
            overcharge_amount = Decimal("0.00")

            # Plant errors at deterministic positions (every 4th line)
            if line_idx % 4 == 0:
                is_planted = True
                error_choice = (line_idx // 4) % 5

                if error_choice == 0:
                    # 1. Base Discount Under-applied
                    planted_type = "base_discount"
                    # Carrier only applied half discount
                    bad_multiplier = Decimal("1.0") - (discount_pct / Decimal("2"))
                    billed_amt = (published * bad_multiplier).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                    overcharge_amount = billed_amt - expected_amt

                elif error_choice == 1:
                    # 2. Accessorial fee violation
                    planted_type = "accessorial_rule"
                    published = None
                    if carrier_name == "Apex Freight Logistics":
                        charge_code = "RES"
                        expected_amt = Decimal("0.00")
                        billed_amt = Decimal("24.50")
                        overcharge_amount = Decimal("24.50")
                    elif carrier_name == "Beacon Express Transport":
                        charge_code = "ADDRC"
                        expected_amt = Decimal("10.00")
                        billed_amt = Decimal("18.00")
                        overcharge_amount = Decimal("8.00")
                    else:
                        charge_code = "LFT"
                        expected_amt = Decimal("50.00")
                        billed_amt = Decimal("75.00")
                        overcharge_amount = Decimal("25.00")

                elif error_choice == 2:
                    # 3. Fuel surcharge inflated or minimum charge
                    fuel_rule = next((r for r in carrier_cfg["rules"] if r["type"] == "fuel_surcharge"), None)
                    if fuel_rule:
                        planted_type = "fuel_surcharge"
                        charge_code = "FSC"
                        published = None
                        fixed_fsc = Decimal(str(fuel_rule["parameters"]["fixed_percentage"]))
                        billed_fuel_pct = fixed_fsc + Decimal("0.05")  # 5% drift
                        fuel_pct = billed_fuel_pct * Decimal("100")
                        base_charge = Decimal("150.00")
                        billed_amt = (base_charge * billed_fuel_pct).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                        expected_amt = (base_charge * fixed_fsc).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                        overcharge_amount = billed_amt - expected_amt
                    else:
                        min_rule = next((r for r in carrier_cfg["rules"] if r["type"] == "minimum_charge"), None)
                        planted_type = "minimum_charge"
                        charge_code = "MIN"
                        published = None
                        agreed_min = Decimal(str(min_rule["parameters"]["amount"])) if min_rule else Decimal("50.00")
                        billed_amt = agreed_min + Decimal("20.00")
                        expected_amt = agreed_min
                        overcharge_amount = Decimal("20.00")

                elif error_choice == 3 and line_idx > 4:
                    # 4. Duplicate charge
                    planted_type = "duplicate_charge"
                    charge_code = "FRT"
                    # Reuse previous shipment ID
                    prev_ship_id = f"TRK-{carrier_name[:3].upper()}-{50000 + batch_idx*100 + (line_idx - 1)}"
                    ship_id = prev_ship_id
                    billed_amt = Decimal("65.00")
                    expected_amt = Decimal("0.00")
                    overcharge_amount = Decimal("65.00")

                elif error_choice == 4:
                    # 5. Minimum charge overbilled
                    min_rule = next((r for r in carrier_cfg["rules"] if r["type"] == "minimum_charge"), None)
                    if min_rule:
                        planted_type = "minimum_charge"
                        charge_code = "MIN"
                        published = None
                        agreed_min = Decimal(str(min_rule["parameters"]["amount"]))
                        billed_amt = agreed_min + Decimal("20.00")
                        expected_amt = agreed_min
                        overcharge_amount = Decimal("20.00")

            if is_planted and overcharge_amount > Decimal("0.00"):
                total_planted_overcharge += overcharge_amount
                planted_ground_truth.append({
                    "batch_id": batch_id,
                    "carrier_name": carrier_name,
                    "line_id": line_id,
                    "invoice_number": inv_num,
                    "shipment_id": ship_id,
                    "charge_code": charge_code,
                    "planted_rule_type": planted_type,
                    "expected_amount": f"{expected_amt:.2f}",
                    "billed_amount": f"{billed_amt:.2f}",
                    "overcharge_amount": f"{overcharge_amount:.2f}",
                })

            rows.append({
                "line_id": line_id,
                "invoice_number": inv_num,
                "invoice_date": inv_date,
                "shipment_id": ship_id,
                "charge_code": charge_code,
                "charge_description": f"{charge_code} charge",
                "service_level": "Standard LTL" if carrier_name == "Apex Freight Logistics" else "Ground",
                "published_rate": f"{published:.2f}" if published else "",
                "discount_applied_percent": "",
                "fuel_surcharge_percent": f"{fuel_pct:.1f}" if fuel_pct else "",
                "amount_billed": f"{billed_amt:.2f}"
            })

        # Write batch CSV
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        batches_meta.append({
            "batch_id": batch_id,
            "carrier_name": carrier_name,
            "filename": batch_filename,
            "total_lines": len(rows)
        })

    # Save Ground Truth JSON
    gt_payload = {
        "metadata": {
            "dataset_label": "synthetic demo data",
            "date_generated": date.today().strftime("%Y-%m-%d"),
            "total_contracts": len(contracts_config),
            "total_invoice_batches": len(batches_meta),
            "total_invoice_lines": len(batches_meta) * 50,
            "total_planted_errors_count": len(planted_ground_truth),
            "total_planted_overcharge_dollars": f"{total_planted_overcharge:.2f}"
        },
        "contracts": contracts_config,
        "batches": batches_meta,
        "planted_discrepancies": planted_ground_truth
    }

    with open(DATA_DIR / "ground_truth.json", "w", encoding="utf-8") as f:
        json.dump(gt_payload, f, indent=2)

    print(f"Generated {len(contracts_config)} synthetic contracts.")
    print(f"Generated {len(batches_meta)} invoice batches (total lines: {len(batches_meta)*50}).")
    print(f"Planted errors: {len(planted_ground_truth)} discrepancies (${total_planted_overcharge:.2f} total recoverable overcharge).")
    print(f"Ground truth written to: {DATA_DIR / 'ground_truth.json'}")


if __name__ == "__main__":
    build_synthetic_contracts_and_ground_truth()
