"""
Deterministic rule: Base Discount Audit.
Evaluates freight line items against the contractual discount percentage.
All calculations use Decimal.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from rules_engine.types import RuleDefinition, NormalizedInvoiceLine, AuditDiscrepancy

TWO_PLACES = Decimal("0.01")


def audit_base_discount(
    line: NormalizedInvoiceLine,
    rule: RuleDefinition
) -> Optional[AuditDiscrepancy]:
    """
    Evaluates whether the base freight discount was honored.
    Expected: line.published_rate * (1 - discount_percent)
    If amount_billed > expected + threshold, returns AuditDiscrepancy.
    """
    if line.charge_code.upper() not in ["FRT", "BASE", "FREIGHT", "LINEHAUL"]:
        return None

    # Check if rule specifies service level or lane constraints
    rule_service = rule.parameters.get("service_level")
    if rule_service and line.service_level and rule_service.upper() != line.service_level.upper():
        return None

    # Discount percentage (e.g., 0.40 or "40" or "0.40")
    discount_raw = rule.parameters.get("percentage")
    if discount_raw is None:
        return None

    discount_pct = Decimal(str(discount_raw))
    if discount_pct > Decimal("1.0"):  # e.g., 40.0 means 40%
        discount_pct = discount_pct / Decimal("100")

    # If line has published rate, compute from published rate; else if invoice shows discount_applied_percent < rule
    if line.published_rate is not None and line.published_rate > Decimal("0"):
        expected_multiplier = Decimal("1.0") - discount_pct
        expected_amount = (line.published_rate * expected_multiplier).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    elif line.discount_applied_percent is not None:
        # Invoice states applied discount: check if less than agreed
        applied = line.discount_applied_percent
        if applied > Decimal("1.0"):
            applied = applied / Decimal("100")
        if applied < discount_pct:
            # Reconstruct published from billed / (1 - applied)
            implied_published = line.amount_billed / (Decimal("1.0") - applied)
            expected_amount = (implied_published * (Decimal("1.0") - discount_pct)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        else:
            return None
    else:
        return None

    # Overcharge check
    if line.amount_billed > expected_amount:
        overcharge = (line.amount_billed - expected_amount).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        math_str = (
            f"Agreed discount {discount_pct * 100:.1f}%. Expected ${expected_amount:.2f} "
            f"vs Billed ${line.amount_billed:.2f}. Overcharge = ${overcharge:.2f}"
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
