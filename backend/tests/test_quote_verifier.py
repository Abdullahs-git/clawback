"""
Unit tests for Quote Verifier Safeguard & Parameter-vs-Quote Grounding (Fix D).
Targeting 100% test coverage of quote verification and parameter grounding.
"""

from decimal import Decimal
import pytest
from backend.app.services.quote_verifier import (
    normalize_text_for_comparison,
    verify_source_quote,
    check_value_in_quote,
    validate_parameters_against_quote,
    apply_quote_verification_safeguard,
)


def test_normalize_text():
    assert normalize_text_for_comparison('“Hello—World”') == '"hello-world"'
    assert normalize_text_for_comparison("   multiple   \n lines  ") == "multiple lines"
    assert normalize_text_for_comparison("") == ""


def test_verify_source_quote_verbatim():
    doc_text = "Page 1: Rates. Section 3: Liftgate fee not to exceed $40.00 per occurrence."
    # Direct match
    ok, msg = verify_source_quote("Liftgate fee not to exceed $40.00", doc_text, doc_text)
    assert ok is True

    # Empty or too short
    ok, msg = verify_source_quote("too", doc_text, doc_text)
    assert ok is False
    assert "too short" in msg

    # Non-existent quote
    ok, msg = verify_source_quote("Shipper shall receive 90% discount on all air freight", doc_text, doc_text)
    assert ok is False
    assert "not found" in msg


def test_parameter_matching_numbers_and_currency():
    # Digits with dollar signs
    assert check_value_in_quote("40.00", "Where requested, liftgate charge shall not exceed $40.00.")
    assert check_value_in_quote(40, "Liftgate charge shall not exceed $40.")
    assert check_value_in_quote("45.00", "Minimum charge floor is $45.00 per shipment.")


def test_parameter_matching_percentages():
    # 0.115 matches 11.5%
    assert check_value_in_quote(0.115, "Fuel surcharge index is agreed and fixed at 11.5% of net linehaul.")
    assert check_value_in_quote("0.45", "Shipper shall receive an agreed base discount of 45.0% off published rates.")
    assert check_value_in_quote(Decimal("0.40"), "Discount shall be forty percent (40%) off tariff.")


def test_parameter_matching_spelled_out_numbers():
    assert check_value_in_quote(40, "Charges shall not exceed forty dollars per occurrence.")
    assert check_value_in_quote(166, "Cubic dimensional weight calculations shall strictly utilize a divisor of one hundred sixty-six.")
    assert check_value_in_quote(180, "Claims must be submitted within one hundred eighty days.")
    assert check_value_in_quote(0.115, "Fuel index fixed at eleven and one-half percent.")


def test_parameter_mismatch_rejection():
    # Quote says $40, but extracted parameter is 14 (hallucinated number)
    rule = {
        "type": "accessorial_rule",
        "source_page": 1,
        "source_quote": "Liftgate charge shall not exceed forty dollars ($40.00).",
        "parameters": {"cap": "14.00", "fee_type": "liftgate"}
    }
    ok, reason = validate_parameters_against_quote(rule)
    assert ok is False
    assert "cap=14.00" in reason
    assert "not supported by quote" in reason


def test_waiver_boolean_validation():
    # Allowed=False with waiver keyword present
    rule_waived = {
        "type": "accessorial_rule",
        "source_quote": "Residential delivery surcharges shall be waived in full.",
        "parameters": {"allowed": False, "fee_type": "residential"}
    }
    ok, _ = validate_parameters_against_quote(rule_waived)
    assert ok is True

    # Allowed=False WITHOUT waiver keyword (e.g. quote simply mentions the fee)
    rule_not_waived = {
        "type": "accessorial_rule",
        "source_quote": "Residential delivery surcharges are assessed per package.",
        "parameters": {"allowed": False, "fee_type": "residential"}
    }
    ok, reason = validate_parameters_against_quote(rule_not_waived)
    assert ok is False
    assert "missing waiver keyword" in reason


def test_apply_safeguard_two_stage_rejection():
    pages_map = {1: "Section 4: Liftgate charge capped at $40.00."}
    full_text = pages_map[1]

    # 1. Unverifiable quote -> rejected at Stage 1
    rule_fake_quote = {
        "source_page": 1,
        "source_quote": "Completely invented contract text.",
        "parameters": {"cap": "40.00"}
    }
    res1 = apply_quote_verification_safeguard(rule_fake_quote, pages_map, full_text)
    assert res1["status"] == "rejected"
    assert "verbatim text not found" in res1["rejection_reason"]

    # 2. Verifiable quote, but mismatched parameter -> rejected at Stage 2
    rule_mismatched_param = {
        "source_page": 1,
        "source_quote": "Liftgate charge capped at $40.00.",
        "parameters": {"cap": "15.00"}
    }
    res2 = apply_quote_verification_safeguard(rule_mismatched_param, pages_map, full_text)
    assert res2["status"] == "rejected"
    assert "Parameter 'cap=15.00' not supported by quote" in res2["rejection_reason"]

    # 3. Valid quote and valid parameter -> proposed
    rule_valid = {
        "source_page": 1,
        "source_quote": "Liftgate charge capped at $40.00.",
        "parameters": {"cap": "40.00"}
    }
    res3 = apply_quote_verification_safeguard(rule_valid, pages_map, full_text)
    assert res3["status"] == "proposed"
    assert res3["rejection_reason"] is None
