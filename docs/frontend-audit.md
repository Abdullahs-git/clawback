# Frontend Fake Data Audit (`docs/frontend-audit.md`)

This audit documents every hardcoded fallback, literal array, and placeholder identified across `frontend/src/` per Fix Plan B.1.

---

## 1. Identified Hardcoded Values & Placeholders

| File | Line | Identified Hardcoded Item | Status / Remediation |
|---|---|---|---|
| `frontend/src/components/DashboardView.tsx` | 31 | `overview?.total_overcharge \|\| '9159.31'` | **Purged**. Replaced with real API value or designed empty state `$0.00`. |
| `frontend/src/components/DashboardView.tsx` | 32 | `overview?.total_findings_count \|\| 287` | **Purged**. Replaced with real API finding count `0`. |
| `frontend/src/components/DashboardView.tsx` | 33–39 | `byCategory = overview?.by_category \|\| { base_discount: '3420.50', ... }` | **Purged**. Literal category dictionary removed; renders empty state if null. |
| `frontend/src/components/DashboardView.tsx` | 40–44 | `byCarrier = overview?.by_carrier \|\| { 'Apex Freight Logistics': '4820.50', ... }` | **Purged**. Literal carrier dictionary removed; renders empty state if null. |
| `frontend/src/components/AmdPanel.tsx` | 98 | `metrics?.average_latency_ms \|\| 642.5` | **Purged**. Replaced with exact API latency or `'-'`. |
| `frontend/src/components/AmdPanel.tsx` | 113 | `metrics?.average_tokens_per_second \|\| 58.5` | **Purged**. Replaced with exact API throughput or `'-'`. |
| `frontend/src/components/AmdPanel.tsx` | 137 | `metrics?.total_calls \|\| 3` | **Purged**. Replaced with exact API count or `0`. |
| `frontend/src/components/AuditView.tsx` | 325 | `selectedFinding.days_remaining_to_claim ?? 180` | **Purged**. Removed arbitrary `180` fallback; displays actual calculated deadline or "Standard term". |
| `frontend/src/components/AuditView.tsx` | 252 | Blocking modal backdrop | **Refactored**. Converted from blocking modal to a non-blocking 3-column side panel with claim deadline and contract quote grounding. |

---

## 2. Forbidden Content & Mock Verification

- **Production Bundle Isolation**: `msw` and test fixtures are not imported anywhere in `frontend/src/`.
- **Banned Marketing Claims**: Grep verification confirmed zero occurrences of:
  - Lorem ipsum
  - "Acme"
  - "John Doe"
  - Fake customer logos or "trusted by"
  - Invented user counts or fake pricing tiers
  - Stock "99.9% uptime" claims
- **Component Currency Literal Check**: Script `scripts/check_frontend_integrity.py` validates that no static currency literals exist inside component markup.
