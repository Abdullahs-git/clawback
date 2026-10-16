"""
Deterministic rule: Dimensional Weight Divisor Audit.
Checks if carrier billed weight based on an improper dimensional divisor.
DIM Weight = (Length * Width * Height) / Divisor.
If contract specifies divisor 166, but carrier used 139, shipper is overbilled on weight.
"""
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING
from typing import Optional
from rules_engine.types import RuleDefinition, NormalizedInvoiceLine, AuditDiscrepancy

TWO_PLACES = Decimal("0.01")


def audit_dim_weight(
    line: NormalizedInvoiceLine,
    rule: RuleDefinition
) -> Optional[AuditDiscrepancy]:
    """
    Evaluates whether dimensional weight was computed using contractual divisor.
    Parameters in rule:
      - divisor: int/float/Decimal (e.g. 166 or 139)
    """
    if line.charge_code.upper() not in ["FRT", "BASE", "FREIGHT", "LINEHAUL"]:
        return None

    divisor_val = rule.parameters.get("divisor")
    if not divisor_val:
        return None

    contract_divisor = Decimal(str(divisor_val))

    # Needs dimensional measurements
    if not (line.dim_length_in and line.dim_width_in and line.dim_height_in and line.billed_weight_lbs):
        return None

    # Compute expected dim weight in lbs
    cubic_inches = line.dim_length_in * line.dim_width_in * line.dim_height_in
    expected_dim_weight = (cubic_inches / contract_divisor).quantize(Decimal("1"), rounding=ROUND_CEILING)

    # Actual weight
    actual_wt = line.weight_actual_lbs or Decimal("0")
    expected_billable_wt = max(actual_wt, expected_dim_weight)

    # If carrier billed more weight than contractual formula allows
    if line.billed_weight_lbs > expected_billable_wt and line.billed_weight_lbs > Decimal("0"):
        # Rate per lb billed
        rate_per_lb = line.amount_billed / line.billed_weight_lbs
        expected_amount = (expected_billable_wt * rate_per_lb).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        overcharge = (line.amount_billed - expected_amount).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        if overcharge > Decimal("0.00"):
            math_str = (
                f"Contract DIM divisor is {contract_divisor}. Cubic in {cubic_inches:.1f} / {contract_divisor} = {expected_dim_weight} lbs. "
                f"Expected billable weight {expected_billable_wt} lbs vs Billed {line.billed_weight_lbs} lbs. "
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
