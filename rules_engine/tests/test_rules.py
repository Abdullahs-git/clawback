"""
Unit tests for Clawback Deterministic Rules Engine.
Targeting 100% line and branch coverage for all money calculations.
"""
from decimal import Decimal
from datetime import date
import pytest

from rules_engine.types import RuleDefinition, NormalizedInvoiceLine, AuditDiscrepancy
from rules_engine.engine import AuditEngine
from rules_engine.rules.base_discount import audit_base_discount
from rules_engine.rules.accessorial import audit_accessorial
from rules_engine.rules.fuel_surcharge import audit_fuel_surcharge
from rules_engine.rules.dim_weight import audit_dim_weight
from rules_engine.rules.minimum_charge import audit_minimum_charge
from rules_engine.rules.duplicate_charge import audit_duplicates
from rules_engine.rules.claim_window import calculate_claim_deadline, audit_claim_window_expiration


def make_line(
    line_id="L-1",
    invoice_number="INV-100",
    invoice_date="2026-09-01",
    shipment_id="TRK-9999",
    charge_code="FRT",
    amount_billed=Decimal("100.00"),
    **kwargs
) -> NormalizedInvoiceLine:
    return NormalizedInvoiceLine(
        line_id=line_id,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        shipment_id=shipment_id,
        charge_code=charge_code,
        amount_billed=amount_billed,
        **kwargs
    )


# ==============================================================================
# Base Discount Tests
# ==============================================================================

def test_base_discount_honored():
    rule = RuleDefinition(
        id="RULE-1",
        type="base_discount",
        description="40% discount on base freight",
        parameters={"percentage": Decimal("0.40")},
        source_page=2,
        source_quote="Shipper receives a 40% discount off standard rates.",
    )
    line = make_line(published_rate=Decimal("100.00"), amount_billed=Decimal("60.00"))
    assert audit_base_discount(line, rule) is None


def test_base_discount_overcharge():
    rule = RuleDefinition(
        id="RULE-1",
        type="base_discount",
        description="40% discount on base freight",
        parameters={"percentage": "40.0"},
        source_page=2,
        source_quote="Shipper receives a 40% discount off standard rates.",
    )
    line = make_line(published_rate=Decimal("100.00"), amount_billed=Decimal("75.00"))
    disc = audit_base_discount(line, rule)
    assert disc is not None
    assert disc.expected_amount == Decimal("60.00")
    assert disc.overcharge_amount == Decimal("15.00")
    assert "Agreed discount 40.0%" in disc.calculation_math


def test_base_discount_service_mismatch():
    rule = RuleDefinition(
        id="RULE-1",
        type="base_discount",
        description="Express only",
        parameters={"percentage": 0.40, "service_level": "EXPRESS"},
        source_page=2,
        source_quote="Express only",
    )
    line = make_line(published_rate=Decimal("100.00"), service_level="GROUND")
    assert audit_base_discount(line, rule) is None


def test_base_discount_non_freight_code():
    rule = RuleDefinition(
        id="RULE-1",
        type="base_discount",
        description="Base discount",
        parameters={"percentage": 0.40},
        source_page=2,
        source_quote="Base discount",
    )
    line = make_line(charge_code="ACC")
    assert audit_base_discount(line, rule) is None


def test_base_discount_missing_percentage():
    rule = RuleDefinition(
        id="RULE-1",
        type="base_discount",
        description="Empty",
        parameters={},
        source_page=1,
        source_quote="quote",
    )
    line = make_line(published_rate=Decimal("100.00"), amount_billed=Decimal("50.00"))
    assert audit_base_discount(line, rule) is None


