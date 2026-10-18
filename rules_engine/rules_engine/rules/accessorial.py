"""
Deterministic rule: Accessorial Fees Audit.
Audits accessorial charges (e.g., Residential Surcharge, Liftgate, Address Correction, Inside Delivery)
against agreed contractual caps, waivers, or fixed rates.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from rules_engine.types import RuleDefinition, NormalizedInvoiceLine, AuditDiscrepancy

TWO_PLACES = Decimal("0.01")


def audit_accessorial(
    line: NormalizedInvoiceLine,
    rule: RuleDefinition
) -> Optional[AuditDiscrepancy]:
    """
    Evaluates whether an accessorial charge is allowed, capped, or waived.
    Parameters in rule:
      - fee_type: str (e.g. "residential", "liftgate", "address_correction", "inside_delivery")
      - allowed: bool (if False, fee is waived -> expected = $0.00)
      - cap: Decimal/str (maximum allowed fee)
      - rate: Decimal/str (fixed agreed rate)
    """
    fee_type = str(rule.parameters.get("fee_type", "")).lower()
    if not fee_type:
        return None

    # Check if invoice line matches this fee type either via charge_code or charge_description
    code_match = fee_type in line.charge_code.lower()
    desc_match = line.charge_description and fee_type in line.charge_description.lower()

    # Common code mappings
    type_code_map = {
        "residential": ["res", "res_del", "residential"],
        "liftgate": ["lft", "lift", "liftgate", "lfg"],
        "address_correction": ["addr", "addrc", "address_corr"],
        "inside_delivery": ["ins", "inside", "inside_del"],
        "saturday_delivery": ["sat", "sat_del", "saturday"],
    }

    mapped_codes = type_code_map.get(fee_type, [fee_type])
    is_matching = (
        code_match or desc_match or any(c in line.charge_code.lower() for c in mapped_codes)
    )

    if not is_matching:
        return None

    allowed = rule.parameters.get("allowed", True)
    cap_val = rule.parameters.get("cap")
    rate_val = rule.parameters.get("rate")

    expected_amount = line.amount_billed
    math_str = ""

    if allowed is False:
        # Fee is waived or strictly disallowed
        expected_amount = Decimal("0.00")
        overcharge = line.amount_billed
        math_str = f"Fee type '{fee_type}' is waived/disallowed per contract. Expected $0.00 vs Billed ${line.amount_billed:.2f}."
    elif cap_val is not None:
        cap = Decimal(str(cap_val)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        if line.amount_billed > cap:
            expected_amount = cap
            overcharge = (line.amount_billed - cap).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            math_str = f"Fee type '{fee_type}' is capped at ${cap:.2f}. Billed ${line.amount_billed:.2f}. Overcharge = ${overcharge:.2f}."
        else:
            return None
    elif rate_val is not None:
        rate = Decimal(str(rate_val)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        if line.amount_billed > rate:
            expected_amount = rate
            overcharge = (line.amount_billed - rate).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            math_str = f"Agreed fixed rate for '{fee_type}' is ${rate:.2f}. Billed ${line.amount_billed:.2f}. Overcharge = ${overcharge:.2f}."
        else:
            return None
    else:
        return None

    if overcharge > Decimal("0.00"):
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
