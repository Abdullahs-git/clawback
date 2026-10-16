"""
Quote Verifier Safeguard.
Non-negotiable principle: A rule whose source_quote cannot be found in the contract text
is automatically rejected as unsupported.
"""
import re
from typing import Dict, Any, Tuple


def normalize_text_for_comparison(text: str) -> str:
    """Normalizes whitespace and standard quotes for robust substring verification."""
    if not text:
        return ""
    # Standardize quotation marks and dashes
    t = text.replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")
    t = t.replace('—', '-').replace('–', '-')
    # Normalize consecutive whitespaces and newlines
    t = re.sub(r'\s+', ' ', t).strip().lower()
    return t


def verify_source_quote(
    source_quote: str,
    page_text: str,
    full_contract_text: str
) -> Tuple[bool, str]:
    """
    Verifies that the extracted source_quote exists verbatim in the contract page.
    Returns: (is_verified, reason)
    """
    if not source_quote or len(source_quote.strip()) < 5:
        return False, "Source quote is missing or too short to verify."

    norm_quote = normalize_text_for_comparison(source_quote)
    norm_page = normalize_text_for_comparison(page_text)
    norm_full = normalize_text_for_comparison(full_contract_text)

    # 1. Check exact or normalized match on specified page
    if norm_quote in norm_page:
        return True, "Verified in page text."

    # 2. Check if text exists elsewhere in the document (wrong page cited)
    if norm_quote in norm_full:
        return True, "Verified in document (page citation offset)."

    return False, "Unverifiable source quote: verbatim text not found in contract document."


def apply_quote_verification_safeguard(
    rule_dict: Dict[str, Any],
    pages_text_map: Dict[int, str],
    full_text: str
) -> Dict[str, Any]:
    """
    Inspects rule source_quote and updates status to 'rejected' if unverified.
    """
    source_page = rule_dict.get("source_page", 1)
    source_quote = rule_dict.get("source_quote", "")
    page_text = pages_text_map.get(source_page, "")

    is_verified, reason = verify_source_quote(source_quote, page_text, full_text)

    if not is_verified:
        rule_dict["status"] = "rejected"
        rule_dict["rejection_reason"] = reason
        rule_dict["confidence"] = min(float(rule_dict.get("confidence", 0.5)), 0.2)
    else:
        if rule_dict.get("status") != "rejected":
            rule_dict["status"] = "proposed"

    return rule_dict
