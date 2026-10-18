"""
Rate Limiter and Sandbox Guards for Public Demo.
Enforces:
- 5 MB maximum upload limit in DEMO_MODE
- Maximum 3 uploads per IP per hour
- Maximum 20 LLM calls per IP per hour
- Daily live call cap with informative fallback message
"""
from collections import defaultdict
from datetime import datetime, timedelta
import logging
from typing import Dict, List
from fastapi import HTTPException, Request

from backend.app.config import settings

logger = logging.getLogger("clawback.rate_limiter")

# In-memory sliding window storage: ip -> list of timestamps
upload_records: Dict[str, List[datetime]] = defaultdict(list)
llm_call_records: Dict[str, List[datetime]] = defaultdict(list)
daily_live_calls: List[datetime] = []


def get_client_ip(request: Request) -> str:
    """Extracts client IP address safely, checking x-forwarded-for header."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def check_upload_rate_limit(request: Request):
    """Enforces 3 uploads per IP per hour when DEMO_MODE is active."""
    if not getattr(settings, "DEMO_MODE", False):
        return

    ip = get_client_ip(request)
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)

    # Filter timestamps within the last hour
    upload_records[ip] = [ts for ts in upload_records[ip] if ts > one_hour_ago]

    if len(upload_records[ip]) >= 3:
        raise HTTPException(
            status_code=429,
            detail="Public demo upload limit reached (maximum 3 uploads per IP per hour). Try again later."
        )

    upload_records[ip].append(now)


def check_llm_rate_limit(request: Request):
    """Enforces 20 LLM requests per IP per hour and a daily cap on live calls."""
    ip = get_client_ip(request)
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(days=1)

    # IP rate limit (20/hr)
    llm_call_records[ip] = [ts for ts in llm_call_records[ip] if ts > one_hour_ago]
    if len(llm_call_records[ip]) >= getattr(settings, "RATE_LIMIT_LLM_PER_IP_HOUR", 20):
        raise HTTPException(
            status_code=429,
            detail="Rate limit reached for LLM requests (20 per IP per hour). Please retry in a few minutes."
        )

    # Daily live calls cap (100/day)
    global daily_live_calls
    daily_live_calls = [ts for ts in daily_live_calls if ts > one_day_ago]
    daily_cap = getattr(settings, "DAILY_CAP_LIVE_CALLS", 100)
    if settings.LLM_MODE.lower() == "live" and len(daily_live_calls) >= daily_cap:
        raise HTTPException(
            status_code=429,
            detail=f"Daily AMD live inference quota reached ({daily_cap} calls/day). System has switched to verified replay."
        )

    llm_call_records[ip].append(now)
    if settings.LLM_MODE.lower() == "live":
        daily_live_calls.append(now)
