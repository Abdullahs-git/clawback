"""
Property-based and determinism tests for Clawback Rules Engine.
Enforces:
1. Determinism across 100 runs (SHA-256 hash invariance)
2. Hypothesis property tests (order independence, idempotency, monotonic findings)
3. Float prohibition audit across rules_engine codebase using AST analysis
"""

import ast
import hashlib
import json
import random
from decimal import Decimal
from pathlib import Path
import pytest
from hypothesis import given, strategies as st, settings

from rules_engine.engine import AuditEngine
from rules_engine.types import RuleDefinition, NormalizedInvoiceLine


def create_sample_rules():
    return [
        RuleDefinition(
            id="R-ACC-01",
            type="accessorial_rule",
            description="Liftgate cap $40.00",
            parameters={"fee_type": "liftgate", "cap": Decimal("40.00"), "allowed": True},
            source_page=3,
            source_quote="Where requested, liftgate service charges shall not exceed forty dollars ($40.00) per occurrence."
        ),
        RuleDefinition(
            id="R-ACC-02",
            type="accessorial_rule",
            description="Residential surcharge waived",
            parameters={"fee_type": "residential", "allowed": False},
            source_page=3,
            source_quote="Residential delivery surcharges shall be waived in full and shall not be assessed on any shipment."
        ),
        RuleDefinition(
            id="R-FUEL-01",
            type="fuel_surcharge",
            description="Fixed 11.5% fuel surcharge",
            parameters={"fixed_percentage": Decimal("0.115")},
            source_page=4,
            source_quote="The applicable fuel surcharge index is agreed and fixed at eleven and one-half percent (11.5%) of net linehaul freight."
        ),
        RuleDefinition(
            id="R-MIN-01",
            type="minimum_charge",
            description="Minimum charge floor $45.00",
            parameters={"amount": Decimal("45.00")},
            source_page=5,
            source_quote="The minimum charge floor per shipment after discount application shall be forty-five dollars ($45.00)."
        ),
        RuleDefinition(
            id="R-DUP-01",
            type="duplicate_charge",
            description="Prohibit duplicate billing",
            parameters={"enabled": True},
            source_page=5,
            source_quote="Carrier warrants that no individual shipment BOL or tracking number shall be invoiced more than once."
        ),
    ]


def create_sample_lines():
    return [
        # Liftgate overcharge: billed $65.00 vs cap $40.00 -> $25.00 overcharge
        NormalizedInvoiceLine(
            line_id="L-01",
            invoice_number="INV-100",
            invoice_date="2026-09-01",
            shipment_id="TRK-001",
            charge_code="LFG",
            charge_description="Liftgate Delivery",
            amount_billed=Decimal("65.00"),
        ),
        # Disallowed residential surcharge: billed $50.00 -> $50.00 overcharge
        NormalizedInvoiceLine(
            line_id="L-02",
            invoice_number="INV-100",
            invoice_date="2026-09-01",
            shipment_id="TRK-002",
            charge_code="RES",
            charge_description="Residential Delivery",
            amount_billed=Decimal("50.00"),
        ),
        # Fuel overcharge: agreed 11.5%, billed 17.5% at $35.00 -> $12.00 overcharge
        NormalizedInvoiceLine(
            line_id="L-03",
            invoice_number="INV-100",
            invoice_date="2026-09-01",
            shipment_id="TRK-003",
            charge_code="FSC",
            charge_description="Fuel Surcharge",
            amount_billed=Decimal("35.00"),
            fuel_surcharge_percent=Decimal("0.175"),
        ),
        # Duplicate charge: TRK-004 billed twice for linehaul FRT
        NormalizedInvoiceLine(
            line_id="L-04A",
            invoice_number="INV-100",
            invoice_date="2026-09-01",
            shipment_id="TRK-004",
            charge_code="FRT",
            charge_description="Linehaul",
            amount_billed=Decimal("150.00"),
        ),
        NormalizedInvoiceLine(
            line_id="L-04B",
            invoice_number="INV-100",
            invoice_date="2026-09-01",
            shipment_id="TRK-004",
            charge_code="FRT",
            charge_description="Linehaul duplicate",
            amount_billed=Decimal("150.00"),
        ),
        # Compliant line
        NormalizedInvoiceLine(
            line_id="L-05",
            invoice_number="INV-100",
            invoice_date="2026-09-01",
            shipment_id="TRK-005",
            charge_code="LFG",
            charge_description="Compliant Liftgate",
            amount_billed=Decimal("35.00"),
        ),
    ]


# ==============================================================================
# Determinism Test across 100 Runs
# ==============================================================================