def test_base_discount_applied_percent_branch():
    rule = RuleDefinition(
        id="RULE-1",
        type="base_discount",
        description="50% base discount",
        parameters={"percentage": 0.50},
        source_page=1,
        source_quote="50% off",
    )
    line = make_line(
        amount_billed=Decimal("75.00"),
        discount_applied_percent=Decimal("25.0")
    )
    disc = audit_base_discount(line, rule)
    assert disc is not None
    assert disc.expected_amount == Decimal("50.00")
    assert disc.overcharge_amount == Decimal("25.00")


def test_base_discount_applied_percent_sufficient():
    rule = RuleDefinition(
        id="RULE-1",
        type="base_discount",
        description="40% base discount",
        parameters={"percentage": 0.40},
        source_page=1,
        source_quote="40% off",
    )
    line = make_line(
        amount_billed=Decimal("50.00"),
        discount_applied_percent=Decimal("50.0")
    )
    assert audit_base_discount(line, rule) is None


def test_base_discount_no_rate_info():
    rule = RuleDefinition(
        id="RULE-1",
        type="base_discount",
        description="40%",
        parameters={"percentage": 0.40},
        source_page=1,
        source_quote="40% off",
    )
    line = make_line(amount_billed=Decimal("50.00"), published_rate=None, discount_applied_percent=None)
    assert audit_base_discount(line, rule) is None


# ==============================================================================
# Accessorial Tests
# ==============================================================================

def test_accessorial_empty_type():
    rule = RuleDefinition(
        id="R", type="accessorial_rule", description="None", parameters={}, source_page=1, source_quote="quote"
    )
    line = make_line(charge_code="RES")
    assert audit_accessorial(line, rule) is None


def test_accessorial_waived():
    rule = RuleDefinition(
        id="RULE-ACC-1",
        type="accessorial_rule",
        description="Residential fee waived",
        parameters={"fee_type": "residential", "allowed": False},
        source_page=3,
        source_quote="Residential delivery fee shall be waived.",
    )
    line = make_line(charge_code="RES", amount_billed=Decimal("15.50"))
    disc = audit_accessorial(line, rule)
    assert disc is not None
    assert disc.expected_amount == Decimal("0.00")
    assert disc.overcharge_amount == Decimal("15.50")
    assert "waived" in disc.calculation_math


def test_accessorial_cap_exceeded():
    rule = RuleDefinition(
        id="RULE-ACC-2",
        type="accessorial_rule",
        description="Liftgate capped at $45.00",
        parameters={"fee_type": "liftgate", "cap": "45.00"},
        source_page=4,
        source_quote="Liftgate charge not to exceed $45.00.",
    )
    line = make_line(charge_code="LFT", amount_billed=Decimal("65.00"))
    disc = audit_accessorial(line, rule)
    assert disc is not None
    assert disc.expected_amount == Decimal("45.00")
    assert disc.overcharge_amount == Decimal("20.00")


def test_accessorial_fixed_rate():
    rule = RuleDefinition(
        id="RULE-ACC-3",
        type="accessorial_rule",
        description="Address correction fixed at $10.00",
        parameters={"fee_type": "address_correction", "rate": "10.00"},
        source_page=4,
        source_quote="Address correction shall be $10.00 per package.",
    )
    line = make_line(charge_code="ADDRC", amount_billed=Decimal("18.00"))
    disc = audit_accessorial(line, rule)
    assert disc is not None
    assert disc.expected_amount == Decimal("10.00")
    assert disc.overcharge_amount == Decimal("8.00")


def test_accessorial_fixed_rate_compliant():
    rule = RuleDefinition(
        id="RULE-ACC-3",
        type="accessorial_rule",
        description="Address correction fixed at $10.00",
        parameters={"fee_type": "address_correction", "rate": "10.00"},
        source_page=4,
        source_quote="Address correction shall be $10.00 per package.",
    )
    line = make_line(charge_code="ADDRC", amount_billed=Decimal("10.00"))
    assert audit_accessorial(line, rule) is None


