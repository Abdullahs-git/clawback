"""
SQLAlchemy models for AMD inference telemetry and operational performance metrics.
"""
from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime
from backend.app.database import Base


class AmdMetricLog(Base):
    __tablename__ = "amd_metric_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    operation = Column(String(100), nullable=False)
    model_name = Column(String(100), nullable=False)
    endpoint_host = Column(String(255), nullable=False)
    latency_ms = Column(Float, nullable=False)
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    tokens_per_second = Column(Float, nullable=False, default=0.0)
    mode = Column(String(20), nullable=False)  # live, replay
    status = Column(String(20), nullable=False, default="success")  # success, error, fallback
