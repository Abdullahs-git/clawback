"""
Audit Execution & Findings API Router.
Runs the pure Python deterministic audit engine and provides findings queries.
"""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.contract import Contract, ContractRule
from backend.app.models.invoice import InvoiceBatch, InvoiceLine
from backend.app.models.finding import AuditFinding
from backend.app.schemas.finding import (
    AuditRunRequest,
    AuditRunResult,
    AuditFindingDetail,
    AuditFindingsOverview
)
from rules_engine.engine import AuditEngine
from rules_engine.types import RuleDefinition, NormalizedInvoiceLine

router = APIRouter(prefix="/api/audit", tags=["Audit & Findings"])

TWO_PLACES = Decimal("0.01")


@router.post("/run", response_model=AuditRunResult)
def execute_audit(payload: AuditRunRequest, db: Session = Depends(get_db)):
    """
    Executes the deterministic audit engine on the specified invoice batch
    against approved rules from the selected carrier contract.
    """
    contract = db.query(Contract).filter(Contract.id == payload.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")

    batch = db.query(InvoiceBatch).filter(InvoiceBatch.id == payload.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Invoice batch not found.")

    # 1. Fetch approved rules only
    approved_rules_db = db.query(ContractRule).filter(
        ContractRule.contract_id == payload.contract_id,
        ContractRule.status == "approved"
    ).all()

    if not approved_rules_db:
        raise HTTPException(
            status_code=400,
            detail="Contract has no approved rules. Please review and approve contract rules first."
        )

    engine_rules: List[RuleDefinition] = []
    for r in approved_rules_db:
        engine_rules.append(
            RuleDefinition(
                id=r.id,
                type=r.type,
                description=r.description,
                parameters=r.parameters or {},
                source_page=r.source_page,
                source_quote=r.source_quote,
                confidence=r.confidence,
                status=r.status
            )
        )

    # 2. Fetch invoice lines
    db_lines = db.query(InvoiceLine).filter(InvoiceLine.batch_id == payload.batch_id).all()
    if not db_lines:
        raise HTTPException(status_code=400, detail="Invoice batch contains no line items.")

    engine_lines: List[NormalizedInvoiceLine] = []
    for l in db_lines:
        def to_dec(val):
            if val is not None and str(val).strip() != "":
                try:
                    return Decimal(str(val).strip())
                except Exception:
                    return None
            return None

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

    # 3. Execute pure deterministic AuditEngine
    engine = AuditEngine(engine_rules)
    audit_res = engine.audit(engine_lines)

    # 4. Clear prior findings for this batch/contract
    db.query(AuditFinding).filter(
        AuditFinding.batch_id == payload.batch_id,
        AuditFinding.contract_id == payload.contract_id
    ).delete()

    # 5. Persist audit discrepancies
    for d in audit_res.discrepancies:
        finding = AuditFinding(
            batch_id=payload.batch_id,
            contract_id=payload.contract_id,
            carrier_name=batch.carrier_name,
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

    db.commit()

    return AuditRunResult(
        batch_id=payload.batch_id,
        contract_id=payload.contract_id,
        lines_audited=audit_res.lines_audited,
        discrepancies_count=len(audit_res.discrepancies),
        total_overcharge_amount=f"{audit_res.total_overcharge:.2f}",
        completed_at=datetime.now(timezone.utc)
    )


@router.get("/findings", response_model=AuditFindingsOverview)
def list_findings(
    batch_id: Optional[str] = None,
    carrier_name: Optional[str] = None,
    rule_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns audit findings with aggregate totals by category and carrier.
    Powers the dashboard's hero metric and findings table.
    """
    query = db.query(AuditFinding)
    if batch_id:
        query = query.filter(AuditFinding.batch_id == batch_id)
    if carrier_name:
        query = query.filter(AuditFinding.carrier_name.ilike(f"%{carrier_name}%"))
    if rule_type:
        query = query.filter(AuditFinding.rule_type == rule_type)
    if status:
        query = query.filter(AuditFinding.status == status)

    findings = query.order_by(AuditFinding.created_at.desc()).all()

    total_overcharge = Decimal("0.00")
    by_category: Dict[str, Decimal] = {}
    by_carrier: Dict[str, Decimal] = {}

    out_findings = []
    for f in findings:
        over_dec = Decimal(f.overcharge_amount)
        total_overcharge += over_dec
        by_category[f.rule_type] = by_category.get(f.rule_type, Decimal("0.00")) + over_dec
        by_carrier[f.carrier_name] = by_carrier.get(f.carrier_name, Decimal("0.00")) + over_dec

        out_findings.append(
            AuditFindingDetail(
                finding_id=f.id,
                batch_id=f.batch_id,
                contract_id=f.contract_id,
                carrier_name=f.carrier_name,
                invoice_number=f.invoice_number,
                invoice_date=f.invoice_date,
                line_id=f.line_id,
                shipment_id=f.shipment_id,
                charge_code=f.charge_code,
                rule_id=f.rule_id,
                rule_type=f.rule_type,
                rule_description=f.rule_description,
                contract_page=f.contract_page,
                contract_clause_quote=f.contract_clause_quote,
                expected_amount=f.expected_amount,
                billed_amount=f.billed_amount,
                overcharge_amount=f.overcharge_amount,
                calculation_math=f.calculation_math,
                claim_deadline_date=f.claim_deadline_date,
                days_remaining_to_claim=f.days_remaining_to_claim,
                status=f.status,
                created_at=f.created_at
            )
        )

    return AuditFindingsOverview(
        total_overcharge=f"{total_overcharge:.2f}",
        total_findings_count=len(findings),
        by_category={k: f"{v:.2f}" for k, v in by_category.items()},
        by_carrier={k: f"{v:.2f}" for k, v in by_carrier.items()},
        findings=out_findings
    )


@router.get("/findings/{finding_id}", response_model=AuditFindingDetail)
def get_finding_detail(finding_id: str, db: Session = Depends(get_db)):
    """Drills down into a single finding for full traceability."""
    f = db.query(AuditFinding).filter(AuditFinding.id == finding_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Finding not found.")

    return AuditFindingDetail(
        finding_id=f.id,
        batch_id=f.batch_id,
        contract_id=f.contract_id,
        carrier_name=f.carrier_name,
        invoice_number=f.invoice_number,
        invoice_date=f.invoice_date,
        line_id=f.line_id,
        shipment_id=f.shipment_id,
        charge_code=f.charge_code,
        rule_id=f.rule_id,
        rule_type=f.rule_type,
        rule_description=f.rule_description,
        contract_page=f.contract_page,
        contract_clause_quote=f.contract_clause_quote,
        expected_amount=f.expected_amount,
        billed_amount=f.billed_amount,
        overcharge_amount=f.overcharge_amount,
        calculation_math=f.calculation_math,
        claim_deadline_date=f.claim_deadline_date,
        days_remaining_to_claim=f.days_remaining_to_claim,
        status=f.status,
        created_at=f.created_at
    )