def test_accessorial_not_exceeded():
    rule = RuleDefinition(
        id="RULE-ACC-4",
        type="accessorial_rule",
        description="Liftgate cap $50",
        parameters={"fee_type": "liftgate", "cap": "50.00"},
        source_page=4,
        source_quote="Cap $50",
    )
    line = make_line(charge_code="LFT", amount_billed=Decimal("40.00"))
    assert audit_accessorial(line, rule) is None


def test_accessorial_no_actionable_params():
    rule = RuleDefinition(
        id="RULE-ACC-5",
        type="accessorial_rule",
        description="Liftgate without cap or rate",
        parameters={"fee_type": "liftgate", "allowed": True},
        source_page=4,
        source_quote="Liftgate allowed",
    )
    line = make_line(charge_code="LFT", amount_billed=Decimal("40.00"))
    assert audit_accessorial(line, rule) is None


# ==============================================================================
# Fuel Surcharge Tests
# ==============================================================================

def test_fuel_surcharge_overcharge():
    rule = RuleDefinition(
        id="RULE-FSC-1",
        type="fuel_surcharge",
        description="Fuel surcharge fixed at 12%",
        parameters={"fixed_percentage": "12.0"},
        source_page=5,
        source_quote="Fuel surcharge shall remain fixed at 12.0% for term.",
    )
    line = make_line(
        charge_code="FSC",
        amount_billed=Decimal("16.00"),
        fuel_surcharge_percent=Decimal("16.0")
    )
    disc = audit_fuel_surcharge(line, rule)
    assert disc is not None
    assert disc.expected_amount == Decimal("12.00")
    assert disc.overcharge_amount == Decimal("4.00")


def test_fuel_surcharge_max_percentage():
    rule = RuleDefinition(
        id="RULE-FSC-1B",
        type="fuel_surcharge",
        description="Fuel surcharge max at 10%",
        parameters={"max_percentage": "0.10"},
        source_page=5,
        source_quote="Fuel surcharge max 10%",
    )
    line = make_line(
        charge_code="FUEL",
        amount_billed=Decimal("15.00"),
        fuel_surcharge_percent=Decimal("0.15")
    )
    disc = audit_fuel_surcharge(line, rule)
    assert disc is not None
    assert disc.expected_amount == Decimal("10.00")


def test_fuel_surcharge_compliant():
    rule = RuleDefinition(
        id="RULE-FSC-2",
        type="fuel_surcharge",
        description="Fuel surcharge 12%",
        parameters={"fixed_percentage": "0.12"},
        source_page=5,
        source_quote="12%",
    )
    line = make_line(
        charge_code="FSC",
        amount_billed=Decimal("12.00"),
        fuel_surcharge_percent=Decimal("0.12")
    )
    assert audit_fuel_surcharge(line, rule) is None


def test_fuel_surcharge_non_fuel_code():
    rule = RuleDefinition(
        id="RULE-FSC-3",
        type="fuel_surcharge",
        description="12%",
        parameters={"fixed_percentage": "0.12"},
        source_page=5,
        source_quote="12%",
    )
    line = make_line(charge_code="FRT", amount_billed=Decimal("12.00"))
    assert audit_fuel_surcharge(line, rule) is None


# ==============================================================================
# DIM Weight Tests
# ==============================================================================

def test_dim_weight_divisor_overcharge():
    rule = RuleDefinition(
        id="RULE-DIM-1",
        type="dim_weight_divisor",
        description="DIM divisor 166",
        parameters={"divisor": 166},
        source_page=6,
        source_quote="Dimensional weight divisor shall be 166.",
    )
    line = make_line(
        charge_code="FRT",
        amount_billed=Decimal("116.00"),
        weight_actual_lbs=Decimal("15.0"),
        dim_length_in=Decimal("20.0"),
        dim_width_in=Decimal("20.0"),
        dim_height_in=Decimal("20.0"),
        billed_weight_lbs=Decimal("58.0"),
    )
    disc = audit_dim_weight(line, rule)
    assert disc is not None
    assert disc.expected_amount == Decimal("98.00")
    assert disc.overcharge_amount == Decimal("18.00")


