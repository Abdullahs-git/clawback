"""
Pure Python domain types for deterministic contract rules engine.
Zero external dependencies, 100% Decimal precision for monetary amounts.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class RuleDefinition:
    id: str
    type: str  # base_discount, accessorial_rule, fuel_surcharge, dim_weight_divisor, minimum_charge, duplicate_charge, claim_window_days
    description: str
    parameters: Dict[str, Any]
    source_page: int
    source_quote: str
    confidence: float = 1.0
    status: str = "approved"


@dataclass(frozen=True)
class NormalizedInvoiceLine:
    line_id: str
    invoice_number: str
    invoice_date: str  # YYYY-MM-DD
    shipment_id: str
    charge_code: str
    amount_billed: Decimal
    charge_description: Optional[str] = None
    service_level: Optional[str] = None
    origin_zip: Optional[str] = None
    destination_zip: Optional[str] = None
    zone: Optional[str] = None
    weight_actual_lbs: Optional[Decimal] = None
    dim_length_in: Optional[Decimal] = None
    dim_width_in: Optional[Decimal] = None
    dim_height_in: Optional[Decimal] = None
    billed_weight_lbs: Optional[Decimal] = None
    published_rate: Optional[Decimal] = None
    discount_applied_percent: Optional[Decimal] = None
    fuel_surcharge_percent: Optional[Decimal] = None


@dataclass(frozen=True)
class AuditDiscrepancy:
    line_id: str
    shipment_id: str
    invoice_number: str
    invoice_date: str
    charge_code: str
    rule_id: str
    rule_type: str
    rule_description: str
    contract_page: int
    contract_clause_quote: str
    expected_amount: Decimal
    billed_amount: Decimal
    overcharge_amount: Decimal
    calculation_math: str
    claim_deadline_date: Optional[str] = None
    days_remaining_to_claim: Optional[int] = None
