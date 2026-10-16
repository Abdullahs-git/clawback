"""
Contract Extraction Pipeline.
Extracts text from PDF contracts, queries Gemma via AMD endpoint,
and runs the mandatory quote verification safeguard on every extracted rule.
"""
import io
import json
import logging
from typing import Any, Dict, List, Tuple
from pypdf import PdfReader
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.services.llm_client import amd_llm_client
from backend.app.services.quote_verifier import apply_quote_verification_safeguard

logger = logging.getLogger("clawback.extraction")

EXTRACTION_SYSTEM_PROMPT = """
You are a senior freight contract auditor and legal parsing agent.
Your task is to analyze carrier contracts and extract all commercial rules and rates into a strict JSON object.

Extract the following rule types when present:
1. base_discount: percentage off published rate (parameters: {"percentage": 0.40, "service_level": "Ground"})
2. accessorial_rule: accessorial fee terms (parameters: {"fee_type": "residential", "allowed": false, "cap": "45.00", "rate": "10.00"})
3. fuel_surcharge: fuel terms (parameters: {"fixed_percentage": 0.12, "max_percentage": 0.15})
4. dim_weight_divisor: dimensional weight divisor (parameters: {"divisor": 166})
5. minimum_charge: absolute minimum charge floor (parameters: {"amount": "45.00"})
6. duplicate_charge: duplicate billing prohibition (parameters: {"enabled": true})
7. claim_window_days: dispute window in days (parameters: {"days": 180})

MANDATORY RULES:
- Every rule MUST have a verbatim "source_quote" copied EXACTLY from the contract text. Any made-up or paraphrased quote will be automatically rejected.
- Provide the exact 1-based "source_page" where the quote appears.
- Do NOT compute money. Represent percentages as decimals (e.g. 0.40 for 40%) or strings.
- Output ONLY valid JSON matching this schema:
{
  "carrier_name": "String",
  "contract_reference": "String",
  "effective_date": "YYYY-MM-DD or null",
  "expiration_date": "YYYY-MM-DD or null",
  "rules": [
    {
      "id": "RULE-001",
      "type": "base_discount",
      "description": "40% discount on Ground shipments",
      "parameters": {"percentage": 0.40, "service_level": "Ground"},
      "source_page": 2,
      "source_quote": "Shipper shall receive a 40% discount off standard rates.",
      "confidence": 0.95
    }
  ]
}
"""


def extract_text_from_pdf(pdf_bytes: bytes) -> Tuple[Dict[int, str], str]:
    """
    Extracts text per page from PDF bytes using pypdf.
    Returns: (pages_text_map: {1: "page 1 text", ...}, full_text: "combined text")
    """
    pages_text_map: Dict[int, str] = {}
    full_text_parts: List[str] = []

    reader = PdfReader(io.BytesIO(pdf_bytes))
    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages_text_map[idx] = text
        full_text_parts.append(f"--- PAGE {idx} ---\n{text}\n")

    full_text = "\n".join(full_text_parts)
    return pages_text_map, full_text


async def extract_contract_rules(
    pdf_bytes: bytes,
    filename: str,
    carrier_hint: str = "",
    db: Session = None,
    cache_key: str = None
) -> Dict[str, Any]:
    """
    Executes the full contract extraction pipeline:
    1. Parse PDF text layer
    2. Query Gemma on AMD inference endpoint
    3. Apply quote verification safeguard
    """
    pages_text_map, full_text = extract_text_from_pdf(pdf_bytes)
    # If no text was extracted from any page, reject as scanned image PDF
    if not "".join(pages_text_map.values()).strip():
        raise HTTPException(
            status_code=400,
            detail="Scanned image detected. Upload a text PDF or CSV."
        )

    # Prepare extraction prompt with contract text
    prompt = f"Carrier Hint: {carrier_hint}\nFilename: {filename}\n\nDocument Text:\n{full_text[:12000]}"
    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    # Query LLM (live AMD or verified replay)
    extraction_raw = await amd_llm_client.generate_chat_completion(
        messages=messages,
        operation="contract_extraction",
        db=db,
        cache_key=cache_key or f"contract_{carrier_hint.lower().replace(' ', '_')}"
    )

    # Run quote verification safeguard on every proposed rule
    rules = extraction_raw.get("rules", [])
    verified_rules = []
    for r in rules:
        verified_rule = apply_quote_verification_safeguard(r, pages_text_map, full_text)
        verified_rules.append(verified_rule)

    extraction_raw["rules"] = verified_rules
    if carrier_hint and not extraction_raw.get("carrier_name"):
        extraction_raw["carrier_name"] = carrier_hint

    return extraction_raw
