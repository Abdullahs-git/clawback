"""
Pydantic v2 schemas for dispute letters.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class DisputeGenerateRequest(BaseModel):
    batch_id: str
    carrier_name: str
    shipper_name: Optional[str] = "Shipper Logistics Operations"
    finding_ids: Optional[List[str]] = None


class DisputeLetterUpdate(BaseModel):
    subject_line: Optional[str] = None
    body_markdown: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|approved|exported)$")
    approved_by: Optional[str] = None


class DisputeLetterResponse(BaseModel):
    id: str
    batch_id: str
    carrier_name: str
    carrier_contact_email: Optional[str] = None
    shipper_name: str
    shipper_contact_name: Optional[str] = None
    shipper_contact_email: Optional[str] = None
    date_generated: str
    earliest_deadline_date: Optional[str] = None
    total_claim_amount: str
    total_disputed_items: int
    subject_line: str
    body_markdown: str
    evidence_table: List[Dict[str, Any]]
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
