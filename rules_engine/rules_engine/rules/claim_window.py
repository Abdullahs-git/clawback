"""
Deterministic rule: Claim Window & Dispute Deadline Audit.
Calculates claim deadline dates based on contractual claim_window_days (e.g. 180 days).
Flags invoices that exceed dispute windows or are within urgent expiration thresholds.
"""
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
from rules_engine.types import RuleDefinition, NormalizedInvoiceLine, AuditDiscrepancy


def calculate_claim_deadline(
    invoice_date_str: str,
    rule: RuleDefinition,
    reference_date: Optional[date] = None
) -> Tuple[Optional[str], Optional[int]]:
    """
    Computes (claim_deadline_date, days_remaining).
    Parameters in rule:
      - days: int (e.g. 180)
    """
    days = rule.parameters.get("days")
    if not days:
        return None, None

    try:
        inv_dt = datetime.strptime(invoice_date_str, "%Y-%m-%d").date()
    except Exception:
        return None, None

    deadline = inv_dt + timedelta(days=int(days))
    ref_dt = reference_date or date.today()
    days_remaining = (deadline - ref_dt).days

    return deadline.strftime("%Y-%m-%d"), days_remaining


def audit_claim_window_expiration(
    line: NormalizedInvoiceLine,
    rule: RuleDefinition,
    reference_date: Optional[date] = None
) -> Optional[AuditDiscrepancy]:
    """
    If a carrier invoices a line after the contractual dispute/billing window has already closed.
    """
    deadline_str, days_remaining = calculate_claim_deadline(line.invoice_date, rule, reference_date)
    if deadline_str is None or days_remaining is None:
        return None

    # If carrier is attempting to bill or if dispute window is already expired
    if days_remaining < 0:
        overcharge = line.amount_billed
        math_str = (
            f"Contractual dispute window is {rule.parameters.get('days')} days. "
            f"Claim deadline was {deadline_str} ({abs(days_remaining)} days ago). "
            f"Billed amount ${line.amount_billed:.2f} is time-barred."
        )
        return AuditDiscrepancy(
            line_id=line.line_id,
            shipment_id=line.shipment_id,
            invoice_number=line.invoice_number,
            invoice_date=line.invoice_date,
            charge_code=line.charge_code,
            rule_id=rule.id,
            rule_type=rule.type,
            rule_description=rule.description,
            contract_page=rule.source_page,
            contract_clause_quote=rule.source_quote,
            expected_amount=line.amount_billed,
            billed_amount=line.amount_billed,
            overcharge_amount=overcharge,
            calculation_math=math_str,
            claim_deadline_date=deadline_str,
            days_remaining_to_claim=days_remaining,
        )

    return None
