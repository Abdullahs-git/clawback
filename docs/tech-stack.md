# Clawback Technology Stack & Tools Inventory

This document details all technologies, libraries, runtimes, hardware platforms, and developer tooling utilized across the Clawback engine.

---

## 1. Complete Technology Inventory

| Layer | Technology | Version | Purpose & Rationale |
|:---|:---|:---|:---|
| **Frontend Framework** | React | `18.3.1` | Declarative UI for interactive audit drilldowns and dispute review |
| **Language (Web)** | TypeScript | `^5.6.2` | Static type safety and strict schema alignment with backend API |
| **Build Tool** | Vite | `^6.2.0` | High-speed frontend bundling and hot module replacement |
| **CSS & Design** | Tailwind CSS | `^3.4.17` | Utility-first styling with dark/light theme support |
| **Icons** | Lucide React | `^1.16.0` | Accessible iconography for financial metrics and navigation |
| **Backend Framework** | FastAPI | `0.139.0` | High-performance asynchronous Python REST API framework |
| **ASGI Server** | Uvicorn | `0.51.0` | High-throughput asynchronous ASGI web server |
| **Language (Backend)**| Python | `3.14.6` (compat 3.11+) | Strict `Decimal` numeric precision and typing |
| **Database & ORM** | SQLAlchemy | `2.0.51` | Enterprise ORM with SQLite and PostgreSQL compatibility |
| **Validation** | Pydantic | `2.13.4` | Strict JSON schema parsing and request/response validation |
| **PDF Extraction** | pypdf | `6.21.0` | Fast, lightweight extraction of contract PDF text layers |
| **PDF Generation** | ReportLab | `5.0.1` | Pixel-perfect dynamic PDF dispute notice rendering |
| **Testing** | pytest | `9.1.1` | Unit, integration, and coverage test execution |
| **Property Testing** | Hypothesis | `6.170.1` | Property-based testing for mathematical order independence |
| **Coverage** | pytest-cov | `7.1.0` | Enforces 100% line & branch coverage on the rules engine |
| **AI / ML Model** | Google Gemma 2 | `9B-IT` | State-of-the-art open model for legal document extraction |
| **Inference Server** | vLLM | `OpenAI-compat` | High-throughput GPU inference with PagedAttention |
| **Hardware** | AMD ROCm | `Instinct / Cloud` | Hardware-accelerated GPU inference on AMD infrastructure |
| **Containers** | Docker | `v27+` | Multi-stage non-root container packaging |
| **Orchestration** | Docker Compose | `v2+` | Multi-service local and demo environment runner |
| **IaC** | Terraform | `>= 1.6` | Modular AWS/cloud provisioning for network and compute |

---

## 2. Directory & Package Architecture

```
clawback/
|-- apps/
|   |-- frontend/                 React 18 + TypeScript + Tailwind CSS UI
|   `-- backend/                  FastAPI REST API application
|-- rules_engine/                 Pure Python deterministic audit package (zero external deps)
|-- benchmark/                    Synthetic data generator, ground truth, and test gates
|-- infra/
|   `-- terraform/                Cloud deployment modules (network, compute, demo env)
|-- schemas/                      Canonical JSON schemas (contract_rules, invoice, finding)
|-- docs/                         Comprehensive system documentation & reports
|-- brain/                        Architectural decisions, data dictionary, & runbooks
`-- scripts/                      Verification, smoke testing, and copy validation utilities
```

---

## 3. Tool Selection Rationale

### Why React 18 & Vite?
- **Speed**: Vite bundles 1,900+ modules in under 25 seconds and enables instant hot reloading.
- **Client-Side Rendering**: Auditors require dynamic table sorting, inline rule approvals, and modal drilldowns into mathematical proofs without full page reloads.

### Why FastAPI & Python `Decimal`?
- **Zero Floating-Point Drift**: Standard IEEE 754 floating-point arithmetic introduces rounding artifacts (e.g., `0.1 + 0.2 = 0.30000000000000004`). In freight billing audits where millions of dollars are contested, `Decimal` arithmetic guarantees exact cent-level precision.
- **OpenAPI Synchronization**: FastAPI automatically generates the `openapi.yaml` contract, ensuring frontend and backend models never diverge.

### Why Google Gemma 2 (9B-IT) on AMD ROCm?
- **Reasoning Density**: Gemma 2 9B possesses exceptional legal text comprehension and structured JSON output discipline.
- **AMD Hardware Acceleration**: Served via vLLM on AMD ROCm Instinct GPUs, providing low latency and high token throughput for multi-page contract processing.
- **Certified Replay Mode**: For zero-GPU evaluation environments (like CI runners), recorded AMD model outputs provide 100% deterministic reproducibility.
