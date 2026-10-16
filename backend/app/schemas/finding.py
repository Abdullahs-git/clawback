"""
Pydantic v2 schemas for deterministic audit findings.
"""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class AuditRunRequest(BaseModel):
    batch_id: str = Field(..., description="Target invoice batch ID")
    contract_id: str = Field(..., description="Contract whose approved rules will be audited against")


class AuditRunResult(BaseModel):
    batch_id: str
    contract_id: str
    lines_audited: int
    discrepancies_count: int
    total_overcharge_amount: str
    completed_at: datetime


class AuditFindingDetail(BaseModel):
    finding_id: str
    batch_id: str
    contract_id: str
    carrier_name: str
    invoice_number: str
    invoice_date: str
    line_id: str
    shipment_id: str
    charge_code: str
    rule_id: str
    rule_type: str
    rule_description: str
    contract_page: int
    contract_clause_quote: str
    expected_amount: str
    billed_amount: str
    overcharge_amount: str
    calculation_math: str
    claim_deadline_date: Optional[str] = None
    days_remaining_to_claim: Optional[int] = None
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AuditFindingsOverview(BaseModel):
    total_overcharge: str
    total_findings_count: int
    by_category: Dict[str, str] = {}
    by_carrier: Dict[str, str] = {}
    findings: List[AuditFindingDetail] = []
