"""
SQLAlchemy models for contracts and extracted contract rules.
"""
from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    carrier_name = Column(String(255), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    contract_reference = Column(String(255), nullable=True)
    effective_date = Column(String(50), nullable=True)
    expiration_date = Column(String(50), nullable=True)
    text_content = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    rules = relationship("ContractRule", back_populates="contract", cascade="all, delete-orphan")


class ContractRule(Base):
    __tablename__ = "contract_rules"

    id = Column(String(50), primary_key=True)  # e.g., RULE-001 or UUID
    contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    parameters = Column(JSON, nullable=False)
    source_page = Column(Integer, nullable=False)
    source_quote = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)
    status = Column(String(20), nullable=False, default="proposed", index=True)  # proposed, approved, rejected
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    contract = relationship("Contract", back_populates="rules")
