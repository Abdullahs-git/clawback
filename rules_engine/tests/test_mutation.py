"""
Mutation Testing for Deterministic Rules Engine.
Asserts that mutating exactly one rule parameter modifies only the discrepancies
for that specific rule, leaving all other findings, categories, and unaffected
lines completely invariant.
"""
from decimal import Decimal
import pytest

from rules_engine.engine import AuditEngine
from rules_engine.types import RuleDefinition, NormalizedInvoiceLine


@pytest.fixture
def sample_rules_and_lines():
    rules = [
        RuleDefinition(
            id="R-DISC-01",
            type="base_discount",
            description="45% base discount",
            parameters={"percentage": Decimal("0.45")},
            source_page=2,
            source_quote="Shipper shall receive 45.0% discount.",
            status="approved",
        ),
        RuleDefinition(
            id="R-LIFT-02",
            type="accessorial_rule",
            description="Liftgate cap $40.00",
            parameters={"fee_type": "liftgate", "cap": Decimal("40.00")},
            source_page=3,
            source_quote="Liftgate shall not exceed $40.00.",
            status="approved",
        ),
        RuleDefinition(
            id="R-FUEL-03",
            type="fuel_surcharge",
            description="Fuel surcharge 11.5%",
            parameters={"fixed_percentage": Decimal("0.115")},
            source_page=4,
            source_quote="Fuel surcharge fixed at 11.5%.",
            status="approved",
        ),
    ]

    lines = [
        # Line 1: Discount overcharge (Published $100, Billed $65 -> expected $55, overcharge $10)
        NormalizedInvoiceLine(
            line_id="L-1",
            invoice_number="INV-1",
            invoice_date="2026-03-01",
            shipment_id="SHP-1",
            charge_code="FRT",
            amount_billed=Decimal("65.00"),
            published_rate=Decimal("100.00"),
        ),
        # Line 2: Liftgate overcharge (Billed $55 -> cap $40, overcharge $15)
        NormalizedInvoiceLine(
            line_id="L-2",
            invoice_number="INV-1",
            invoice_date="2026-03-01",
            shipment_id="SHP-1",
            charge_code="LFT",
            amount_billed=Decimal("55.00"),
        ),
        # Line 3: Fuel overcharge (Billed $20 with FSC 20% on $100 -> expected 11.5% = $11.50, overcharge $8.50)
        NormalizedInvoiceLine(
            line_id="L-3",
            invoice_number="INV-1",
            invoice_date="2026-03-01",
            shipment_id="SHP-1",
            charge_code="FSC",
            amount_billed=Decimal("20.00"),
            fuel_surcharge_percent=Decimal("0.20"),
        ),
        # Line 4: Compliant line (Billed liftgate at $35 <= $40)
        NormalizedInvoiceLine(
            line_id="L-4",
            invoice_number="INV-1",
            invoice_date="2026-03-01",
            shipment_id="SHP-2",
            charge_code="LFT",
            amount_billed=Decimal("35.00"),
        ),
    ]

    return rules, lines


def test_mutation_liftgate_cap(sample_rules_and_lines):
    rules, lines = sample_rules_and_lines
    engine_baseline = AuditEngine(rules)
    res_baseline = engine_baseline.audit(lines)

    assert len(res_baseline.discrepancies) == 3
    base_disc = {d.rule_id: d for d in res_baseline.discrepancies}
    assert base_disc["R-LIFT-02"].overcharge_amount == Decimal("15.00")  # 55 - 40

    # Mutate ONLY liftgate cap from $40.00 to $45.00
    mutated_rules = [
        RuleDefinition(
            id=r.id,
            type=r.type,
            description=r.description,
            parameters={"fee_type": "liftgate", "cap": Decimal("45.00")} if r.id == "R-LIFT-02" else r.parameters,
            source_page=r.source_page,
            source_quote=r.source_quote,
            status=r.status,
        )
        for r in rules
    ]

    engine_mutated = AuditEngine(mutated_rules)
    res_mutated = engine_mutated.audit(lines)

    mut_disc = {d.rule_id: d for d in res_mutated.discrepancies}

    # 1. Non-mutated rules must be 100% identical in overcharge, math, and findings
    assert mut_disc["R-DISC-01"].overcharge_amount == base_disc["R-DISC-01"].overcharge_amount
    assert mut_disc["R-FUEL-03"].overcharge_amount == base_disc["R-FUEL-03"].overcharge_amount

    # 2. Mutated rule must change by exactly $5.00 (from $15.00 to $10.00)
    assert mut_disc["R-LIFT-02"].overcharge_amount == Decimal("10.00")  # 55 - 45
    assert res_mutated.total_overcharge == res_baseline.total_overcharge - Decimal("5.00")


def test_mutation_base_discount_percentage(sample_rules_and_lines):
    rules, lines = sample_rules_and_lines
    engine_baseline = AuditEngine(rules)
    res_baseline = engine_baseline.audit(lines)

    base_disc = {d.rule_id: d for d in res_baseline.discrepancies}
    assert base_disc["R-DISC-01"].overcharge_amount == Decimal("10.00")  # expected 55, billed 65

    # Mutate ONLY base discount from 45% (0.45) to 50% (0.50)
    mutated_rules = [
        RuleDefinition(
            id=r.id,
            type=r.type,
            description=r.description,
            parameters={"percentage": Decimal("0.50")} if r.id == "R-DISC-01" else r.parameters,
            source_page=r.source_page,
            source_quote=r.source_quote,
            status=r.status,
        )
        for r in rules
    ]

    engine_mutated = AuditEngine(mutated_rules)
    res_mutated = engine_mutated.audit(lines)

    mut_disc = {d.rule_id: d for d in res_mutated.discrepancies}

    # 1. Non-mutated rules are completely unaffected
    assert mut_disc["R-LIFT-02"].overcharge_amount == base_disc["R-LIFT-02"].overcharge_amount
    assert mut_disc["R-FUEL-03"].overcharge_amount == base_disc["R-FUEL-03"].overcharge_amount

    # 2. Expected is now $100 * (1 - 0.50) = $50.00, so overcharge is $65 - $50 = $15.00 (+ $5.00)
    assert mut_disc["R-DISC-01"].overcharge_amount == Decimal("15.00")
    assert res_mutated.total_overcharge == res_baseline.total_overcharge + Decimal("5.00")
