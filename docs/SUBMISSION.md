# CLAWBACK: FINAL DEVPOST / PORTAL SUBMISSION COPY

> [!IMPORTANT]
> This document contains the completed, audited submission text for Clawback (AMD Developer Hackathon: ACT III, Track 3: Reinvent Commerce). All bracketed placeholders have been filled directly from `benchmark/results.json` and verified against the running application.

---

## 1. Submission Overview & Form Metadata

- **Project Title**: Clawback
- **Tagline**: Find the money your carriers overcharged you, with proof.
- **Selected Challenge**: Track 3: Reinvent Commerce
- **Partner Prizes to Select**:
  - **Google**: Eligible (Serves `google/gemma-2-9b-it` on AMD ROCm).
  - **Evolus**: Do not tick (unverified usage).
- **Technology Tags**:
  `AMD ROCm`, `AMD Developer Cloud`, `AMD Token Factory`, `vLLM`, `google/gemma-2-9b-it`, `FastAPI`, `React 18`, `TypeScript`, `Python 3.14`, `SQLite`, `Docker`, `Tailwind CSS`, `ReportLab`

---

## 2. Short Description (275 characters)

Clawback is an AP copilot that reads a carrier contract with an open model on AMD, checks every extracted rule against the contract text, audits invoice lines with deterministic Decimal code, and drafts dispute letters for a human to approve. All demo data is synthetic.

---

## 3. Long Description

### The Problem
Shippers pay carrier invoices with thousands of charges, and nobody has time to check each one against the negotiated contract. Audit vendors report that freight audits recover about 3 to 7 percent of freight spend, and carriers often allow only a short dispute window, commonly around 15 days for parcel. Outsourced audit firms commonly take 20 to 50 percent of what they recover. These figures come from vendor sources and are indicative only.

### Why This is a Commerce Track Project
Most commerce tools chase top-line revenue growth. Clawback protects margin from the cost side. In commercial logistics and supply chain operations, freight spend represents 8 to 15 percent of total cost of goods sold (COGS). A dollar recovered from an overcharge drops directly to pre-tax net margin.

### What Clawback Does
1. **Contract In**: A clerk uploads a carrier contract (text PDF). An open model (`google/gemma-2-9b-it`) served on AMD infrastructure reads it and proposes rules, each with a verbatim quote and page citation.
2. **Safeguard Verification**: Clawback checks that every quote exists verbatim in the contract text layer and that extracted numbers match the quote. Unsupported rules are rejected automatically. A human explicitly reviews and approves each rule before it is activated.
3. **Deterministic Audit**: Invoice lines (CSV) are audited by a pure-Python rules engine using exact `Decimal` arithmetic. The language model never touches money.
4. **Itemized Evidence**: Each finding displays the invoice line, the contract quote and page citation, and the mathematical proof, alongside statutory claim-deadline warnings.
5. **Dispute Package Drafted**: An approval-stamped dispute letter with an itemized Schedule A evidence table is drafted for clerk review and export (PDF/Markdown). Clawback never contacts a carrier automatically.

### How AMD is Used
- **Model & Host**: The model that reads contracts and normalizes messy invoice charge descriptions is `google/gemma-2-9b-it`, hosted on AMD Developer Cloud / AMD Token Factory infrastructure (`notebooks.amd.com`).
- **Telemetry & Live Verification**: The application includes an AMD Telemetry panel displaying real-time model architecture, endpoint host, mode (`LIVE` vs. `REPLAY`), latency, tokens per second, and `last_live_call_timestamp`.
- **Live Test Button**: A *"Run Live Extraction Test"* button executes an extraction call on a sample contract clause so judges can verify connectivity, raw latency, and tokens per second firsthand.
- **Replay Mode**: When offline or if API quotas are exhausted, a deterministic replay mode serves recorded outputs from real AMD calls, visibly labeled with a persistent `REPLAY` badge.
- **Workload Concurrency**: Utilizes $k=3$ parallel self-consistency consensus extraction and batch charge-description normalization, fully utilizing AMD ROCm GPU concurrency.

### Measured Results (Synthetic Benchmark)
- **Source**: `benchmark/results.json` (Mode: `replay` / baseline; Run Date: October 16, 2026).
- **Scope**: 1,250 invoice lines across 25 batches and 3 synthetic carrier contracts (`Apex Freight Logistics`, `Beacon Express Transport`, `Crestline Cargo Partners`), with 284 planted billing errors.
- **Accuracy**:
  - Audit Recall: **100.00%** (284 of 284 planted errors detected)
  - Audit Precision: **100.00%** (0 false positives)
  - True Positives: 284 | False Positives: 0 | False Negatives: 0
  - Planted Ground Truth: **$9,130.51 USD**
  - Recovered Overcharges: **$9,130.51 USD**
  - Dollar Variance: **$0.00 (0.00%)**
- **Inference & Batch Performance**:
  - Average Batch Audit Latency: **2.16 ms** per 50-line invoice batch
  - Average Extraction Latency: **24 ms** (cached replay) / **642 ms** (single stream on AMD)
  - Audit Engine Cost: **$0.00** (pure Python Decimal logic)
- *Note*: These results prove the pipeline and deterministic arithmetic engine work as designed on synthetic benchmark data. They are not evidence of real-world carrier recovery rates.

### Limits, Stated Plainly
- **Synthetic Data**: All demo contracts and invoice records are synthetic. We have not tested real carrier contracts.
- **Scanned PDFs**: Scanned image PDFs without a text layer are rejected at upload; text PDFs and CSVs are supported.
- **Tariff Tables**: Contracts specifying discounts off external published carrier base tariffs cannot be verified without importing those external tables.
- **Human Approval**: Dispute packages are drafts for human review. Direct carrier EDI / API transmission is on the roadmap, not built.
- **Commercial Validation**: Whether shippers prefer self-serve audit software over outsourced contingency audit firms is a hypothesis we have not yet validated with live customers.

### Roadmap
1. Carrier portal upload connectors and EDI 210/214 integration.
2. External CZAR-Lite / published base tariff rate-table lookups.
3. Automated carrier dispute deadline calendar sync.
4. Pilot deployment on real carrier contracts with commercial logistics design partners.

---

## 4. Key Links
- **GitHub Repository**: `https://github.com/Abdullahs-git/clawback`
- **License**: MIT
- **Main Branch**: `main`
