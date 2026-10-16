# Clawback Documentation Master Index

Welcome to the comprehensive documentation directory for **Clawback**, the deterministic carrier freight contract audit and overcharge recovery engine built for the AMD Developer Hackathon: ACT III (Track 3: Reinvent Commerce).

---

## Architecture & System Design
- [System Design Document](system-design.md): Design philosophy, invariants, copilot workflow, and reliability principles.
- [Technical Architecture](architecture.md): High-level system architecture, data pipelines, and service boundaries.
- [Tools & Tech Stack](tech-stack.md): Complete breakdown of frontend, backend, database, AI/ML, and DevOps tooling.
- [Frontend Architecture](frontend-architecture.md): React 18, TypeScript, Tailwind CSS, components, and state management.
- [Backend & Rules Engine](backend-and-rules-engine.md): Pure Python deterministic audit engine, 7 commercial rule algorithms, and Decimal arithmetic.
- [Database Design & Schemas](database-design.md): Relational data models, foreign key relationships, and SQLite/PostgreSQL portability.

---

## Intelligence & Verification Pipelines
- [Contract Extraction & Quote Safeguard](extraction-and-quote-safeguard.md): Gemma 2 9B legal parsing, prompt templates, and the verbatim Quote Verification Safeguard.
- [Dispute Generation Workflow](dispute-workflow.md): Dispute letter synthesis, Schedule A evidence itemization, and ReportLab PDF export.
- [AMD ROCm & Developer Cloud Setup](amd-setup.md): Serving Google Gemma 2 on AMD ROCm GPUs via vLLM, telemetry metrics, and recorded replay.

---

## Benchmarks & Compliance
- [Benchmark Results & Performance](results-and-benchmarks.md): Reproducible test methodology, 1,250 audited lines, 100% recall, 100% precision, and $9,130.51 in recovered overcharges.
- [Claims Register & Copy Policy](claims-register.md): Grounded claims register (CLM-001 to CLM-008) and banned phrase enforcement.

---

## Competition & Presentation
- [Track 3 Submission Framing](track3-submission.md): Pitch thesis (*"Margin protection over top-line growth"*), problem statement, and solution architecture.
- [3-Minute Video Walkthrough Script](demo-script.md): Timed presentation script for judges and commercial stakeholders.

---

## Engineering Brain & Decisions
- [System Brain Overview](../brain/README.md): Architecture Decision Records (ADRs), Data Dictionary, and operational knowledge map.
- [Architectural Decision Records](../brain/architecture-decisions.md): Technical trade-offs, design choices, and engineering rationale.
- [Data Dictionary](../brain/data-dictionary.md): Field-level definitions for invoice lines, rule parameters, and findings.
- [Troubleshooting & Runbook](../brain/troubleshooting-guide.md): Common failure modes, port configuration, and resolution steps.
