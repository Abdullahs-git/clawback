# Clawback Frontend Architecture

The Clawback user interface is an enterprise-grade single-page application (SPA) built with React 18, TypeScript, Tailwind CSS, and Lucide Icons. It acts as an interactive copilot for freight audit and accounts payable teams.

---

## 1. Component Hierarchy & Navigation Flow

```
                                  +-------------------+
                                  |     App.tsx       |
                                  +-------------------+
                                            |
                         +------------------+------------------+
                         |                                     |
                +-----------------+                   +-----------------+
                |   Navbar.tsx    |                   |  AmdPanel.tsx   |
                +-----------------+                   +-----------------+
                         |
      +------------------+------------------+------------------+------------------+
      |                  |                  |                  |                  |
+-------------+   +---------------+  +--------------+   +-------------+   +---------------+
|  Dashboard  |   | ContractsView |  | InvoicesView |   |  AuditView  |   |  DisputeView  |
|  View.tsx   |   |     .tsx      |  |     .tsx     |   |    .tsx     |   |     .tsx      |
+-------------+   +---------------+  +--------------+   +-------------+   +---------------+
                                                               |
                                                      +-----------------+
                                                      | FindingProof    |
                                                      | Modal.tsx       |
                                                      +-----------------+
```

---

## 2. Core Views Breakdown

### 1. Dashboard View (`DashboardView.tsx`)
- **Hero Recovery Metric**: Displays total recoverable overcharge dollars (e.g. **$9,159.31 USD**) formatted with currency locales and zero floating-point loss.
- **KPI Summary Cards**: Total lines audited, detected discrepancies count, active approved rules, and generated dispute letters.
- **Overcharge Breakdown by Category**: Visual distribution across accessorial fee caps, fuel surcharges, dimensional weight discrepancies, and duplicate charges.
- **Recent Discrepancies Table**: Immediate access to latest detected line items with drilldown links.

### 2. Contracts View (`ContractsView.tsx`)
- **PDF Upload Component**: Drag-and-drop contract ingestion with real-time text parsing.
- **Scanned Image Warning**: Displays user-friendly error banners if a scanned PDF lacking a text layer is uploaded.
- **Rule Review Cards**: Displays proposed contractual rules extracted by Gemma on AMD.
- **Verbatim Quote Badge**: Surfaces the exact contract clause quote and page citation.
- **Safeguard Enforcement**: Unsupported/unverified rules display a red rejection badge and cannot be used in audits without explicit override.
- **Approval Actions**: Individual "Approve" / "Reject" controls and a 1-click "Approve All Verified Rules" action.

### 3. Invoices View (`InvoicesView.tsx`)
- **Batch CSV Upload**: Ingestion for multi-line invoice files (50 to 1,000+ lines per batch).
- **Line Item Inspector**: Searchable and filterable table displaying shipment tracking numbers, BOLs, charge codes, billed amounts, and applied percentages.
- **Audit Trigger**: Immediate invocation of the deterministic audit engine on any uploaded batch.

### 4. Audit & Traceability View (`AuditView.tsx`)
- **Interactive Discrepancy Grid**: Filterable by carrier, rule type, and overcharge magnitude.
- **Mathematical Proof Modal (`FindingProofModal`)**:
  - Displays the billed amount vs contractual expected amount.
  - Cites the contract page number and verbatim clause quote.
  - Renders the step-by-step arithmetic equation proving the exact overcharge.

### 5. Dispute Management View (`DisputeView.tsx`)
- **Formal Notice Generator**: Consolidates approved findings into a legal notice of billing discrepancy.
- **Itemized Schedule A**: Detailed table of disputed tracking numbers, invoice dates, and amounts.
- **Human Approval Gate**: Dispute letters remain in `draft` state until explicitly approved by the clerk.
- **Export Controls**: 1-click export to **Markdown** (for email transmission) or publication-ready **PDF**.

---

## 3. The AMD Telemetry Panel (`AmdPanel.tsx`)

The top navigation header houses the dedicated AMD Hardware Telemetry panel, providing observability into model execution:
- **Model Architecture**: Pinned indicator for `google/gemma-2-9b-it`.
- **Inference Host**: Displays the connected endpoint host (e.g., `notebooks.amd.com` or local vLLM).
- **Execution Mode Badge**:
  - `LIVE`: Green pulse badge indicating live GPU inference on AMD ROCm.
  - `REPLAY`: Amber badge indicating verified AMD replay cache for deterministic demonstrations.
- **Performance Metrics**: Average latency in milliseconds, tokens per second (TPS), prompt tokens, and completion tokens.
- **Recent Call Audit Log**: Expandable history showing timestamp, operation, and duration for each extraction.

---

## 4. API Client & Error Handling (`src/api/client.ts`)

- Centralized `api` client wrapping standard `fetch` with typed TypeScript interfaces.
- Intercepts non-2xx responses and formats backend error details (e.g. 400 scanned PDF, 413 file size limit, 404 not found) into toast notifications.
- Supports configurable base URLs via `VITE_API_BASE_URL` with fallback to `http://localhost:8000`.
