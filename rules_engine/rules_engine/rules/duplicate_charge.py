"""
Deterministic rule: Duplicate Charge Audit.
Identifies identical charges billed more than once for the same shipment ID.
Any secondary occurrence of the same charge code for the same shipment is a duplicate (expected = $0.00).
"""
from decimal import Decimal
from typing import Dict, List, Set, Optional
from rules_engine.types import RuleDefinition, NormalizedInvoiceLine, AuditDiscrepancy


def audit_duplicates(
    lines: List[NormalizedInvoiceLine],
    rule: RuleDefinition
) -> List[AuditDiscrepancy]:
    """
    Evaluates an entire batch of lines for duplicate charges per shipment.
    Returns discrepancies for all lines that repeat a (shipment_id, charge_code) combination.
    """
    discrepancies: List[AuditDiscrepancy] = []
    seen_charges: Set[str] = set()

    # Sort deterministically by date and line_id so the original is always preserved
    # and duplicates are flagged consistently regardless of input batch order.
    sorted_lines = sorted(lines, key=lambda l: (l.invoice_date or "", l.line_id or ""))

    for line in sorted_lines:
        key = f"{line.shipment_id}::{line.charge_code.upper()}"
        if key in seen_charges:
            # Duplicate detected!
            expected = Decimal("0.00")
            overcharge = line.amount_billed
            math_str = (
                f"Duplicate billing detected: shipment {line.shipment_id} was already billed for code {line.charge_code}. "
                f"Expected $0.00 vs Billed ${line.amount_billed:.2f}. Overcharge = ${overcharge:.2f}."
            )
            discrepancies.append(
                AuditDiscrepancy(
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
                    expected_amount=expected,
                    billed_amount=line.amount_billed,
                    overcharge_amount=overcharge,
                    calculation_math=math_str,
                )
            )
        else:
            seen_charges.add(key)

    return discrepancies