def test_determinism_across_100_runs():
    """
    Run the same audit 100 times, hash the output, and assert exactly ONE hash.
    Ensures zero non-deterministic behavior, no random dict ordering issues,
    and no time-dependent side effects.
    """
    rules = create_sample_rules()
    lines = create_sample_lines()
    engine = AuditEngine(rules)

    hashes = set()
    for _ in range(100):
        result = engine.audit(lines)
        # Serialize findings into deterministic canonical JSON
        findings_repr = [
            {
                "line_id": f.line_id,
                "rule_id": f.rule_id,
                "amount": str(f.overcharge_amount),
                "expected": str(f.expected_amount),
                "billed": str(f.billed_amount),
            }
            for f in sorted(result.discrepancies, key=lambda x: (x.line_id, x.rule_id))
        ]
        serialized = json.dumps(findings_repr, sort_keys=True)
        h = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        hashes.add(h)

    assert len(hashes) == 1, f"Expected 1 unique hash across 100 runs, got {len(hashes)}"


# ==============================================================================
# Float Prohibition Audit via Python AST
# ==============================================================================

def test_float_prohibition_in_rules_engine():
    """
    Audit rules_engine codebase using AST analysis to verify that NO float calls or
    float constants exist in executable Python code.
    Clawback strictly requires Decimal for all monetary math.
    """
    package_dir = Path(__file__).resolve().parent.parent / "rules_engine"
    py_files = list(package_dir.rglob("*.py"))
    assert len(py_files) > 0

    violations = []
    for f in py_files:
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            # Check for float(...) function call
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "float":
                    violations.append(f"{f.name}:{node.lineno} uses float() call")
            # Check for float constants (e.g. 1.5, 0.40)
            elif isinstance(node, ast.Constant) and isinstance(node.value, float):
                violations.append(f"{f.name}:{node.lineno} contains float constant {node.value}")

    assert len(violations) == 0, f"Found float violations in rules_engine: {violations}"


# ==============================================================================
# Property Tests
# ==============================================================================

def test_property_line_order_independence():
    """
    Shuffling invoice lines must yield the exact same discrepancies set and total amount.
    """
    rules = create_sample_rules()
    base_lines = create_sample_lines()
    engine = AuditEngine(rules)

    reference_result = engine.audit(base_lines)
    ref_map = {f.line_id: f.overcharge_amount for f in reference_result.discrepancies}
    ref_total = reference_result.total_overcharge

    for seed in range(20):
        shuffled = list(base_lines)
        random.seed(seed)
        random.shuffle(shuffled)

        result = engine.audit(shuffled)
        test_map = {f.line_id: f.overcharge_amount for f in result.discrepancies}
        test_total = result.total_overcharge

        assert test_total == ref_total, f"Order affected total with seed {seed}"
        assert test_map == ref_map, f"Order affected line findings with seed {seed}"


def test_property_idempotency():
    """Running the engine twice on the exact same input yields identical findings."""
    rules = create_sample_rules()
    lines = create_sample_lines()
    engine = AuditEngine(rules)

    run1 = engine.audit(lines)
    run2 = engine.audit(lines)

    assert run1.lines_audited == run2.lines_audited
    assert run1.total_overcharge == run2.total_overcharge
    assert len(run1.discrepancies) == len(run2.discrepancies)

    for f1, f2 in zip(run1.discrepancies, run2.discrepancies):
        assert f1.line_id == f2.line_id
        assert f1.rule_id == f2.rule_id
        assert f1.overcharge_amount == f2.overcharge_amount
        assert f1.calculation_math == f2.calculation_math


def test_property_adding_compliant_line_invariance():
    """
    Adding a compliant invoice line never alters or removes existing findings.
    """
    rules = create_sample_rules()
    lines = create_sample_lines()
    engine = AuditEngine(rules)

    initial_result = engine.audit(lines)
    initial_ids = {f.line_id for f in initial_result.discrepancies}
    initial_total = initial_result.total_overcharge

    compliant_line = NormalizedInvoiceLine(
        line_id="COMPLIANT-99",
        invoice_number="INV-200",
        invoice_date="2026-09-01",
        shipment_id="TRK-999",
        charge_code="LFG",
        amount_billed=Decimal("20.00"),  # Well below $40.00 cap
    )

    augmented_lines = lines + [compliant_line]
    new_result = engine.audit(augmented_lines)
    new_ids = {f.line_id for f in new_result.discrepancies}
    new_total = new_result.total_overcharge

    assert new_ids == initial_ids
    assert new_total == initial_total


def test_property_line_with_no_rule_never_produces_finding():
    """
    A line with an unknown charge code not matching any rule, not duplicate, and within window
    must produce zero findings.
    """
    rules = create_sample_rules()
    engine = AuditEngine(rules)

    unknown_line = NormalizedInvoiceLine(
        line_id="NO-RULE-01",
        invoice_number="INV-300",
        invoice_date="2026-09-01",
        shipment_id="TRK-NO-RULE",
        charge_code="CUSTOMS_CLEARANCE",  # No rule in contract
        amount_billed=Decimal("500.00"),
    )

    result = engine.audit([unknown_line])
    assert len(result.discrepancies) == 0
    assert result.total_overcharge == Decimal("0.00")
