"""
Deterministic rule: Fuel Surcharge Audit.
Validates fuel surcharge percentage or billed amount against contractual fuel tables or agreed rate caps.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from rules_engine.types import RuleDefinition, NormalizedInvoiceLine, AuditDiscrepancy

TWO_PLACES = Decimal("0.01")


def audit_fuel_surcharge(
    line: NormalizedInvoiceLine,
    rule: RuleDefinition
) -> Optional[AuditDiscrepancy]:
    """
    Evaluates whether fuel surcharge was billed according to contractual terms.
    Parameters in rule:
      - fixed_percentage: Decimal or str (e.g. "0.12" for 12%)
      - max_percentage: Decimal or str
      - table: list of dicts [{'min_price': x, 'max_price': y, 'percentage': z}]
    """
    if line.charge_code.upper() not in ["FSC", "FUEL", "FUEL_SURCHARGE"]:
        return None

    # Check agreed maximum or fixed percentage
    target_pct = None
    if "fixed_percentage" in rule.parameters:
        target_pct = Decimal(str(rule.parameters["fixed_percentage"]))
    elif "max_percentage" in rule.parameters:
        target_pct = Decimal(str(rule.parameters["max_percentage"]))

    if target_pct is not None and target_pct > Decimal("1.0"):
        target_pct = target_pct / Decimal("100")

    # If line has fuel_surcharge_percent specified
    if target_pct is not None and line.fuel_surcharge_percent is not None:
        billed_pct = line.fuel_surcharge_percent
        if billed_pct > Decimal("1.0"):
            billed_pct = billed_pct / Decimal("100")

        if billed_pct > target_pct:
            # Overcharge calculation:
            # billed_amount is based on billed_pct; expected_amount = billed_amount * (target_pct / billed_pct)
            expected_amount = (line.amount_billed * (target_pct / billed_pct)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            overcharge = (line.amount_billed - expected_amount).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            math_str = (
                f"Contractual fuel surcharge is {target_pct * 100:.2f}%. Billed fuel surcharge was {billed_pct * 100:.2f}%. "
                f"Expected ${expected_amount:.2f} vs Billed ${line.amount_billed:.2f}. Overcharge = ${overcharge:.2f}."
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
                expected_amount=expected_amount,
                billed_amount=line.amount_billed,
                overcharge_amount=overcharge,
                calculation_math=math_str,
            )

    return None