def test_dim_weight_non_freight():
    rule = RuleDefinition(
        id="RULE-DIM-1", type="dim_weight_divisor", description="166", parameters={"divisor": 166}, source_page=1, source_quote="quote"
    )
    line = make_line(charge_code="ACC")
    assert audit_dim_weight(line, rule) is None


def test_dim_weight_missing_divisor_or_dims():
    rule_no_div = RuleDefinition(
        id="RULE-DIM-1", type="dim_weight_divisor", description="166", parameters={}, source_page=1, source_quote="quote"
    )
    line = make_line(charge_code="FRT", dim_length_in=Decimal("10.0"))
    assert audit_dim_weight(line, rule_no_div) is None

    rule_with_div = RuleDefinition(
        id="RULE-DIM-1", type="dim_weight_divisor", description="166", parameters={"divisor": 166}, source_page=1, source_quote="quote"
    )
    line_no_dims = make_line(charge_code="FRT")
    assert audit_dim_weight(line_no_dims, rule_with_div) is None


def test_dim_weight_compliant():
    rule = RuleDefinition(
        id="RULE-DIM-1", type="dim_weight_divisor", description="166", parameters={"divisor": 166}, source_page=1, source_quote="quote"
    )
    line = make_line(
        charge_code="FRT",
        amount_billed=Decimal("98.00"),
        weight_actual_lbs=Decimal("15.0"),
        dim_length_in=Decimal("20.0"),
        dim_width_in=Decimal("20.0"),
        dim_height_in=Decimal("20.0"),
        billed_weight_lbs=Decimal("49.0"),
    )
    assert audit_dim_weight(line, rule) is None


# ==============================================================================
# Minimum Charge Tests
# ==============================================================================

def test_minimum_charge_overcharge():
    rule = RuleDefinition(
        id="RULE-MIN-1",
        type="minimum_charge",
        description="Minimum charge floor $45.00",
        parameters={"amount": "45.00"},
        source_page=7,
        source_quote="Absolute minimum charge per shipment is $45.00.",
    )
    line = make_line(charge_code="MIN", amount_billed=Decimal("65.00"))
    disc = audit_minimum_charge(line, rule)
    assert disc is not None
    assert disc.expected_amount == Decimal("45.00")
    assert disc.overcharge_amount == Decimal("20.00")


def test_minimum_charge_service_mismatch_and_compliant():
    rule = RuleDefinition(
        id="RULE-MIN-1",
        type="minimum_charge",
        description="Ground min",
        parameters={"amount": "45.00", "service_level": "GROUND"},
        source_page=1,
        source_quote="quote",
    )
    line_diff_srv = make_line(charge_code="MIN", service_level="AIR", amount_billed=Decimal("60.00"))
    assert audit_minimum_charge(line_diff_srv, rule) is None

    line_compliant = make_line(charge_code="MIN", service_level="GROUND", amount_billed=Decimal("40.00"))
    assert audit_minimum_charge(line_compliant, rule) is None

    line_non_min = make_line(charge_code="FRT", amount_billed=Decimal("60.00"))
    assert audit_minimum_charge(line_non_min, rule) is None


# ==============================================================================
# Duplicate Charge Tests
# ==============================================================================

def test_duplicate_charges():
    rule = RuleDefinition(
        id="RULE-DUP-1",
        type="duplicate_charge",
        description="Duplicate billing audit",
        parameters={"enabled": True},
        source_page=8,
        source_quote="No shipment shall be billed more than once.",
    )
    lines = [
        make_line(line_id="L-1", shipment_id="SHP-101", charge_code="FRT", amount_billed=Decimal("50.00")),
        make_line(line_id="L-2", shipment_id="SHP-101", charge_code="FRT", amount_billed=Decimal("50.00")),
        make_line(line_id="L-3", shipment_id="SHP-102", charge_code="FRT", amount_billed=Decimal("70.00")),
    ]
    discs = audit_duplicates(lines, rule)
    assert len(discs) == 1
    assert discs[0].line_id == "L-2"
    assert discs[0].overcharge_amount == Decimal("50.00")
    assert discs[0].expected_amount == Decimal("0.00")


