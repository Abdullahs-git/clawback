"""
Pydantic v2 schemas for contracts and rules.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ContractRuleBase(BaseModel):
    id: str = Field(..., description="Rule ID (e.g. RULE-001)")
    type: str = Field(..., description="Rule type")
    description: str = Field(..., description="Summary of rule")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Rule parameters")
    source_page: int = Field(..., ge=1, description="Page number")
    source_quote: str = Field(..., min_length=5, description="Verbatim text from contract")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    status: str = Field(default="proposed", description="proposed, approved, rejected")
    rejection_reason: Optional[str] = None


class ContractRuleCreate(ContractRuleBase):
    pass


class ContractRuleUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(proposed|approved|rejected)$")
    parameters: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    rejection_reason: Optional[str] = None


class ContractRuleResponse(ContractRuleBase):
    contract_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ContractBatchRulesUpdate(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    rule_ids: List[str]


class ContractSummaryResponse(BaseModel):
    id: str
    carrier_name: str
    filename: str
    uploaded_at: datetime
    rule_count: int = 0
    approved_rule_count: int = 0
    model_config = ConfigDict(from_attributes=True)


class ContractDetailResponse(BaseModel):
    id: str
    carrier_name: str
    filename: str
    contract_reference: Optional[str] = None
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    uploaded_at: datetime
    rules: List[ContractRuleResponse] = []
    model_config = ConfigDict(from_attributes=True)
