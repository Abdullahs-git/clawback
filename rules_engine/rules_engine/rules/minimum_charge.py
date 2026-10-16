"""
Deterministic rule: Minimum Charge Audit.
Validates that minimum charges billed do not exceed contractual minimum charge floors.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from rules_engine.types import RuleDefinition, NormalizedInvoiceLine, AuditDiscrepancy

TWO_PLACES = Decimal("0.01")


def audit_minimum_charge(
    line: NormalizedInvoiceLine,
    rule: RuleDefinition
) -> Optional[AuditDiscrepancy]:
    """
    Evaluates whether an applied minimum charge exceeds the contractual cap or agreed rate.
    Parameters in rule:
      - amount: Decimal/str/float (e.g. 45.00)
      - service_level: optional str
    """
    rule_service = rule.parameters.get("service_level")
    if rule_service and line.service_level and rule_service.upper() != line.service_level.upper():
        return None

    is_min_charge = (
        line.charge_code.upper() in ["MIN", "MIN_CHARGE", "MC"]
        or (line.charge_description and "minimum charge" in line.charge_description.lower())
    )

    if not is_min_charge:
        return None

    agreed_min_raw = rule.parameters.get("amount")
    if agreed_min_raw is None:
        return None

    agreed_min = Decimal(str(agreed_min_raw)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    if line.amount_billed > agreed_min:
        overcharge = (line.amount_billed - agreed_min).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        math_str = (
            f"Contractual minimum charge floor is ${agreed_min:.2f}. Billed ${line.amount_billed:.2f}. "
            f"Overcharge = ${overcharge:.2f}."
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
            expected_amount=agreed_min,
            billed_amount=line.amount_billed,
            overcharge_amount=overcharge,
            calculation_math=math_str,
        )

    return None
