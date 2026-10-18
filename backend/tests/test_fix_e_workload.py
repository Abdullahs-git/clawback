"""
Tests for Fix E: Meaningful Workload for AMD
1. Charge-description normalization & whitelist validation
2. Self-consistency extraction k=3 consensus
3. Plain-language finding explanations & amount validation safeguard
"""
import pytest
from backend.app.services.charge_normalization import (
    validate_normalization_output,
    normalize_charge_descriptions,
    CANONICAL_CHARGE_CODES
)
from backend.app.services.extraction import (
    normalize_rule_parameters_key,
    evaluate_self_consistency_consensus
)
from backend.app.services.dispute import (
    validate_text_amounts_against_data,
    generate_finding_plain_explanation,
    extract_numeric_tokens
)


def test_charge_normalization_whitelist_validation():
    # Valid canonical mappings with high confidence
    raw_output = {
        "mappings": [
            {"raw_description": "RESI DLVRY", "canonical_code": "RES", "confidence": 0.98},
            {"raw_description": "LIFT GATE SVC", "canonical_code": "LFG", "confidence": 0.92},
            {"raw_description": "UNKNOWN BIZARRE FEE", "canonical_code": "UNKNOWN", "confidence": 0.20},
            {"raw_description": "NON_EXISTENT_CODE", "canonical_code": "INVALID_XYZ", "confidence": 0.99},
            {"raw_description": "LOW_CONF_RES", "canonical_code": "RES", "confidence": 0.50},
        ]
    }
    validated = validate_normalization_output(raw_output)

    assert validated["RESI DLVRY"]["status"] == "normalized"
    assert validated["RESI DLVRY"]["canonical_code"] == "RES"
    assert not validated["RESI DLVRY"]["needs_review"]

    assert validated["LIFT GATE SVC"]["status"] == "normalized"
    assert validated["LIFT GATE SVC"]["canonical_code"] == "LFG"
    assert not validated["LIFT GATE SVC"]["needs_review"]

    # Unknown or low confidence must flag needs_review
    assert validated["UNKNOWN BIZARRE FEE"]["needs_review"] is True
    assert validated["UNKNOWN BIZARRE FEE"]["status"] == "needs_review"

    # Invalid code not in whitelist must flag needs_review and set UNKNOWN
    assert validated["NON_EXISTENT_CODE"]["needs_review"] is True
    assert validated["NON_EXISTENT_CODE"]["canonical_code"] == "UNKNOWN"

    # Valid code with confidence < 0.85 must flag needs_review
    assert validated["LOW_CONF_RES"]["needs_review"] is True


import anyio

def test_charge_normalization_service_known_abbreviations():
    descs = ["RESI DLVRY", "LIFT GATE SVC", "FUEL SURCHARGE", "INSIDE PICKUP"]
    results = anyio.run(normalize_charge_descriptions, descs)

    assert results["RESI DLVRY"]["canonical_code"] == "RES"
    assert results["LIFT GATE SVC"]["canonical_code"] == "LFG"
    assert results["FUEL SURCHARGE"]["canonical_code"] == "FUEL"
    assert results["INSIDE PICKUP"]["canonical_code"] == "INSIDE"
    for d in descs:
        assert results[d]["needs_review"] is False


def test_self_consistency_consensus_high_confidence():
    # 3 runs where 2 or 3 runs agree on type and parameters
    run1 = {
        "rules": [
            {
                "id": "R1",
                "type": "base_discount",
                "parameters": {"percentage": 0.40, "service_level": "Ground"},
                "source_page": 2,
                "source_quote": "40% discount off standard rates.",
                "confidence": 0.95
            }
        ]
    }
    run2 = {
        "rules": [
            {
                "id": "R1",
                "type": "base_discount",
                "parameters": {"percentage": 0.40, "service_level": "Ground"},
                "source_page": 2,
                "source_quote": "40% discount off standard rates.",
                "confidence": 0.95
            }
        ]
    }
    run3 = {
        "rules": [
            {
                "id": "R1",
                "type": "base_discount",
                "parameters": {"percentage": 0.40, "service_level": "Ground"},
                "source_page": 2,
                "source_quote": "40% discount off standard rates.",
                "confidence": 0.95
            }
        ]
    }

    consensus = evaluate_self_consistency_consensus([run1, run2, run3], k=3)
    assert len(consensus) == 1
    assert consensus[0]["consensus_status"] == "high_confidence"
    assert consensus[0]["consensus_agreement_count"] == 3


def test_self_consistency_consensus_disagreement_needs_review():
    # Run 1 extracted 40%, Run 2 extracted 45%, Run 3 extracted 50%
    run1 = {
        "rules": [
            {"id": "R1", "type": "base_discount", "parameters": {"percentage": 0.40}, "status": "approved"}
        ]
    }
    run2 = {
        "rules": [
            {"id": "R1", "type": "base_discount", "parameters": {"percentage": 0.45}, "status": "approved"}
        ]
    }
    run3 = {
        "rules": [
            {"id": "R1", "type": "base_discount", "parameters": {"percentage": 0.50}, "status": "approved"}
        ]
    }

    consensus = evaluate_self_consistency_consensus([run1, run2, run3], k=3)
    # None reached >= 2 votes
    for r in consensus:
        assert r["consensus_status"] == "needs_review"
        assert r["consensus_agreement_count"] == 1
        assert "agreed on parameters" in r["review_reason"]


def test_amount_validation_safeguard():
    allowed_amounts = {"9130.51", "65.00", "45.00", "0.00"}

    # Text containing only valid amounts and innocuous small numbers (like 1, 30 days)
    valid_text = (
        "Total overcharge is $9130.51. Discrepancy on line 1 was $65.00. "
        "Allowed floor was $45.00. Please respond within 30 days."
    )
    assert validate_text_amounts_against_data(valid_text, allowed_amounts) is True

    # Text containing a hallucinated or altered number like $500 or $9159.31
    invalid_text = "Total overcharge is $9159.31 with an unauthorized fee of $500."
    assert validate_text_amounts_against_data(invalid_text, allowed_amounts) is False


def test_plain_explanation_generation_and_validation():
    explanation = generate_finding_plain_explanation(
        shipment_id="TRK-9876",
        invoice_number="INV-1001",
        charge_code="RES",
        rule_type="accessorial_rule",
        billed_amount="65.00",
        expected_amount="0.00",
        overcharge_amount="65.00",
        contract_page=2,
        contract_quote="Residential delivery charges are fully waived."
    )

    assert "$65.00" in explanation
    assert "$0.00" in explanation
    assert "TRK-9876" in explanation
    assert "Page 2" in explanation
    # Must pass validation
    assert validate_text_amounts_against_data(explanation, {"65.00", "0.00"}) is True
