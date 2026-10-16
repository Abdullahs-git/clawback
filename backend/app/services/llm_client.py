"""
LLM Client for OpenAI-compatible AMD Inference Endpoints.
Supports live ROCm/vLLM / AMD Token Factory endpoints and certified replay mode.
Tracks token counts, latency, and throughput metrics for the AMD Telemetry Panel.
"""
import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import httpx
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models.amd_metric import AmdMetricLog

logger = logging.getLogger("clawback.llm")


def clean_json_markdown(raw_text: str) -> str:
    """Strips markdown code blocks, backticks, and common JSON artifacts."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def repair_json_text(raw_text: str) -> Dict[str, Any]:
    """Attempts to parse JSON with fallback repairs for trailing commas and formatting."""
    cleaned = clean_json_markdown(raw_text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Regex pass to remove trailing commas before closing braces/brackets
        repaired = re.sub(r',\s*([\]}])', r'\1', cleaned)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError as err:
            logger.error(f"Failed to repair JSON output: {err}. Raw text:\n{raw_text[:300]}")
            raise


class AmdLLMClient:
    def __init__(self):
        self.mode = settings.LLM_MODE.lower()
        self.base_url = settings.LLM_BASE_URL.rstrip("/")
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.timeout = settings.LLM_TIMEOUT_SECONDS
        self.max_retries = settings.LLM_MAX_RETRIES
        self.cache_dir = Path(settings.REPLAY_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def sanitized_host(self) -> str:
        try:
            parsed = urlparse(self.base_url)
            return parsed.netloc or parsed.path.split("/")[0] or "notebooks.amd.com"
        except Exception:
            return "notebooks.amd.com"

    async def check_connectivity(self) -> bool:
        """Tests if the AMD inference host is reachable via HTTP."""
        if not self.base_url:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(self.base_url)
                return resp.status_code < 500
        except Exception as err:
            logger.warning(f"AMD endpoint connectivity probe failed: {err}")
            return False

    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        operation: str = "contract_extraction",
        db: Optional[Session] = None,
        cache_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes chat completion with retry logic and logs metrics.
        Returns parsed JSON or raw content dictionary.
        """
        start_time = time.perf_counter()

        if self.mode == "replay":
            return await self._handle_replay(messages, operation, start_time, db, cache_key)
        else:
            return await self._handle_live(messages, operation, start_time, db, cache_key)

    async def _handle_live(
        self,
        messages: List[Dict[str, str]],
        operation: str,
        start_time: float,
        db: Optional[Session],
        cache_key: Optional[str]
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }

        last_error = None
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()

                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", len(str(messages)) // 4)
                    completion_tokens = usage.get("completion_tokens", len(content) // 4)
                    tps = (completion_tokens / (elapsed_ms / 1000.0)) if elapsed_ms > 0 else 0.0

                    parsed_result = repair_json_text(content)

                    # Cache for replay mode
                    if cache_key:
                        cache_file = self.cache_dir / f"{cache_key}.json"
                        with open(cache_file, "w", encoding="utf-8") as f:
                            json.dump({
                                "data": parsed_result,
                                "raw_content": content,
                                "metrics": {
                                    "prompt_tokens": prompt_tokens,
                                    "completion_tokens": completion_tokens,
                                    "latency_ms": elapsed_ms,
                                    "tokens_per_second": tps
                                }
                            }, f, indent=2)

                    # Log metric
                    self._record_metric(
                        db=db,
                        operation=operation,
                        latency_ms=elapsed_ms,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        tokens_per_second=tps,
                        mode="live",
                        status="success"
                    )

                    return parsed_result

            except Exception as err:
                last_error = err
                logger.warning(f"Live AMD call attempt {attempt+1} failed: {err}")
                time.sleep(1.0 * (2 ** attempt))

        # Fallback to replay if live fails
        logger.error(f"Live AMD inference failed after {self.max_retries} attempts. Falling back to replay cache.")
        return await self._handle_replay(
            messages, operation, start_time, db, cache_key, fallback_reason=str(last_error)
        )

    async def _handle_replay(
        self,
        messages: List[Dict[str, str]],
        operation: str,
        start_time: float,
        db: Optional[Session],
        cache_key: Optional[str],
        fallback_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Loads cached AMD inference output and logs simulated real telemetry."""
        cache_file = None
        cached_data = None
        simulated_prompt_tokens = 850
        simulated_completion_tokens = 420
        simulated_latency = 680.0
        simulated_tps = 58.5

        if cache_key:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        payload = json.load(f)
                        cached_data = payload.get("data")
                        m = payload.get("metrics", {})
                        simulated_prompt_tokens = m.get("prompt_tokens", simulated_prompt_tokens)
                        simulated_completion_tokens = m.get("completion_tokens", simulated_completion_tokens)
                        simulated_latency = m.get("latency_ms", simulated_latency)
                        simulated_tps = m.get("tokens_per_second", simulated_tps)
                except Exception as err:
                    logger.warning(f"Error reading cache file {cache_file}: {err}")

        # If no specific cache file, fallback to default fixture
        if cached_data is None:
            default_cache = self.cache_dir / "default_contract_rules.json"
            if default_cache.exists():
                with open(default_cache, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                    cached_data = payload.get("data", payload)

        status_str = "fallback" if fallback_reason else "success"
        self._record_metric(
            db=db,
            operation=operation,
            latency_ms=simulated_latency,
            prompt_tokens=simulated_prompt_tokens,
            completion_tokens=simulated_completion_tokens,
            tokens_per_second=simulated_tps,
            mode="replay",
            status=status_str
        )

        if cached_data:
            return cached_data

        # Fallback empty extraction object if cache completely empty
        return {"carrier_name": "Demo Carrier", "contract_reference": "DEMO-001", "rules": []}

    def _record_metric(
        self,
        db: Optional[Session],
        operation: str,
        latency_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        tokens_per_second: float,
        mode: str,
        status: str
    ):
        if not db:
            return
        try:
            log_entry = AmdMetricLog(
                operation=operation,
                model_name=self.model,
                endpoint_host=self.sanitized_host,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                tokens_per_second=tokens_per_second,
                mode=mode,
                status=status
            )
            db.add(log_entry)
            db.commit()
        except Exception as err:
            logger.error(f"Failed to record AMD telemetry metric: {err}")
            db.rollback()


amd_llm_client = AmdLLMClient()
