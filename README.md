# Clawback

> **Deterministic Carrier Contract Audit & Overcharge Recovery Engine**  
> *Built for AMD Developer Hackathon: ACT III | Track 3: Reinvent Commerce*

[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Hardware](https://img.shields.io/badge/Hardware-AMD%20ROCm%20%2F%20Instinct-red.svg)](docs/amd-setup.md)
[![Model](https://img.shields.io/badge/Model-Google%20Gemma--2--9B--it-orange.svg)](docs/amd-setup.md)
[![Coverage](https://img.shields.io/badge/Rules%20Engine%20Coverage-100%25-brightgreen.svg)](rules_engine/tests/)
[![Data](https://img.shields.io/badge/Data%20Notice-Synthetic%20Demo%20Data-lightgrey.svg)](#synthetic-demo-data-notice)

---

## 1. The Product in One Paragraph

Shippers and manufacturers overpay freight carriers because invoices routinely contain billing errors that nobody has time to check against the contract. **Clawback** reads a carrier contract PDF, extracts its commercial terms with **Google Gemma on AMD infrastructure** into explicit, human-reviewable rules, audits every invoice line item against those rules with **deterministic Python `Decimal` code**, and proves exactly how much money was overcharged. Every discrepancy is traced to the specific invoice line, contract page, verbatim clause quote, and arithmetic calculation. Clawback drafts an itemized dispute letter per carrier with Schedule A evidence, and a human approves before anything is exported.

**Target User:** Logistics, supply chain, and finance managers at mid-size shippers and manufacturers.  
**Result Delivered:** Recoverable cash back, backed by mathematical proof and legal citations.

---

## 2. Non-Negotiable Engineering Principles

1. **The LLM Never Computes Money:**  
   Gemma reads legal PDF contracts, proposes rule schemas, and formats prose. All amounts, discounts, fee caps, fuel surcharges, and claim totals are calculated deterministically by pure Python using `Decimal`. No floating-point inaccuracies or hallucinated math.
2. **Every Finding is 100% Traceable:**  
   Every audit finding contains the exact invoice line ID, rule ID, contract page number, verbatim clause quote, expected amount, billed amount, difference, and step-by-step arithmetic proof.
3. **Quote Verification Safeguard:**  
   Every extracted rule's `source_quote` is automatically searched in the contract text. Any rule whose quote cannot be found verbatim in the document is automatically rejected as unsupported.
4. **Human in the Loop:**  
   Extracted rules require user review and approval before becoming active. Dispute letters require review and approval before export. Clawback never automatically contacts a carrier without human approval.
5. **AMD Inference Telemetry Panel:**  
   The UI includes a dedicated AMD Panel displaying model name (`google/gemma-2-9b-it`), host, latency ms, tokens/sec, and call logs.
6. **Certified Replay Mode:**  
   Supports `LLM_MODE=live|replay`. Replay mode serves cached outputs recorded from AMD endpoints, and the UI displays a clear `REPLAY (recorded from AMD endpoint)` badge.

---

## 3. Measured Benchmark Results

> [!IMPORTANT]
> All figures below were measured directly by `benchmark/run_benchmark.py` on the synthetic benchmark dataset. No figures are simulated or fabricated.

| Metric | Measured Benchmark Output | Standard Target |
| :--- | :---: | :---: |
| **Rule Extraction Precision** | **100.0%** | &gt; 90.0% |
| **Rule Extraction Recall** | **100.0%** | &gt; 90.0% |
| **F1 Score** | **100.0%** | &gt; 90.0% |
| **Quote Verification Safeguard Pass Rate** | **100.0%** | 100.0% |
| **Audit Engine Line Coverage** | **1,250 Lines Audited** | 1,000+ Lines |
| **Audit Error Detection Precision** | **100.0%** | &gt; 95.0% |
| **Total Overcharge Recovered** | **$9,159.31 USD** | Exact Cent Accuracy |
| **Batch Audit Latency** | **2.13 ms** (50 lines) | &lt; 50 ms |
| **Audit LLM Cost per Invoice** | **$0.000000** | $0 (Deterministic) |
| **Rules Engine Unit Test Coverage** | **100% Line & Branch** | 100% Required |

---

## 4. Architecture Overview

```
                          ┌─────────────────────────────┐
                          │   React + TS Web Frontend   │
                          │   (Tailwind, Lucide, Dark)  │
                          └──────────────┬──────────────┘
                                         │
                             REST API    │  AMD Telemetry
                                         ▼
                          ┌─────────────────────────────┐
                          │     FastAPI Application     │
                          │ (SQLAlchemy 2.0 / Pydantic) │
                          └──────┬───────────────┬──────┘
                                 │               │
            ┌────────────────────┘               └──────────────────┐
            ▼                                                       ▼
┌─────────────────────────┐                             ┌─────────────────────────┐
│   Pure Rules Engine     │                             │   AMD Inference Client  │
│ - Zero network imports  │                             │ - Gemma-2-9B on ROCm    │
│ - Pure Decimal math     │                             │ - Quote Verifier Guard  │
│ - 100% test coverage    │                             │ - Replay Cache System   │
└───────────┬─────────────┘                             └───────────┬─────────────┘
            │                                                       │
            └────────────────────┐               ┌──────────────────┘
                                 ▼               ▼
                          ┌─────────────────────────────┐
                          │ SQLite / Postgres Database  │
                          │ (Contracts, Invoices, Proof)│
                          └─────────────────────────────┘
```

Detailed architectural diagrams and data flows are documented in [docs/architecture.md](docs/architecture.md).  
AMD GPU serving instructions are documented in [docs/amd-setup.md](docs/amd-setup.md).

---

## 5. Quick Start (Run Locally)

### Option A: One Command with Docker Compose

Ensure Docker is running, then run:

```bash
docker compose up --build
```

- **Web Dashboard:** Open `http://localhost:3000`
- **Backend API & Swagger Docs:** Open `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`

---

### Option B: Local Development Setup

#### 1. Backend & Database
```bash
# Clone the repository
git clone https://github.com/Abdullahs-git/clawback.git
cd clawback

# Create environment configuration
cp .env.example .env

# Install Python requirements
pip install -r backend/requirements.txt
pip install reportlab pypdf pytest pytest-cov python-multipart

# Seed demo dataset (contracts, invoices, verified rules)
$env:PYTHONPATH=".;rules_engine" # Windows PowerShell
# or export PYTHONPATH=".:rules_engine" for Linux/macOS
python -m backend.app.seed

# Start the API server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 6. Running Tests & Benchmarks

```bash
# Run rules engine unit tests with 100% money coverage check
$env:PYTHONPATH=".;rules_engine"
pytest rules_engine/tests --cov=rules_engine/rules_engine --cov-report=term-missing

# Run backend API integration tests
pytest backend/tests -v

# Run the full automated benchmark suite
python benchmark/run_benchmark.py
```

---

## 7. Synthetic Demo Data Notice

All carrier names (e.g., *Apex Freight Logistics*, *Beacon Express Transport*, *Crestline Cargo Partners*), tracking numbers, addresses, and invoice records used in this repository and demo are **synthetic demo data** generated by `benchmark/generator.py`. They do not represent real companies or proprietary rate sheets.

---

## 8. Honest Limitations & Roadmap

### What is Built & Verified in P0
- [x] Multi-page PDF carrier contract text extraction
- [x] Gemma structured JSON rule extraction on AMD architecture
- [x] Quote Verification Safeguard (auto-rejects unverified clauses)
- [x] Human-in-the-loop rule approval workflow (individual and batch)
- [x] Normalized invoice CSV and PDF ingestion
- [x] Deterministic audit engine for 7 core rule types (`base_discount`, `accessorial_rule`, `fuel_surcharge`, `dim_weight_divisor`, `minimum_charge`, `duplicate_charge`, `claim_window_days`)
- [x] 100% unit-test coverage for money logic using Python `Decimal`
- [x] Full traceability finding drilldown with step-by-step arithmetic proof
- [x] Formal carrier dispute letter generator with Schedule A evidence table
- [x] PDF and Markdown dispute letter export
- [x] AMD telemetry panel with latency, tokens/sec, and replay status
- [x] Automated benchmark runner writing verified results to `results.json`
- [x] Docker Compose with multi-stage non-root containers and healthchecks

### What is Roadmap (Out of Scope for Hackathon)
- Scanned OCR image fallback with Tesseract (P1)
- Multi-tenant enterprise authentication and RBAC (P2)
- Direct EDI (EDI 210/EDI 214) transport intake (P2)
- Real-time ERP accounting writeback (SAP / NetSuite) (P2)

---

## 9. License

This project is licensed under the [MIT License](LICENSE).
