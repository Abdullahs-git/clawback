# Clawback System Design

## 1. System Mission & Core Philosophy

In commercial logistics, freight contracts are multi-page, dense legal agreements filled with variable base discount tiers, conditional accessorial fees (e.g., liftgate caps, residential waivers), fuel index surcharge tables, dimensional weight divisor formulas, and strict dispute claim windows. 

Because accounts payable (AP) clerks lack the time to manually cross-reference thousands of CSV invoice lines against these contracts, shippers routinely overpay carrier bills. Existing outsourced audit firms exploit this gap by charging 20% to 50% contingency fees on recovered funds.

**Clawback** was architected from first principles as an **intelligent AP copilot** designed for private deployment on AMD infrastructure. It combines LLM text extraction for legal contracts with deterministic Python arithmetic for billing audits, guaranteeing zero hallucinated math, 100% legal traceability, and zero ungrounded claims.

---

## 2. Non-Negotiable System Invariants

The Clawback architecture enforces five non-negotiable invariants:

```
+-----------------------------------------------------------------------------------------+
|                                CLAWBACK SYSTEM INVARIANTS                               |
+-----------------------------------------------------------------------------------------+
| 1. ZERO LLM MATH             | LLMs extract contract text; pure Python Decimal calculates|
|                              | all dollar deltas. Floats are banned via AST analysis.  |
| ---------------------------- | --------------------------------------------------------|
| 2. 100% TRACEABILITY         | Every audit finding links to line ID, rule ID, contract  |
|                              | page, verbatim clause quote, and step-by-step arithmetic.|
| ---------------------------- | --------------------------------------------------------|
| 3. QUOTE SAFEGUARD           | Extracted rules are checked against contract text.       |
|                              | Unverified quotes are automatically rejected.           |
| ---------------------------- | --------------------------------------------------------|
| 4. HUMAN-IN-THE-LOOP         | Clerks review and approve proposed rules and dispute     |
|                              | letters before any action is finalized or exported.     |
| ---------------------------- | --------------------------------------------------------|
| 5. REPRODUCIBLE REPLAY       | Offline evaluations use verified AMD fixtures with a     |
|                              | visible UI badge. Demo data is labeled synthetic.        |
+-----------------------------------------------------------------------------------------+
```

---

## 3. High-Level Pipeline Architecture

```
[Contract PDF] ---> [pypdf Text Extraction] ---> [Gemma 2 on AMD ROCm] ---> [Proposed Rules]
                                                             |
                                                             v
                                             [Quote Verification Safeguard]
                                             (Auto-rejects unverified quotes)
                                                             |
                                                             v
                                                  [Human Rule Approval]
                                                             |
                                                             v
[Invoice CSV/Lines] ------------------------> [Deterministic Audit Engine]
                                              (Pure Python, Decimal arithmetic)
                                                             |
                                                             v
                                              [100% Traceable Findings]
                                                             |
                                                             v
                                                  [Dispute Letter Draft]
                                                             |
                                                             v
                                                  [Human Clerk Approval]
                                                             |
                                                             v
                                                  [Export: PDF / Markdown]
```

---

## 4. End-to-End Processing Stages

### Stage 1: Contract Ingestion & Parsing
- **Input:** Standard multi-page carrier agreement (PDF).
- **Text Layer Extraction:** Extracted page-by-page using `pypdf`, preserving a map of page numbers to text chunks (`Dict[int, str]`).
- **Scanned Image Detection:** If total extracted text across all pages is empty, the system halts immediately with HTTP 400: *"Scanned image detected. Upload a text PDF or CSV."*

### Stage 2: Structural Extraction on AMD Hardware
- Contract text is fed into **Google Gemma 2 (9B-IT)** served via an OpenAI-compatible endpoint accelerated by AMD ROCm and vLLM.
- Gemma extracts commercial terms into a strict JSON schema containing:
  - `carrier_name`, `contract_reference`, `effective_date`, `expiration_date`
  - Array of typed commercial rules (`accessorial_rule`, `fuel_surcharge`, `dim_weight_divisor`, `minimum_charge`, `duplicate_charge`, `claim_window_days`, `base_discount`)
  - Mandatory fields: `source_page` (int) and `source_quote` (verbatim string).

### Stage 3: The Quote Verification Safeguard
- An automated validator verifies each extracted `source_quote` against the contract text layer.
- Text is normalized (collapsing whitespace, stripping trailing periods).
- If the normalized quote cannot be located in the document text, the rule is marked `status = "rejected"` with `rejection_reason = "Unverifiable source quote: verbatim text not found in contract document."`
- Rejected rules are visibly flagged in the UI and excluded from audit execution.

### Stage 4: Invoice Ingestion & Normalization
- CSV invoice files are ingested and parsed into `NormalizedInvoiceLine` domain objects.
- All monetary columns (`amount_billed`, `published_rate`) and percentages (`discount_applied_percent`, `fuel_surcharge_percent`) are converted to `Decimal` using `ROUND_HALF_UP` (not banker's rounding).

### Stage 5: Deterministic Audit Execution
- Pure-Python `AuditEngine` executes active rules against normalized invoice lines:
  - Single-line evaluations: fee waivers, accessorial caps, fuel surcharge deltas, dimensional weight recalculations, minimum charge floors.
  - Multi-line evaluations: duplicate shipment billing detection, claim deadline tracking.
- Output: Array of `AuditDiscrepancy` objects with exact calculation math string proofs.

### Stage 6: Dispute Synthesis & Export
- Aggregates findings by carrier and batch into formal dispute notices.
- Generates itemized Schedule A evidence tables.
- Renders signed Markdown and publication-quality PDF documents via ReportLab.
