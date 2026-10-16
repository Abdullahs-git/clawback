"""
SQLAlchemy models for carrier dispute letters.
"""
from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from backend.app.database import Base


class DisputeLetter(Base):
    __tablename__ = "dispute_letters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(String(36), nullable=False, index=True)
    carrier_name = Column(String(255), nullable=False, index=True)
    carrier_contact_email = Column(String(255), nullable=True)
    shipper_name = Column(String(255), nullable=False, default="Shipper Operations")
    shipper_contact_name = Column(String(255), nullable=True)
    shipper_contact_email = Column(String(255), nullable=True)
    date_generated = Column(String(50), nullable=False)
    earliest_deadline_date = Column(String(50), nullable=True)
    total_claim_amount = Column(String(50), nullable=False)  # Decimal formatted string
    total_disputed_items = Column(Integer, nullable=False, default=0)
    subject_line = Column(String(500), nullable=False)
    body_markdown = Column(Text, nullable=False)
    evidence_table = Column(JSON, nullable=False)
    status = Column(String(30), nullable=False, default="draft", index=True)  # draft, approved, exported
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
