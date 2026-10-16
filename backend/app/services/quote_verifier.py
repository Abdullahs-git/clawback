"""
Quote Verifier Safeguard & Parameter-vs-Quote Grounding.
Non-negotiable principles:
1. A rule whose source_quote cannot be found in the contract text is automatically rejected as unsupported.
2. A rule whose extracted parameters (numbers, percentages, waiver booleans) are not substantiated
   by the quote is automatically rejected as 'parameter not supported by quote'.
"""
from decimal import Decimal
import re
from typing import Dict, Any, Tuple, List, Optional

WORD_TO_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90, "hundred": 100,
    "one-half": 0.5, "half": 0.5, "quarter": 0.25,
}

WAIVER_KEYWORDS = [
    "waived", "waiver", "no charge", "shall not apply", "not apply",
    "shall not be assessed", "not be assessed", "free of charge", "prohibited", "waive"
]


def normalize_text_for_comparison(text: str) -> str:
    """Normalizes whitespace and standard quotes for robust substring verification."""
    if not text:
        return ""
    t = text.replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")
    t = t.replace('—', '-').replace('–', '-')
    t = re.sub(r'\s+', ' ', t).strip().lower()
    return t


def parse_spelled_out_number(phrase: str) -> Optional[float]:
    """Parses common contract number phrases such as 'one hundred sixty-six' or 'eleven and one-half'."""
    tokens = re.findall(r'[a-z\-]+', phrase.lower())
    if not tokens:
        return None
    total = 0.0
    current = 0.0
    for tok in tokens:
        if tok == "and":
            continue
        if tok in WORD_TO_NUM:
            val = WORD_TO_NUM[tok]
            if val == 100:
                current = (current if current > 0 else 1.0) * 100
            elif val < 1:  # fraction like half
                current += val
            else:
                current += val
        elif "-" in tok:
            parts = tok.split("-")
            sub_val = 0.0
            for p in parts:
                if p in WORD_TO_NUM:
                    sub_val += WORD_TO_NUM[p]
            current += sub_val
    total += current
    return total if total > 0 else None


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

    # 2. Check if text exists elsewhere in the document (page citation offset)
    if norm_quote in norm_full:
        return True, "Verified in document (page citation offset)."

    return False, "Unverifiable source quote: verbatim text not found in contract document."


def check_value_in_quote(val: Any, quote_text: str) -> bool:
    """
    Determines whether a numeric parameter value is substantiated within the quote.
    Handles exact digits ($40, 40.00, 40), percentages (11.5%, 0.115), and spelled-out words.
    """
    norm_quote = normalize_text_for_comparison(quote_text)

    # Convert val to string and Decimal
    str_val = str(val).strip().replace("$", "")
    try:
        dec_val = Decimal(str_val)
    except Exception:
        return str_val.lower() in norm_quote

    # 1. Direct string representations
    candidates = [
        str_val,
        f"{dec_val:.2f}",
        f"{dec_val:.1f}",
        f"{int(dec_val)}" if dec_val == int(dec_val) else None,
        f"${dec_val:.2f}",
        f"${int(dec_val)}" if dec_val == int(dec_val) else None,
    ]
    # 2. Percentage representation (e.g. 0.45 -> 45%, 45.0%)
    if Decimal("0.00") < dec_val <= Decimal("1.00"):
        pct_val = dec_val * 100
        candidates.extend([
            f"{pct_val:.2f}%",
            f"{pct_val:.1f}%",
            f"{int(pct_val)}%" if pct_val == int(pct_val) else None,
            f"{pct_val:.2f}",
            f"{pct_val:.1f}",
            f"{int(pct_val)}" if pct_val == int(pct_val) else None,
        ])

    for c in filter(None, candidates):
        c_norm = c.lower()
        if c_norm in norm_quote:
            return True

    # 3. Spelled-out words in contract text
    # e.g., 40 -> "forty", 45 -> "forty-five", 166 -> "one hundred sixty-six"
    for word, num in WORD_TO_NUM.items():
        if num == float(dec_val) or (dec_val <= 1 and num == float(dec_val * 100)):
            if word in norm_quote:
                return True

    # Match compound phrases like "forty dollars", "eleven and one-half", "one hundred sixty-six"
    extracted_phrases = re.findall(r'\b(?:[a-z]+(?:-[a-z]+)?(?:\s+(?:and\s+)?[a-z]+(?:-[a-z]+)?)*)\b', norm_quote)
    for phrase in extracted_phrases:
        parsed_num = parse_spelled_out_number(phrase)
        if parsed_num is not None:
            if abs(parsed_num - float(dec_val)) < 0.001:
                return True
            if dec_val <= 1 and abs(parsed_num - float(dec_val * 100)) < 0.001:
                return True

    return False


def validate_parameters_against_quote(rule_dict: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates that every extracted parameter is substantiated by the source quote:
    1. Numbers (cap, rate, fixed_percentage, max_percentage, divisor, amount, percentage, days).
    2. Boolean waivers (allowed = False requires waiver keywords in quote).
    """
    quote = rule_dict.get("source_quote", "")
    params = rule_dict.get("parameters", {})
    norm_quote = normalize_text_for_comparison(quote)

    # Check waiver flag
    if "allowed" in params and params["allowed"] is False:
        has_waiver_keyword = any(kw in norm_quote for kw in WAIVER_KEYWORDS)
        if not has_waiver_keyword:
            return False, "Parameter allowed=False not supported by quote: missing waiver keyword."

    # Check numeric parameters
    numeric_keys = [
        "cap", "rate", "fixed_percentage", "max_percentage", "percentage",
        "divisor", "amount", "days"
    ]
    for k in numeric_keys:
        if k in params and params[k] is not None:
            val = params[k]
            if not check_value_in_quote(val, quote):
                return False, f"Parameter '{k}={val}' not supported by quote."

    return True, "Parameters validated against quote."


def apply_quote_verification_safeguard(
    rule_dict: Dict[str, Any],
    pages_text_map: Dict[int, str],
    full_text: str
) -> Dict[str, Any]:
    """
    Executes two-stage safeguard on proposed rules:
    Stage 1: Verify source_quote exists verbatim in the contract document.
    Stage 2: Verify that rule parameters are grounded in the quote text.
    """
    source_page = rule_dict.get("source_page", 1)
    source_quote = rule_dict.get("source_quote", "")
    page_text = pages_text_map.get(source_page, "")

    # Stage 1: Quote verification
    is_quote_verified, quote_reason = verify_source_quote(source_quote, page_text, full_text)
    if not is_quote_verified:
        rule_dict["status"] = "rejected"
        rule_dict["rejection_reason"] = quote_reason
        rule_dict["confidence"] = min(float(rule_dict.get("confidence", 0.5)), 0.2)
        return rule_dict

    # Stage 2: Parameter-vs-quote grounding
    is_param_grounded, param_reason = validate_parameters_against_quote(rule_dict)
    if not is_param_grounded:
        rule_dict["status"] = "rejected"
        rule_dict["rejection_reason"] = param_reason
        rule_dict["confidence"] = min(float(rule_dict.get("confidence", 0.5)), 0.2)
        return rule_dict

    # Passed both stages
    if rule_dict.get("status") != "rejected":
        rule_dict["status"] = "proposed"
        rule_dict["rejection_reason"] = None

    return rule_dict
