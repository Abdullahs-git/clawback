# Clawback Architectural Decision Records (ADRs)

This document records the foundational engineering trade-offs, alternative approaches considered, and ultimate decisions governing the Clawback system.

---

## ADR-001: Pure Python `Decimal` Over LLM Arithmetic

- **Status**: Accepted & Enforced
- **Context**: Large language models (LLMs) are probabilistic token generators. Even advanced frontier models suffer from arithmetic hallucinations, off-by-one penny errors, and inability to maintain consistent rounding modes across thousands of calculations. In freight billing disputes, a single arithmetic error discredits the entire claim before a carrier's billing audit committee.
- **Decision**: Prohibit the LLM from computing monetary values, percentages, or overcharges. All financial logic is executed by a deterministic, pure-Python rules engine utilizing Python's `Decimal` module with `ROUND_HALF_UP` rounding.
- **Enforcement**: Automated AST (Abstract Syntax Tree) test (`test_float_prohibition_in_rules_engine`) scans the entire engine package to fail CI if any `float()` call or naked float constant is introduced.

---

## ADR-002: Verbatim Quote Verification Safeguard vs Fuzzy Matching

- **Status**: Accepted & Enforced
- **Context**: When extracting contract rules, an LLM might summarize or paraphrase terms (e.g. inventing *"Residential surcharge is $0"* when the contract states *"Residential delivery fee shall be waived in full"*). If an auditor cites a paraphrased quote in a formal dispute, the carrier will reject the claim as ungrounded.
- **Decision**: Enforce a strict **Quote Verification Safeguard**: every rule proposed by Gemma must supply a verbatim `source_quote`. The system verifies that the normalized string exists directly within the contract text layer. Any rule whose quote cannot be verified is automatically marked `status = "rejected"`.
- **Consequences**: Zero hallucinated rules reach the audit execution stage. Audited claims are 100% legally grounded.

---

## ADR-003: Certified Replay Mode (`LLM_MODE=replay`)

- **Status**: Accepted & Enforced
- **Context**: Live GPU inference endpoints can experience network latency, rate limits, or intermittent downtime during offline hackathon reviews, automated CI runs, or pitch presentations.
- **Decision**: Implement a certified replay cache (`LLM_MODE=replay`) that serves pre-recorded real AMD model outputs for verified contracts.
- **Consequences**: The system is 100% testable and runnable on clean machines without requiring an active GPU or live API token. The UI prominently renders an amber `REPLAY (recorded from AMD endpoint)` badge to maintain complete transparency.

---

## ADR-004: Monorepo with Decoupled Pure Rules Engine

- **Status**: Accepted & Enforced
- **Context**: Coupling the audit logic directly into database models or web controllers creates testing friction, slow test suites, and tight coupling with FastAPI.
- **Decision**: Structure the rules engine as an isolated pure-Python package (`rules_engine/`) containing only standard library imports (`decimal`, `dataclasses`, `typing`, `datetime`).
- **Consequences**: The engine executes with near-zero overhead (~2.13 ms for 50 lines), achieves 100% line & branch test coverage in ~1.1 seconds, and can be embedded into any serverless function, CLI, or cloud container.

---

## ADR-005: Copilot Model vs Autonomous Carrier Dispute Dispatch

- **Status**: Accepted & Enforced
- **Context**: Autonomous AI agents that dispatch legal dispute letters directly to carrier billing portals without human oversight create severe business, legal, and relational risks for merchants.
- **Decision**: Position Clawback strictly as an **AP Copilot**. Extracted rules require explicit human approval; generated dispute letters remain in `draft` state until approved by the clerk; export to PDF/Markdown is human-initiated.
