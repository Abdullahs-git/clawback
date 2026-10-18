"""
Pydantic v2 schemas for AMD panel metrics and telemetry.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class AmdRecentCall(BaseModel):
    call_id: str
    timestamp: datetime
    operation: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    tokens_per_second: float
    mode: str
    status: str
    model_config = ConfigDict(from_attributes=True)


class AmdPanelMetricsResponse(BaseModel):
    model_name: str
    endpoint_host: str
    mode: str
    is_connected: bool
    total_calls: int
    total_prompt_tokens: int
    total_completion_tokens: int
    average_latency_ms: float
    average_tokens_per_second: float
    last_live_call_timestamp: Optional[datetime] = None
    recent_calls: List[AmdRecentCall] = []
