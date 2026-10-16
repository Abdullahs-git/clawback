# Clawback: Reinventing Commerce Through Freight Margin Protection

**Hackathon Track:** Track 3 (Reinvent Commerce)  
**Submission Category:** Commerce Operations, Logistics Finance & AP Copilot  
**Hardware & Platform:** AMD ROCm / AMD Developer Cloud / Google Gemma 2 9B-IT on vLLM  

---

## 1. Executive Summary & Pitch Opening

> "Most commerce tools chase top-line growth. Clawback protects margin from the cost side: it audits carrier invoices against the contract, and every dollar recovered goes straight to pre-tax profit."

For mid-market merchants, direct-to-consumer brands, and multi-channel commerce shippers, freight transportation represents one of the largest and most volatile cost centers on the income statement. 

Industry audit vendors report that about 3 to 7 percent of freight spend is recovered in overbilling, and trade publications report that up to 10 percent of freight bills contain billing discrepancies. However, small and mid-market commerce teams face a stark dilemma:
1. **Manual Spreadsheet Audits**: Accounts payable clerks manually spot-check complex 40-page contract terms against thousands of CSV line items—a tedious process that leaves substantial overbilling undiscovered.
2. **Third-Party Contingency Audit Firms**: Shippers outsource audits to third-party firms, which commonly take 20 to 50 percent of all recovered capital.

**Clawback** reinvents commerce operations by placing an enterprise-grade contract audit engine directly in the hands of the merchant's AP or logistics clerk. It acts as an intelligent, human-in-the-loop copilot: parsing contracts with Gemma on AMD infrastructure, enforcing verified contract quotes, deterministically calculating overcharges with Decimal arithmetic, and drafting carrier-ready dispute letters.

*Note: All benchmark figures and demonstrations utilize labeled synthetic demo data.*

---

## 2. Product Capabilities

### A. Contract Rule Extraction with Mandatory Quote Verification
- Shippers upload standard PDF contracts (synthetic contracts modeled on common LTL terms; real carrier contracts are untested).
- **Google Gemma 2 (9B-IT)** running on AMD ROCm extracts contractual terms: base discounts, accessorial caps (liftgate, residential, inside delivery), fuel surcharge index percentages, dimensional weight divisors, minimum charge floors, duplicate billing prohibitions, and claim windows.
- **Quote Verification Safeguard**: Every rule proposed by the LLM must contain a verbatim quote from the contract text. If a quote does not match the text layer, the rule is **automatically rejected** as unsupported. Quotes are verified, parameters are checked against them, and a human approves every rule before audit execution.

### B. Deterministic Audit Engine (Zero LLM Math)
- Invoices are ingested via CSV upload (EDI is roadmap).
- Calculations are executed by a pure-Python, zero-network engine utilizing strict `Decimal` arithmetic.
- The LLM **never** performs mathematical operations or computes money.
- Audit rules run with an average batch audit latency of **2.30 ms**.

### C. 100% Traceable Mathematical Proofs
- Every audit finding provides a drill-down proof connecting:
  1. The specific invoice line ID and billed amount.
  2. The contracted parameter (e.g., $40.00 liftgate cap).
  3. The contract page number and verbatim clause quote.
  4. The exact step-by-step arithmetic (`Billed $65.00 - Cap $40.00 = Overcharge $25.00`).

### D. Human-in-the-Loop Dispute Generation
- Overcharges are consolidated into professional dispute notices with itemized schedules.
- Clerks review, approve, and export dispute packages to Markdown or PDF.

---

## 3. Measured Benchmark Results (Source: `benchmark/results.json`)

All performance statistics are measured and reproduced via automated test gates:

| Benchmark Dimension | Measured Result | Significance |
|:---|:---|:---|
| **Audited Invoice Lines** | **1,250 lines** (25 batches) | Comprehensive multi-carrier workload |
| **Carrier Profiles** | **3 contracts** (Apex, Beacon, Crestline) | Multi-page commercial agreements |
| **Audit Recall** | **100.0%** | All 284 planted billing errors caught |
| **Audit Precision** | **100.0%** | Zero false accusations |
| **Planted Overcharge Dollars** | **$9,130.51** | Ground truth planted baseline |
| **Recovered Overcharge Dollars** | **$9,130.51** | 100% exact ground truth recovery |
| **Quote Verification Success** | **100.0%** | Unsupported rules rejected |
| **Engine Execution Speed** | **2.30 ms / batch** | Instantaneous batch processing |

---

## 4. Technical Architecture on AMD

```
Browser (React 18 + TS + Tailwind)
         |
         v
FastAPI REST API (Single Session AP Copilot)
   |                                 |
   +--> Quote Verification           +--> Deterministic Audit Engine
   |    Safeguard (Exact string)          (Pure Python, Decimal arithmetic)
   |                                 |
   v                                 v
OpenAI-Compatible vLLM Endpoint   SQLite Database (Portable)
(Google Gemma 2 on AMD ROCm)
[Recorded Replay Mode: LLM_MODE=replay]
```

Clawback is engineered for private deployment on AMD infrastructure:
- **vLLM Inference Acceleration**: Gemma 2 9B-IT served on AMD GPUs through ROCm, providing high-throughput inference for dense legal text parsing.
- **Recorded Replay Mode**: For reliable, deterministic offline reviews and demonstrations, `LLM_MODE=replay` serves recorded AMD outputs with clear UI badging.

---

## 5. Roadmap

1. **Carrier Portal & EDI Integrations**: Direct API and EDI 210/310 integration for automated submission into carrier billing dispute portals.
2. **Dynamic Published Tariff Tables**: Expansion of base linehaul discount rules against published carrier baseline rate tables.
3. **Multi-Carrier Claim Expiration Alerts**: Proactive timeline notifications alerting clerks before 15-day or contractual claim windows elapse.
