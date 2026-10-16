# Clawback Domain Data Dictionary

This document defines the canonical domain models, charge codes, and data schemas across the Clawback platform.

---

## 1. Freight Charge Code Taxonomy

Standard industry charge codes recognized and normalized by Clawback:

| Code | Standard Description | Rule Applied | Overcharge Metric |
|:---|:---|:---|:---|
| **`FRT`** | Base Linehaul Freight | `base_discount`, `dim_weight_divisor`, `minimum_charge`, `duplicate_charge` | Delta between billed linehaul and discounted/dimensional/minimum rate |
| **`LFG`** | Liftgate Service | `accessorial_rule` | Amount billed exceeding contractual cap (e.g. $40.00) |
| **`RES`** | Residential Delivery Surcharge | `accessorial_rule` | Entire fee if waived per contract ($0.00 expected) |
| **`INS`** | Inside Delivery Service | `accessorial_rule` | Amount billed exceeding contractual cap |
| **`FSC`** / **`FUEL`** | Fuel Surcharge Index | `fuel_surcharge` | Delta between billed percentage and contractual fixed/max percentage |
| **`ADDRC`** | Address Correction Fee | `accessorial_rule` | Billed fee exceeding contracted rate |
| **`HAZ`** | Hazardous Materials Surcharge | `accessorial_rule` | Billed fee exceeding contracted rate |

---

## 2. Ingestion Domain Entities

### `NormalizedInvoiceLine`
The canonical in-memory representation of an invoice charge line item fed into the rules engine:
- `line_id`: Unique identifier across the batch (string).
- `invoice_number`: Carrier invoice reference string.
- `invoice_date`: Date string formatted as `YYYY-MM-DD`.
- `shipment_id`: Bill of Lading (BOL), PRO, or tracking number.
- `charge_code`: Uppercase charge identifier (e.g., `FRT`, `LFG`, `RES`, `FSC`).
- `amount_billed`: Exact billed monetary amount (`Decimal`).
- `charge_description`: Natural language description from carrier bill (optional).
- `service_level`: Service type (e.g., `Standard Ground`, `Next Day Air`, `LTL Freight`).
- `published_rate`: Carrier standard baseline rate before discount (`Decimal`, optional).
- `discount_applied_percent`: Discount percentage shown on invoice (`Decimal`, optional).
- `fuel_surcharge_percent`: Fuel surcharge percentage applied (`Decimal`, optional).
- `weight_actual_lbs`: Scale weight in pounds (`Decimal`, optional).
- `dim_length_in`, `dim_width_in`, `dim_height_in`: Package dimensions in inches (`Decimal`, optional).
- `billed_weight_lbs`: Weight billed by carrier (`Decimal`, optional).

---

## 3. Contractual Domain Entities

### `RuleDefinition`
A validated contractual commercial term:
- `id`: Unique rule identifier (string).
- `type`: Rule category (`accessorial_rule`, `fuel_surcharge`, `dim_weight_divisor`, `minimum_charge`, `duplicate_charge`, `claim_window_days`, `base_discount`).
- `description`: Plain-language explanation.
- `parameters`: Typed dictionary containing rule thresholds:
  - `accessorial_rule`: `{"fee_type": str, "cap": Decimal, "rate": Decimal, "allowed": bool}`
  - `fuel_surcharge`: `{"fixed_percentage": Decimal, "max_percentage": Decimal}`
  - `dim_weight_divisor`: `{"divisor": int}`
  - `minimum_charge`: `{"amount": Decimal, "service_level": str}`
  - `duplicate_charge`: `{"enabled": bool}`
  - `claim_window_days`: `{"days": int}`
- `source_page`: 1-based page index where clause was located (int).
- `source_quote`: Verbatim contractual clause from contract text layer (string).
- `status`: Rule state (`proposed`, `approved`, `rejected`).
- `confidence`: Extraction model confidence score (`Decimal`).

---

## 4. Audit Output Entities

### `AuditDiscrepancy`
An itemized overcharge finding backed by mathematical and legal proof:
- `line_id`: Target invoice line identifier.
- `shipment_id`: Bill of Lading (BOL) or tracking number.
- `invoice_number`: Carrier invoice reference.
- `invoice_date`: Date of invoice.
- `charge_code`: Specific disputed charge code.
- `rule_id`: Contract rule applied.
- `rule_type`: Rule category.
- `contract_page`: Exact page number citation in carrier contract.
- `contract_clause_quote`: Verbatim contractual clause.
- `expected_amount`: Contractually mandated amount (`Decimal`).
- `billed_amount`: Carrier's billed amount (`Decimal`).
- `overcharge_amount`: Net overcharge dollar delta (`Decimal`).
- `calculation_math`: Traceable, step-by-step arithmetic proof string.
- `claim_deadline_date`: Legal expiration deadline for filing dispute.
- `days_remaining_to_claim`: Integer days remaining before dispute window closes.