# ==============================================================================
# Claim Window & Engine Integration Tests
# ==============================================================================

def test_claim_window_calculation():
    rule = RuleDefinition(
        id="RULE-CLM-1",
        type="claim_window_days",
        description="180 day dispute window",
        parameters={"days": 180},
        source_page=9,
        source_quote="Overcharge claims must be submitted within 180 days of invoice date.",
    )
    deadline_str, days_rem = calculate_claim_deadline(
        "2026-01-01", rule, reference_date=date(2026, 3, 1)
    )
    assert deadline_str == "2026-06-30"
    assert days_rem == 121

    # Invalid date string test
    assert calculate_claim_deadline("invalid-date", rule)[0] is None
    # Missing days parameter test
    rule_empty = RuleDefinition(id="R", type="claim_window_days", description="", parameters={}, source_page=1, source_quote="")
    assert calculate_claim_deadline("2026-01-01", rule_empty)[0] is None


def test_claim_window_expiration_audit():
    rule = RuleDefinition(
        id="RULE-CLM-1",
        type="claim_window_days",
        description="90 day dispute window",
        parameters={"days": 90},
        source_page=9,
        source_quote="90 days",
    )
    # Invoice from 2026-01-01, audited on 2026-08-01 -> Expired!
    line = make_line(invoice_date="2026-01-01", amount_billed=Decimal("50.00"))
    disc = audit_claim_window_expiration(line, rule, reference_date=date(2026, 8, 1))
    assert disc is not None
    assert disc.days_remaining_to_claim < 0
    assert "time-barred" in disc.calculation_math

    # Unexpired line
    line_recent = make_line(invoice_date="2026-07-01", amount_billed=Decimal("50.00"))
    assert audit_claim_window_expiration(line_recent, rule, reference_date=date(2026, 8, 1)) is None


