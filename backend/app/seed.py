"""
Seed script to pre-populate database with synthetic carrier contracts,
approved rules, and invoice batches so the demo is ready out of the box.
"""
from decimal import Decimal
import json
from pathlib import Path
import uuid
from sqlalchemy.orm import Session

from backend.app.database import engine, Base, SessionLocal
from backend.app.models.contract import Contract, ContractRule
from backend.app.models.invoice import InvoiceBatch, InvoiceLine
from backend.app.models.finding import AuditFinding
from backend.app.models.dispute import DisputeLetter
from backend.app.models.amd_metric import AmdMetricLog
from backend.app.services.dispute import generate_dispute_letter_content
from rules_engine.engine import AuditEngine
from rules_engine.types import RuleDefinition, NormalizedInvoiceLine

DATA_DIR = Path("benchmark/data")


def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    print("Seeding database with synthetic demo dataset...")

    # Clear old data for a fresh clean state
    db.query(AuditFinding).delete()
    db.query(DisputeLetter).delete()
    db.query(InvoiceLine).delete()
    db.query(InvoiceBatch).delete()
    db.query(ContractRule).delete()
    db.query(Contract).delete()
    db.query(AmdMetricLog).delete()
    db.commit()

    gt_file = DATA_DIR / "ground_truth.json"
    if not gt_file.exists():
        print("Ground truth not found. Running generator first...")
        from benchmark.generator import build_synthetic_contracts_and_ground_truth
        build_synthetic_contracts_and_ground_truth()

    with open(gt_file, "r", encoding="utf-8") as f:
        gt = json.load(f)

    # 1. Seed Contracts and Rules
    carrier_contract_map = {}
    for c_cfg in gt["contracts"]:
        contract_id = str(uuid.uuid4())
        carrier_name = c_cfg["carrier_name"]
        contract = Contract(
            id=contract_id,
            carrier_name=carrier_name,
            filename=c_cfg["pdf_filename"],
            file_path=str(DATA_DIR / "contracts" / c_cfg["pdf_filename"]),
            contract_reference=c_cfg["ref"],
            effective_date="2026-01-01",
            expiration_date="2026-12-31"
        )
        db.add(contract)

        rules_list = []
        for r in c_cfg["rules"]:
            rule_id = f"{contract_id[:8]}-{r['id']}"
            rule = ContractRule(
                id=rule_id,
                contract_id=contract_id,
                type=r["type"],
                description=r["description"],
                parameters=r["parameters"],
                source_page=r["source_page"],
                source_quote=r["source_quote"],
                confidence=r.get("confidence", 0.98),
                status="approved"  # Pre-approved for demo readiness
            )
            db.add(rule)
            rules_list.append(rule)

        carrier_contract_map[carrier_name] = {
            "contract": contract,
            "rules": rules_list
        }

    # 2. Seed Invoice Batches and Line Items
    from backend.app.api.invoices import parse_csv_invoices

    for b_meta in gt["batches"]:
        batch_id = b_meta["batch_id"]
        carrier_name = b_meta["carrier_name"]
        csv_file = DATA_DIR / "invoices" / b_meta["filename"]

        with open(csv_file, "r", encoding="utf-8") as f:
            csv_text = f.read()

        lines = parse_csv_invoices(csv_text, batch_id)
        total_billed = sum(Decimal(line.amount_billed) for line in lines)

        batch = InvoiceBatch(
            id=batch_id,
            carrier_name=carrier_name,
            filename=b_meta["filename"],
            file_path=str(csv_file),
            total_lines=len(lines),
            total_billed_amount=f"{total_billed:.2f}"
        )
        db.add(batch)
        for line in lines:
            db.add(line)

    db.commit()

    # 3. Run Deterministic Audit Engine across all batches
    total_findings_count = 0
    all_findings_for_apex = []

    for carrier_name, c_data in carrier_contract_map.items():
        contract = c_data["contract"]
        rules = c_data["rules"]

        engine_rules = [
            RuleDefinition(
                id=r.id,
                type=r.type,
                description=r.description,
                parameters=r.parameters,
                source_page=r.source_page,
                source_quote=r.source_quote,
                confidence=r.confidence,
                status=r.status
            )
            for r in rules
        ]
        audit_engine = AuditEngine(engine_rules)

        carrier_batches = db.query(InvoiceBatch).filter(InvoiceBatch.carrier_name == carrier_name).all()
        for b in carrier_batches:
            db_lines = db.query(InvoiceLine).filter(InvoiceLine.batch_id == b.id).all()
            engine_lines = [
                NormalizedInvoiceLine(
                    line_id=l.id,
                    invoice_number=l.invoice_number,
                    invoice_date=l.invoice_date,
                    shipment_id=l.shipment_id,
                    charge_code=l.charge_code,
                    amount_billed=Decimal(l.amount_billed),
                    charge_description=l.charge_description,
                    service_level=l.service_level,
                    published_rate=Decimal(l.published_rate) if l.published_rate else None,
                    fuel_surcharge_percent=Decimal(l.fuel_surcharge_percent) if l.fuel_surcharge_percent else None,
                )
                for l in db_lines
            ]

            res = audit_engine.audit(engine_lines)
            for d in res.discrepancies:
                finding = AuditFinding(
                    batch_id=b.id,
                    contract_id=contract.id,
                    carrier_name=carrier_name,
                    invoice_number=d.invoice_number,
                    invoice_date=d.invoice_date,
                    line_id=d.line_id,
                    shipment_id=d.shipment_id,
                    charge_code=d.charge_code,
                    rule_id=d.rule_id,
                    rule_type=d.rule_type,
                    rule_description=d.rule_description,
                    contract_page=d.contract_page,
                    contract_clause_quote=d.contract_clause_quote,
                    expected_amount=f"{d.expected_amount:.2f}",
                    billed_amount=f"{d.billed_amount:.2f}",
                    overcharge_amount=f"{d.overcharge_amount:.2f}",
                    calculation_math=d.calculation_math,
                    claim_deadline_date=d.claim_deadline_date,
                    days_remaining_to_claim=d.days_remaining_to_claim,
                    status="open"
                )
                db.add(finding)
                total_findings_count += 1
                if carrier_name == "Apex Freight Logistics" and b.id == "BATCH-001":
                    all_findings_for_apex.append(finding)

    db.commit()

    # 4. Seed sample Dispute Letter
    if all_findings_for_apex:
        letter_dict = generate_dispute_letter_content(
            carrier_name="Apex Freight Logistics",
            shipper_name="Acme Logistics & AP",
            findings=all_findings_for_apex
        )
        dispute_letter = DisputeLetter(
            id=str(uuid.uuid4()),
            batch_id="BATCH-001",
            carrier_name="Apex Freight Logistics",
            carrier_contact_email="disputes@apexfreight.com",
            shipper_name="Acme Logistics & AP",
            date_generated=letter_dict["date_generated"],
            earliest_deadline_date=letter_dict["earliest_deadline_date"],
            total_claim_amount=letter_dict["total_claim_amount"],
            total_disputed_items=letter_dict["total_disputed_items"],
            subject_line=letter_dict["subject_line"],
            body_markdown=letter_dict["body_markdown"],
            evidence_table=letter_dict["evidence_table"],
            status="draft"
        )
        db.add(dispute_letter)
        db.commit()

    # 5. Seed AMD Metric Logs for Telemetry Panel
    for carrier_name in carrier_contract_map.keys():
        log = AmdMetricLog(
            operation="contract_extraction",
            model_name="google/gemma-2-9b-it",
            endpoint_host="notebooks.amd.com",
            latency_ms=642.5,
            prompt_tokens=1420,
            completion_tokens=580,
            tokens_per_second=58.5,
            mode="replay",
            status="success"
        )
        db.add(log)

    db.commit()
    db.close()

    print(f"Database seeded successfully with {len(carrier_contract_map)} contracts, {len(gt['batches'])} batches, and {total_findings_count} audit findings!")


if __name__ == "__main__":
    seed_database()
