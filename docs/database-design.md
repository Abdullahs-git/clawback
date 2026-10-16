# Clawback Database Design & Relational Schema

Clawback utilizes SQLAlchemy 2.0 with a relational schema optimized for both single-instance SQLite deployments and enterprise PostgreSQL infrastructure.

---

## 1. Entity-Relationship Diagram

```
+-------------------+        1:N        +-----------------------+
|     contracts     |------------------<|    contract_rules     |
+-------------------+                   +-----------------------+
| id (PK, UUID)     |                   | id (PK, String)       |
| carrier_name      |                   | contract_id (FK)      |
| contract_ref      |                   | type                  |
| effective_date    |                   | parameters (JSON)     |
| expiration_date   |                   | source_page           |
| file_path         |                   | source_quote          |
+-------------------+                   | status (appr/rej)     |
                                        +-----------------------+
                                                    |
                                                    | 1:N
                                                    v
+-------------------+        1:N        +-----------------------+
|  invoice_batches  |------------------<|     invoice_lines     |
+-------------------+                   +-----------------------+
| id (PK, UUID)     |                   | id (PK, String)       |
| carrier_name      |                   | batch_id (FK)         |
| filename          |                   | invoice_number        |
| total_lines       |                   | invoice_date          |
| status            |                   | shipment_id           |
+-------------------+                   | charge_code           |
          |                             | amount_billed         |
          |                             +-----------------------+
          |                                         |
          |                                         | 1:N
          v                                         v
+-------------------+        1:N        +-----------------------+
|  dispute_letters  |------------------<|    audit_findings     |
+-------------------+                   +-----------------------+
| id (PK, UUID)     |                   | id (PK, UUID)         |
| batch_id (FK)     |                   | line_id (FK)          |
| carrier_name      |                   | rule_id (FK)          |
| total_claim_amount|                   | overcharge_amount     |
| status            |                   | expected_amount       |
| approved_by       |                   | calculation_math      |
+-------------------+                   +-----------------------+
```

---

## 2. Table Schemas & Definitions

### `contracts`
Stores ingested carrier service agreements.
- `id` (VARCHAR(36), PK): UUID primary key.
- `carrier_name` (VARCHAR(128)): Normalized carrier name (e.g. "Apex Freight Logistics").
- `contract_reference` (VARCHAR(128)): Contract reference or agreement number.
- `effective_date` / `expiration_date` (VARCHAR(32)): Term boundary dates.
- `file_path` (VARCHAR(512)): Local or volume storage location of the source PDF.
- `uploaded_at` (DATETIME): Ingestion timestamp.

### `contract_rules`
Stores commercial terms extracted by Gemma and evaluated by the Quote Verification Safeguard.
- `id` (VARCHAR(64), PK): Unique rule identifier formatted as `{contract_id_prefix}-{rule_id}` to prevent collisions across uploads.
- `contract_id` (VARCHAR(36), FK): References `contracts.id`.
- `type` (VARCHAR(64)): Rule category (`accessorial_rule`, `fuel_surcharge`, `dim_weight_divisor`, etc.).
- `description` (TEXT): Natural language explanation of the rule.
- `parameters` (JSON): Rule parameters (e.g., `{"cap": "40.00", "fee_type": "liftgate"}`).
- `source_page` (INTEGER): Contract page number where clause was located.
- `source_quote` (TEXT): Verbatim clause quote from the contract text layer.
- `confidence` (FLOAT/DECIMAL): Extraction confidence score.
- `status` (VARCHAR(32)): State (`proposed`, `approved`, `rejected`).
- `rejection_reason` (TEXT): Explanation if rejected by the quote verification safeguard.

### `invoice_batches`
Represents an ingested invoice file (e.g., weekly billing batch).
- `id` (VARCHAR(36), PK): Batch UUID.
- `carrier_name` (VARCHAR(128)): Carrier name associated with the invoice.
- `filename` (VARCHAR(256)): Source CSV or PDF filename.
- `total_lines` (INTEGER): Count of parsed line items.
- `status` (VARCHAR(32)): Ingestion status (`pending`, `audited`).

### `invoice_lines`
Normalized individual freight billing charges.
- `id` (VARCHAR(64), PK): Unique line ID formatted as `{batch_id_prefix}-{raw_line_id}`.
- `batch_id` (VARCHAR(36), FK): References `invoice_batches.id`.
- `invoice_number` (VARCHAR(64)): Carrier invoice number.
- `invoice_date` (VARCHAR(32)): Billing date (`YYYY-MM-DD`).
- `shipment_id` (VARCHAR(64)): Bill of Lading (BOL), PRO number, or tracking number.
- `charge_code` (VARCHAR(32)): Standard freight charge code (e.g. `FRT`, `LFG`, `RES`, `FSC`).
- `amount_billed` (VARCHAR(32)): Stored string representation of Decimal billed amount.
- `published_rate` / `discount_applied_percent` / `fuel_surcharge_percent` (VARCHAR/FLOAT): Supporting tariff rates.
- `dim_length_in`, `dim_width_in`, `dim_height_in`, `weight_actual_lbs`, `billed_weight_lbs` (FLOAT): Shipment metrics.

### `audit_findings`
Persisted overcharge findings computed by the deterministic rules engine.
- `id` (VARCHAR(36), PK): Finding UUID.
- `line_id` (VARCHAR(64), FK): References `invoice_lines.id`.
- `rule_id` (VARCHAR(64), FK): References `contract_rules.id`.
- `overcharge_amount` (VARCHAR(32)): Exact dollar discrepancy.
- `expected_amount` / `billed_amount` (VARCHAR(32)): Comparative monetary figures.
- `calculation_math` (TEXT): Traceable step-by-step arithmetic equation.
- `contract_page` (INTEGER): Contract citation page.
- `contract_clause_quote` (TEXT): Verbatim contractual clause.

### `dispute_letters`
Formal recovery dispute notices generated for human clerk approval.
- `id` (VARCHAR(36), PK): Dispute letter UUID.
- `batch_id` (VARCHAR(36), FK): References `invoice_batches.id`.
- `carrier_name` / `shipper_name` (VARCHAR(128)): Party names.
- `total_claim_amount` (VARCHAR(32)): Aggregated recoverable dollars.
- `status` (VARCHAR(32)): Approval lifecycle (`draft`, `approved`, `submitted`).
- `approved_by` (VARCHAR(128)): Signing clerk or manager name.
- `letter_content_md` (TEXT): Full generated Markdown notice including Schedule A.

### `amd_metric_logs`
Real-time telemetry records for AMD inference tracking.
- `id` (VARCHAR(36), PK): Log UUID.
- `operation` (VARCHAR(64)): Extraction operation name.
- `latency_ms` (FLOAT): Execution duration in milliseconds.
- `prompt_tokens` / `completion_tokens` (INTEGER): Token counts.
- `tokens_per_second` (FLOAT): Inference throughput.
- `mode` (VARCHAR(32)): `live` or `replay`.
