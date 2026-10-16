"""
SQLAlchemy models for invoice batches and normalized line items.
"""
from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base


class InvoiceBatch(Base):
    __tablename__ = "invoice_batches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    carrier_name = Column(String(255), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    total_lines = Column(Integer, default=0, nullable=False)
    total_billed_amount = Column(String(50), default="0.00", nullable=False)

    lines = relationship("InvoiceLine", back_populates="batch", cascade="all, delete-orphan")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id = Column(String(50), primary_key=True)
    batch_id = Column(String(36), ForeignKey("invoice_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_number = Column(String(100), nullable=False, index=True)
    invoice_date = Column(String(50), nullable=False, index=True)
    shipment_id = Column(String(100), nullable=False, index=True)
    charge_code = Column(String(50), nullable=False, index=True)
    charge_description = Column(String(255), nullable=True)
    service_level = Column(String(100), nullable=True)
    origin_zip = Column(String(20), nullable=True)
    destination_zip = Column(String(20), nullable=True)
    zone = Column(String(20), nullable=True)
    weight_actual_lbs = Column(Float, nullable=True)
    dim_length_in = Column(Float, nullable=True)
    dim_width_in = Column(Float, nullable=True)
    dim_height_in = Column(Float, nullable=True)
    billed_weight_lbs = Column(Float, nullable=True)
    published_rate = Column(String(50), nullable=True)
    discount_applied_percent = Column(String(50), nullable=True)
    fuel_surcharge_percent = Column(String(50), nullable=True)
    amount_billed = Column(String(50), nullable=False)  # Decimal formatted string

    batch = relationship("InvoiceBatch", back_populates="lines")
