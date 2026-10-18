"""
Charge-Description Normalization Service.
Maps non-standard carrier charge descriptions (e.g. 'RESI DLVRY', 'LIFT GATE SVC')
to a strict canonical charge code whitelist using Gemma on AMD ROCm.
All outputs are validated against the whitelist.
STRICT INVARIANT: The LLM never processes, touches, or generates dollar amounts.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional, Set
from sqlalchemy.orm import Session

from backend.app.services.llm_client import amd_llm_client

logger = logging.getLogger("clawback.normalization")

CANONICAL_CHARGE_CODES: Set[str] = {
    "BASE",        # Base freight linehaul / standard charge
    "RES",         # Residential delivery / pickup
    "LFG",         # Liftgate service
    "FUEL",        # Fuel surcharge
    "MIN",         # Absolute minimum floor charge
    "HAZ",         # Hazardous materials handling
    "NOTIFY",      # Prior notification of delivery
    "STORAGE",     # Storage / redelivery detention
    "INSIDE",      # Inside delivery / pickup
    "LTD_ACCESS",  # Limited access location
    "OVERLENGTH"   # Overlength / oversize package
}

KNOWN_ABBREVIATIONS: Dict[str, str] = {
    "RESI DLVRY": "RES",
    "RESIDENTIAL DELIVERY": "RES",
    "RES DELIVERY": "RES",
    "RESIDENTIAL": "RES",
    "LIFT GATE SVC": "LFG",
    "LIFTGATE": "LFG",
    "LIFTGATE PICKUP": "LFG",
    "LIFTGATE DELIVERY": "LFG",
    "FUEL SURCHARGE": "FUEL",
    "FSC": "FUEL",
    "DIESEL SURCHARGE": "FUEL",
    "INSIDE PICKUP": "INSIDE",
    "INSIDE DLVRY": "INSIDE",
    "INSIDE DELIVERY": "INSIDE",
    "HAZMAT": "HAZ",
    "HAZARDOUS MATERIAL": "HAZ",
    "HAZMAT SURCHARGE": "HAZ",
    "LIMITED ACCESS": "LTD_ACCESS",
    "LTD ACCESS": "LTD_ACCESS",
    "NOTIFY PRIOR": "NOTIFY",
    "NOTIFICATION": "NOTIFY",
    "STORAGE CHG": "STORAGE",
    "STORAGE FEE": "STORAGE",
    "OVERSIZE": "OVERLENGTH",
    "OVERLENGTH": "OVERLENGTH",
    "BASE RATE": "BASE",
    "LINEHAUL": "BASE",
    "FRT": "BASE",
}

NORMALIZATION_SYSTEM_PROMPT = f"""
You are a freight billing classification specialist.
Your task is to map messy, abbreviated carrier invoice charge descriptions to standard canonical charge codes.

ALLOWED CANONICAL CODES:
{', '.join(sorted(CANONICAL_CHARGE_CODES))}

RULES:
1. Map each raw description to exactly one canonical code.
2. If uncertain, map to "UNKNOWN".
3. Provide a confidence between 0.00 and 1.00.
4. DO NOT process, compute, or output any currency or dollar amounts.
5. Return ONLY a valid JSON object matching this schema:
{{
  "mappings": [
    {{
      "raw_description": "String",
      "canonical_code": "One of the allowed codes or UNKNOWN",
      "confidence": 0.95
    }}
  ]
}}
"""


def validate_normalization_output(raw_result: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Validates LLM normalization output against the strict canonical whitelist.
    Enforces that unknown or low-confidence (<0.85) mappings require human review.
    """
    validated: Dict[str, Dict[str, Any]] = {}
    mappings = raw_result.get("mappings", [])

    for item in mappings:
        desc = item.get("raw_description", "").strip()
        code = str(item.get("canonical_code", "")).strip().upper()
        try:
            confidence = float(item.get("confidence", 0.0))
        except (ValueError, TypeError):
            confidence = 0.0

        if code in CANONICAL_CHARGE_CODES and confidence >= 0.85:
            validated[desc] = {
                "raw_description": desc,
                "canonical_code": code,
                "confidence": confidence,
                "needs_review": False,
                "status": "normalized"
            }
        else:
            validated[desc] = {
                "raw_description": desc,
                "canonical_code": code if code in CANONICAL_CHARGE_CODES else "UNKNOWN",
                "confidence": confidence,
                "needs_review": True,
                "status": "needs_review"
            }

    return validated


async def normalize_charge_descriptions(
    descriptions: List[str],
    db: Optional[Session] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Normalizes a list of distinct charge descriptions.
    Uses Gemma on AMD ROCm, with verified deterministic replay cache fallback.
    """
    unique_descs = list({d.strip() for d in descriptions if d and d.strip()})
    if not unique_descs:
        return {}

    # Check for known deterministic abbreviations first for instantaneous exact matching
    cached_mappings: Dict[str, Dict[str, Any]] = {}
    remaining_to_query: List[str] = []

    for d in unique_descs:
        upper_d = d.upper()
        if upper_d in KNOWN_ABBREVIATIONS:
            cached_mappings[d] = {
                "raw_description": d,
                "canonical_code": KNOWN_ABBREVIATIONS[upper_d],
                "confidence": 1.0,
                "needs_review": False,
                "status": "normalized"
            }
        else:
            remaining_to_query.append(d)

    if not remaining_to_query:
        return cached_mappings

    # Query LLM on AMD endpoint
    user_prompt = f"Map the following {len(remaining_to_query)} charge descriptions to canonical codes:\n"
    user_prompt += "\n".join(f"- {d}" for d in remaining_to_query)

    messages = [
        {"role": "system", "content": NORMALIZATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    try:
        raw_result = await amd_llm_client.generate_chat_completion(
            messages=messages,
            operation="charge_normalization",
            db=db,
            cache_key="charge_normalization_batch"
        )
        llm_validated = validate_normalization_output(raw_result)
        cached_mappings.update(llm_validated)
    except Exception as err:
        logger.warning(f"Charge normalization LLM query failed: {err}. Falling back to review.")
        for d in remaining_to_query:
            cached_mappings[d] = {
                "raw_description": d,
                "canonical_code": "UNKNOWN",
                "confidence": 0.0,
                "needs_review": True,
                "status": "needs_review"
            }

    return cached_mappings
