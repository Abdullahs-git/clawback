"""
AMD Operational Status and Telemetry API Router.
Powers the AMD Panel in the UI.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.models.amd_metric import AmdMetricLog
from backend.app.schemas.amd import AmdPanelMetricsResponse, AmdRecentCall
from backend.app.services.llm_client import amd_llm_client

router = APIRouter(prefix="/api", tags=["AMD Telemetry"])


@router.get("/amd-status", response_model=AmdPanelMetricsResponse)
async def get_amd_status(db: Session = Depends(get_db)):
    """
    Returns live operational status, latency, tokens/sec, and recent call logs.
    Shows the AMD model running and whether current mode is 'live' or 'replay'.
    """
    is_connected = await amd_llm_client.check_connectivity()
    recent_logs = db.query(AmdMetricLog).order_by(desc(AmdMetricLog.timestamp)).limit(20).all()

    total_calls = db.query(AmdMetricLog).count()
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_latency = 0.0

    recent_calls_data = []
    for log in recent_logs:
        total_prompt_tokens += log.prompt_tokens
        total_completion_tokens += log.completion_tokens
        total_latency += log.latency_ms

        recent_calls_data.append(
            AmdRecentCall(
                call_id=log.id,
                timestamp=log.timestamp,
                operation=log.operation,
                latency_ms=log.latency_ms,
                prompt_tokens=log.prompt_tokens,
                completion_tokens=log.completion_tokens,
                tokens_per_second=log.tokens_per_second,
                mode=log.mode,
                status=log.status
            )
        )

    avg_latency = (total_latency / len(recent_logs)) if recent_logs else 0.0
    avg_tps = (
        sum(r.tokens_per_second for r in recent_calls_data) / len(recent_calls_data)
    ) if recent_calls_data else 0.0

    return AmdPanelMetricsResponse(
        model_name=amd_llm_client.model,
        endpoint_host=amd_llm_client.sanitized_host,
        mode=amd_llm_client.mode,
        is_connected=is_connected,
        total_calls=total_calls,
        total_prompt_tokens=total_prompt_tokens,
        total_completion_tokens=total_completion_tokens,
        average_latency_ms=round(avg_latency, 1),
        average_tokens_per_second=round(avg_tps, 1),
        recent_calls=recent_calls_data
    )
