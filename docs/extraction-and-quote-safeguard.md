# Clawback Contract Extraction Pipeline & Quote Safeguard

A primary failure mode of LLMs in legal and financial domains is "hallucination"—inventing plausible-sounding contract clauses, discount percentages, or fee waivers that do not actually exist in the signed agreement.

Clawback eliminates this risk through an automated, deterministic **Quote Verification Safeguard** that intercepts every rule proposed by Google Gemma 2 (9B-IT) before it can be presented to a human or applied in an audit.

---

## 1. Extraction Pipeline Architecture

```
[Contract PDF]
      |
      v
[extract_text_from_pdf (pypdf)]
      |
      +---> [Scanned Image Check] ---> (0 text found? Halt: HTTP 400 "Scanned image detected")
      |
      +---> [Page Text Map: {1: "...", 2: "..."}]
      |
      v
[Gemma 2 9B-IT on AMD ROCm / vLLM]
      |
      v
[clean_json_markdown & repair_json_text]
      |
      v
[apply_quote_verification_safeguard]
      |
      +---> Verbatim quote found on page? ---> status = "proposed" (Verified)
      |
      +---> Verbatim quote NOT in text?    ---> status = "rejected" (Unsupported)
```

---

## 2. Scanned Image Detection

Carrier agreements provided as scanned raster images (e.g., flat TIFF/JPEG embedded in a PDF without an OCR text layer) cannot be reliably parsed without introducing OCR transcription errors.

In accordance with Plan v2:
- `extract_text_from_pdf` aggregates text across all pages.
- If `not "".join(pages_text_map.values()).strip()`, the API halts immediately:
  ```json
  {
    "detail": "Scanned image detected. Upload a text PDF or CSV."
  }
  ```
- This prevents silent parsing failures and prompts the user to supply digital text PDFs or standard billing CSVs.

---

## 3. Gemma 2 9B-IT Prompt Engineering

Contract extraction utilizes a constrained system prompt enforcing strict structural outputs:

```text
You are a senior freight contract auditor and legal parsing agent.
Your task is to analyze carrier contracts and extract all commercial rules and rates into a strict JSON object.

MANDATORY RULES:
- Every rule MUST have a verbatim "source_quote" copied EXACTLY from the contract text. Any made-up or paraphrased quote will be automatically rejected.
- Provide the exact 1-based "source_page" where the quote appears.
- Do NOT compute money. Represent percentages as decimals (e.g. 0.40 for 40%) or strings.
- Output ONLY valid JSON matching this schema...
```

---

## 4. JSON Repair Layer (`repair_json_text`)

LLM responses often include Markdown wrappers, commentary, or minor syntactic errors. The repair pipeline executes:
1. **Markdown Stripping**: Strips opening ```json and closing ``` blocks using regular expressions.
2. **Trailing Comma Resolution**: Removes invalid trailing commas prior to closing braces or brackets (`, \s*([\]}])` -> `\1`).
3. **Fail-Fast Parse**: If JSON parsing fails after repair, an explicit exception is logged rather than falling back to guessing.

---

## 5. The Quote Verification Safeguard Algorithm

The safeguard functions as an automated verifier:

```python
def verify_quote_against_contract(
    source_quote: str,
    source_page: int,
    pages_text_map: Dict[int, str],
    full_text: str
) -> Tuple[bool, str]:
    if not source_quote or len(source_quote.strip()) < 8:
        return False, "Source quote is empty or too short to verify."

    clean_quote = normalize_text(source_quote)

    # 1. Page-specific verification
    if source_page in pages_text_map:
        page_text = normalize_text(pages_text_map[source_page])
        if clean_quote in page_text:
            return True, "Verified on specified page."

    # 2. Document-wide verification (fallback if page index is off by 1)
    norm_full = normalize_text(full_text)
    if clean_quote in norm_full:
        return True, "Verified in document text."

    return False, "Unverifiable source quote: verbatim text not found in contract document."
```

### Verification Outcomes:
- **Verified Clauses**: Marked `status = "proposed"`. Displayed in the UI with a verified badge ready for clerk sign-off.
- **Unverified Clauses**: Marked `status = "rejected"`. Displayed in the UI with an amber/red warning banner, citing the rejection reason. These rules are **strictly excluded** from audit execution.
