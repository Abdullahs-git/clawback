# Clawback System Brain & Knowledge Map

This directory serves as the persistent **System Brain** for Clawback, containing architectural decision records (ADRs), domain entity data dictionaries, operational runbooks, and design rationale.

---

## Knowledge Map & Navigation

```
brain/
|-- README.md                         This knowledge base index
|-- architecture-decisions.md         Architectural Decision Records (ADR-001 to ADR-005)
|-- data-dictionary.md                Complete field-level data dictionary for freight entities
`-- troubleshooting-guide.md          Operational runbook, port resolutions, and debug steps
```

---

## Key References

- **ADR-001: Zero LLM Math**: Why we ban LLMs from calculating financial numbers and enforce strict Python `Decimal`.
- **ADR-002: Quote Safeguard**: Why verbatim substring verification is enforced over probabilistic fuzzy matching.
- **ADR-003: Certified Replay Mode**: Why certified replay fixtures are used for deterministic CI and offline reviews.
- **ADR-004: Decoupled Rules Engine**: Why the rules engine has zero dependencies on web frameworks or LLM libraries.
- **ADR-005: AP Clerk Copilot**: Why Clawback acts as a copilot for human sign-off rather than an autonomous carrier dispatch agent.
