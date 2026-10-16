"""
SQLAlchemy models for audit findings produced by deterministic rules engine.
"""
from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text
from backend.app.database import Base


class AuditFinding(Base):
    __tablename__ = "audit_findings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(String(36), nullable=False, index=True)
    contract_id = Column(String(36), nullable=False, index=True)
    carrier_name = Column(String(255), nullable=False, index=True)
    invoice_number = Column(String(100), nullable=False, index=True)
    invoice_date = Column(String(50), nullable=False)
    line_id = Column(String(50), nullable=False, index=True)
    shipment_id = Column(String(100), nullable=False, index=True)
    charge_code = Column(String(50), nullable=False, index=True)
    rule_id = Column(String(50), nullable=False, index=True)
    rule_type = Column(String(50), nullable=False, index=True)
    rule_description = Column(Text, nullable=False)
    contract_page = Column(Integer, nullable=False)
    contract_clause_quote = Column(Text, nullable=False)
    expected_amount = Column(String(50), nullable=False)  # Decimal formatted string
    billed_amount = Column(String(50), nullable=False)    # Decimal formatted string
    overcharge_amount = Column(String(50), nullable=False) # Decimal formatted string
    calculation_math = Column(Text, nullable=False)
    claim_deadline_date = Column(String(50), nullable=True)
    days_remaining_to_claim = Column(Integer, nullable=True)
    status = Column(String(30), nullable=False, default="open", index=True)  # open, included_in_dispute, resolved, dismissed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
