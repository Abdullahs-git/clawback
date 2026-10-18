"""
Contract Extraction Pipeline.
Extracts text from PDF contracts, queries Gemma via AMD endpoint,
and runs the mandatory quote verification safeguard on every extracted rule.
"""
import asyncio
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


def normalize_rule_parameters_key(rule: Dict[str, Any]) -> Tuple[str, str]:
    """Generates a canonical signature for a rule to evaluate consensus across self-consistency runs."""
    rtype = str(rule.get("type", "")).strip().lower()
    params = rule.get("parameters", {})
    canonical_items = []
    if isinstance(params, dict):
        for k, v in sorted(params.items()):
            if isinstance(v, (int, float)):
                val_str = f"{float(v):.4f}"
            else:
                val_str = str(v).strip().lower()
            canonical_items.append(f"{k}:{val_str}")
    return rtype, "|".join(canonical_items)


def evaluate_self_consistency_consensus(
    runs_results: List[Dict[str, Any]],
    k: int = 3
) -> List[Dict[str, Any]]:
    """
    Evaluates rule consensus across k parallel extraction runs.
    Accepts a rule as high-confidence only if at least 2 runs agree on type and parameters;
    otherwise marks it needs-review.
    """
    if not runs_results:
        return []

    signatures_map: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}

    for run_data in runs_results:
        rules = run_data.get("rules", [])
        for rule in rules:
            sig = normalize_rule_parameters_key(rule)
            if sig not in signatures_map:
                signatures_map[sig] = []
            signatures_map[sig].append(rule)

    consensus_rules: List[Dict[str, Any]] = []
    for sig, matching_rules in signatures_map.items():
        agreed_count = len(matching_rules)
        best_rule = matching_rules[0].copy()
        best_rule["consensus_agreement_count"] = agreed_count
        best_rule["consensus_total_runs"] = k

        if agreed_count >= 2:
            best_rule["consensus_status"] = "high_confidence"
            best_rule["confidence"] = max(best_rule.get("confidence", 0.95), 0.95)
        else:
            best_rule["consensus_status"] = "needs_review"
            best_rule["confidence"] = min(best_rule.get("confidence", 0.65), 0.65)
            if best_rule.get("status") == "approved":
                best_rule["status"] = "proposed"
            best_rule["review_reason"] = f"Only {agreed_count}/{k} extraction runs agreed on parameters"

        consensus_rules.append(best_rule)

    return consensus_rules


async def extract_contract_rules(
    pdf_bytes: bytes,
    filename: str,
    carrier_hint: str = "",
    db: Session = None,
    cache_key: str = None,
    k_runs: int = 3
) -> Dict[str, Any]:
    """
    Executes the full contract extraction pipeline with k=3 self-consistency:
    1. Parse PDF text layer
    2. Query Gemma k=3 in parallel on AMD inference endpoint
    3. Reconcile consensus (requires >= 2 runs agreement)
    4. Apply quote verification and parameter safeguard
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

    # Run k parallel extraction calls on AMD endpoint
    k = max(1, k_runs)
    tasks = [
        amd_llm_client.generate_chat_completion(
            messages=messages,
            operation=f"contract_extraction_run_{i+1}",
            db=db,
            cache_key=cache_key or f"contract_{carrier_hint.lower().replace(' ', '_')}"
        )
        for i in range(k)
    ]

    runs_raw = await asyncio.gather(*tasks, return_exceptions=True)
    valid_runs: List[Dict[str, Any]] = [r for r in runs_raw if isinstance(r, dict)]

    if not valid_runs:
        raise HTTPException(
            status_code=500,
            detail="Contract extraction failed on all inference attempts."
        )

    # Evaluate consensus across the runs
    merged_rules = evaluate_self_consistency_consensus(valid_runs, k=k)

    # Run quote verification safeguard on every proposed rule
    verified_rules = []
    for r in merged_rules:
        verified_rule = apply_quote_verification_safeguard(r, pages_text_map, full_text)
        verified_rules.append(verified_rule)

    extraction_result = valid_runs[0].copy()
    extraction_result["rules"] = verified_rules
    extraction_result["self_consistency_k"] = k
    if carrier_hint and not extraction_result.get("carrier_name"):
        extraction_result["carrier_name"] = carrier_hint

    return extraction_result

