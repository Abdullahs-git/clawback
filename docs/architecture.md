# Clawback Architecture & System Design

```
+-----------------------------------------------------------------------------------+
|                                  CLAWBACK UI                                      |
|            (React 18 + TypeScript + Vite + Tailwind CSS + Lucide Icons)           |
+-----------------------------------------------------------------------------------+
        |                                                              |
        | REST API Calls                                               | Telemetry
        v                                                              v
+----------------------------------------------------+   +--------------------------+
|                 FastAPI Application                |   |        AMD Panel         |
|  - Contracts Router       - Invoices Router        |   | - Latency ms / TPS       |
|  - Audit Router           - Disputes Router        |   | - Host: notebooks.amd.com|
|  - Security & CORS        - AmdStatus Router       |   | - Pinned: Gemma-2-9B     |
+----------------------------------------------------+   +--------------------------+
        |                                                              |
        +----------------------------+                                 |
        |                            |                                 |
        v                            v                                 v
+-------------------+      +---------------------+         +------------------------+
|   Rules Engine    |      | Extraction Pipeline |         |      LLM Client        |
|  (Pure Python 3)  |      |   - PDF Text Layer  |         | - Live: AMD ROCm vLLM  |
| - 100% Decimal    |      |   - Quote Verifier  |         | - Replay: AMD Fixtures |
| - 0 LLM/Network   |      |     Safeguard       |         | - Automatic Backoff    |
+-------------------+      +---------------------+         +------------------------+
        |                            |                                 |
        v                            v                                 v
+-----------------------------------------------------------------------------------+
|                        SQLite / PostgreSQL Database Volume                        |
|  Contracts  |  ContractRules  |  InvoiceBatches  |  InvoiceLines  |  AuditFindings |
+-----------------------------------------------------------------------------------+
```

---

## 1. Non-Negotiable Core Principles

1. **The LLM Never Computes Money:**
   Google Gemma on AMD reads legal PDFs, extracts rule schemas, and writes human prose. Deterministic Python using `Decimal` evaluates every freight amount, comparison, and claim total. Zero floating-point drift.
2. **Every Finding is 100% Traceable:**
   Every overcharge finding includes:
   - Specific Invoice Line ID & Shipment Tracking #
   - Contract Clause Quote (verbatim text from contract)
   - Contract Page Citation
   - Contract Expected Amount vs Billed Amount
   - Step-by-Step Arithmetic Proof
3. **Quote Verification Safeguard:**
   Every extracted rule's `source_quote` is tested against the contract text. Any rule whose quote cannot be found verbatim in the document is automatically rejected as unsupported.
4. **Human in the Loop:**
   - Extracted rules require explicit human approval before becoming active for audits.
   - Generated dispute letters require approval before formal export.
   - Clawback never automatically contacts a carrier without human sign-off.
5. **Certified Replay Mode:**
   When running offline or during network disruptions, Clawback serves pre-recorded real AMD model responses labeled with the badge: `REPLAY (recorded from AMD endpoint)`.
