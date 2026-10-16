"""
Deterministic Audit Engine.
Coordinates execution of all contractual rules against normalized invoice lines.
All calculations use Decimal arithmetic.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import date

from rules_engine.types import RuleDefinition, NormalizedInvoiceLine, AuditDiscrepancy
from rules_engine.rules.base_discount import audit_base_discount
from rules_engine.rules.accessorial import audit_accessorial
from rules_engine.rules.fuel_surcharge import audit_fuel_surcharge
from rules_engine.rules.dim_weight import audit_dim_weight
from rules_engine.rules.minimum_charge import audit_minimum_charge
from rules_engine.rules.duplicate_charge import audit_duplicates
from rules_engine.rules.claim_window import calculate_claim_deadline


@dataclass
class AuditResult:
    lines_audited: int
    discrepancies: List[AuditDiscrepancy]
    total_overcharge: Decimal
    by_category: Dict[str, Decimal] = field(default_factory=dict)


class AuditEngine:
    """
    Pure Python deterministic audit engine.
    Never uses floats or LLMs for calculations.
    """

    def __init__(self, rules: List[RuleDefinition], reference_date: Optional[date] = None):
        # Filter for approved rules only
        self.rules = [r for r in rules if r.status == "approved"]
        self.reference_date = reference_date

        # Extract claim window rule if present to annotate deadlines
        self.claim_rule: Optional[RuleDefinition] = next(
            (r for r in self.rules if r.type == "claim_window_days"), None
        )

    def audit(self, lines: List[NormalizedInvoiceLine]) -> AuditResult:
        discrepancies: List[AuditDiscrepancy] = []

        # 1. Run multi-line rules first (e.g. duplicate charges) so 100% full-line overcharges take precedence
        dup_rules = [r for r in self.rules if r.type == "duplicate_charge"]
        duplicate_line_ids = set()
        for rule in dup_rules:
            dup_discs = audit_duplicates(lines, rule)
            for disc in dup_discs:
                if self.claim_rule and not disc.claim_deadline_date:
                    dl, rem = calculate_claim_deadline(
                        disc.invoice_date, self.claim_rule, self.reference_date
                    )
                    disc = AuditDiscrepancy(
                        line_id=disc.line_id,
                        shipment_id=disc.shipment_id,
                        invoice_number=disc.invoice_number,
                        invoice_date=disc.invoice_date,
                        charge_code=disc.charge_code,
                        rule_id=disc.rule_id,
                        rule_type=disc.rule_type,
                        rule_description=disc.rule_description,
                        contract_page=disc.contract_page,
                        contract_clause_quote=disc.contract_clause_quote,
                        expected_amount=disc.expected_amount,
                        billed_amount=disc.billed_amount,
                        overcharge_amount=disc.overcharge_amount,
                        calculation_math=disc.calculation_math,
                        claim_deadline_date=dl,
                        days_remaining_to_claim=rem,
                    )
                discrepancies.append(disc)
                duplicate_line_ids.add(disc.line_id)

        # 2. Run single-line rules on lines not already flagged as duplicates
        for line in lines:
            if line.line_id in duplicate_line_ids:
                # Line is already flagged as a 100% duplicate charge (expected $0.00)
                continue
            line_flagged = False
            for rule in self.rules:
                disc: Optional[AuditDiscrepancy] = None

                if rule.type == "base_discount":
                    disc = audit_base_discount(line, rule)
                elif rule.type == "accessorial_rule":
                    disc = audit_accessorial(line, rule)
                elif rule.type == "fuel_surcharge":
                    disc = audit_fuel_surcharge(line, rule)
                elif rule.type == "dim_weight_divisor":
                    disc = audit_dim_weight(line, rule)
                elif rule.type == "minimum_charge":
                    disc = audit_minimum_charge(line, rule)

                if disc:
                    # Enrich with claim deadline if claim window rule exists
                    if self.claim_rule and not disc.claim_deadline_date:
                        dl, rem = calculate_claim_deadline(
                            disc.invoice_date, self.claim_rule, self.reference_date
                        )
                        disc = AuditDiscrepancy(
                            line_id=disc.line_id,
                            shipment_id=disc.shipment_id,
                            invoice_number=disc.invoice_number,
                            invoice_date=disc.invoice_date,
                            charge_code=disc.charge_code,
                            rule_id=disc.rule_id,
                            rule_type=disc.rule_type,
                            rule_description=disc.rule_description,
                            contract_page=disc.contract_page,
                            contract_clause_quote=disc.contract_clause_quote,
                            expected_amount=disc.expected_amount,
                            billed_amount=disc.billed_amount,
                            overcharge_amount=disc.overcharge_amount,
                            calculation_math=disc.calculation_math,
                            claim_deadline_date=dl,
                            days_remaining_to_claim=rem,
                        )

                    discrepancies.append(disc)
                    line_flagged = True
                    # Stop after first matching rule per line to avoid double-claiming the same line
                    break

        # 3. Calculate category totals & aggregate overcharge
        total_overcharge = Decimal("0.00")
        by_category: Dict[str, Decimal] = {}

        for d in discrepancies:
            total_overcharge += d.overcharge_amount
            by_category[d.rule_type] = by_category.get(d.rule_type, Decimal("0.00")) + d.overcharge_amount

        return AuditResult(
            lines_audited=len(lines),
            discrepancies=discrepancies,
            total_overcharge=total_overcharge,
            by_category=by_category,
        )