def test_audit_engine_end_to_end_all_rules():
    rules = [
        RuleDefinition(
            id="R-1", type="base_discount", description="50% base discount",
            parameters={"percentage": "0.50"}, source_page=2, source_quote="50% discount", status="approved"
        ),
        RuleDefinition(
            id="R-2", type="accessorial_rule", description="Residential waived",
            parameters={"fee_type": "residential", "allowed": False}, source_page=3, source_quote="Residential waived", status="approved"
        ),
        RuleDefinition(
            id="R-3", type="fuel_surcharge", description="Fuel max 10%",
            parameters={"fixed_percentage": "0.10"}, source_page=4, source_quote="Fuel 10%", status="approved"
        ),
        RuleDefinition(
            id="R-4", type="dim_weight_divisor", description="DIM 166",
            parameters={"divisor": 166}, source_page=5, source_quote="DIM 166", status="approved"
        ),
        RuleDefinition(
            id="R-5", type="minimum_charge", description="Min $40",
            parameters={"amount": "40.00"}, source_page=6, source_quote="Min $40", status="approved"
        ),
        RuleDefinition(
            id="R-6", type="duplicate_charge", description="No dups",
            parameters={"enabled": True}, source_page=7, source_quote="No dups", status="approved"
        ),
        RuleDefinition(
            id="R-7", type="claim_window_days", description="180 days dispute window",
            parameters={"days": 180}, source_page=9, source_quote="180 days", status="approved"
        ),
    ]

    engine = AuditEngine(rules, reference_date=date(2026, 9, 1))

    lines = [
        # Line 1: Base discount overcharge -> $20
        make_line(line_id="L-1", published_rate=Decimal("100.00"), amount_billed=Decimal("70.00")),
        # Line 2: Disallowed residential surcharge -> $15
        make_line(line_id="L-2", charge_code="RES", amount_billed=Decimal("15.00")),
        # Line 3: Fuel overcharge -> Billed 15% ($15), expected 10% ($10) -> $5
        make_line(line_id="L-3", charge_code="FSC", amount_billed=Decimal("15.00"), fuel_surcharge_percent=Decimal("0.15")),
        # Line 4: Minimum charge overcharge -> Billed $55 vs agreed $40 -> $15
        make_line(line_id="L-4", charge_code="MIN", amount_billed=Decimal("55.00")),
        # Line 5 & 6: Duplicate line -> $50
        make_line(line_id="L-5", shipment_id="SHP-DUP", charge_code="FRT", amount_billed=Decimal("50.00")),
        make_line(line_id="L-6", shipment_id="SHP-DUP", charge_code="FRT", amount_billed=Decimal("50.00")),
    ]

    result = engine.audit(lines)
    assert result.lines_audited == 6
    assert len(result.discrepancies) == 5
    # Total overcharge = 20 + 15 + 5 + 15 + 50 = $105.00
    assert result.total_overcharge == Decimal("105.00")
    assert result.by_category["base_discount"] == Decimal("20.00")
    assert result.by_category["accessorial_rule"] == Decimal("15.00")
    assert result.by_category["fuel_surcharge"] == Decimal("5.00")
    assert result.by_category["minimum_charge"] == Decimal("15.00")
    assert result.by_category["duplicate_charge"] == Decimal("50.00")

    for d in result.discrepancies:
        assert d.claim_deadline_date is not None
        assert d.days_remaining_to_claim is not None

def test_coverage_edge_cases():
    # 1. accessorial overcharge <= 0 (e.g. rate == amount_billed handled, test direct cap == amount_billed, and 0 billed waived)
    rule_cap = RuleDefinition(id="R", type="accessorial_rule", description="", parameters={"fee_type": "liftgate", "cap": "50.00"}, source_page=1, source_quote="")
    line_cap = make_line(charge_code="LFT", amount_billed=Decimal("50.00"))
    assert audit_accessorial(line_cap, rule_cap) is None

    rule_waived = RuleDefinition(id="R", type="accessorial_rule", description="", parameters={"fee_type": "residential", "allowed": False}, source_page=1, source_quote="")
    line_zero = make_line(charge_code="RES", amount_billed=Decimal("0.00"))
    assert audit_accessorial(line_zero, rule_waived) is None

    # 2. base_discount with applied_percent >= 1.0 (invalid percentage > 100% after division)
    rule_base = RuleDefinition(id="R", type="base_discount", description="", parameters={"percentage": "0.40"}, source_page=1, source_quote="")
    line_huge_applied = make_line(amount_billed=Decimal("50.00"), discount_applied_percent=Decimal("0.20"))
    # test applied < 1.0 vs else
    line_100_applied = make_line(amount_billed=Decimal("50.00"), discount_applied_percent=Decimal("1.0"))
    assert audit_base_discount(line_100_applied, rule_base) is None

    # 3. claim_window expiration with invalid date
    rule_clm = RuleDefinition(id="R", type="claim_window_days", description="", parameters={"days": 90}, source_page=1, source_quote="")
    line_bad_date = make_line(invoice_date="bad-date", amount_billed=Decimal("50.00"))
    assert audit_claim_window_expiration(line_bad_date, rule_clm) is None

    # 4. minimum_charge with missing amount parameter
    rule_min_no_amount = RuleDefinition(id="R", type="minimum_charge", description="", parameters={}, source_page=1, source_quote="")
    line_min = make_line(charge_code="MIN", amount_billed=Decimal("50.00"))
    assert audit_minimum_charge(line_min, rule_min_no_amount) is None
