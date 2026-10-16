# Clawback Backend & Deterministic Rules Engine

The backend of Clawback is split into two distinct layers:
1. **FastAPI Application Layer**: Manages REST endpoints, database transactions, PDF uploads, and AMD inference calls.
2. **Pure Rules Engine (`rules_engine/`)**: An isolated, pure-Python domain package with zero external network or LLM dependencies that deterministically evaluates freight invoice line items using strict `Decimal` arithmetic.

---

## 1. Rules Engine Mathematical Formulas

All money math is computed using Python's `Decimal` module with `ROUND_HALF_UP` rounding to two decimal places (`TWO_PLACES = Decimal("0.01")`). Floating-point arithmetic is strictly prohibited across the package.

### Rule 1: Accessorial Fee Cap & Waiver (`accessorial_rule`)
- **Fee Waiver Evaluation:**
  If the contract clause specifies that a fee type is waived (`allowed = False`), any billed amount on that charge code represents an overcharge:
  $$\text{Expected Amount} = \$0.00$$
  $$\text{Overcharge} = \text{Amount Billed}$$
- **Fee Cap Evaluation:**
  If the rule specifies an agreed monetary cap (`cap`):
  $$\text{Expected Amount} = \min(\text{Amount Billed}, \text{Cap})$$
  $$\text{Overcharge} = \max(\$0.00, \text{Amount Billed} - \text{Cap})$$
- **Fixed Rate Evaluation:**
  If the rule specifies a contracted flat rate (`rate`):
  $$\text{Expected Amount} = \text{Contract Rate}$$
  $$\text{Overcharge} = \max(\$0.00, \text{Amount Billed} - \text{Contract Rate})$$

### Rule 2: Fuel Surcharge Index (`fuel_surcharge`)
When a contract defines a fixed fuel percentage ($P_{\text{target}}$) or a maximum allowable surcharge percentage ($P_{\text{max}}$), and the carrier bills a higher percentage ($P_{\text{billed}}$):
$$\text{Expected Amount} = \text{round}\left(\text{Amount Billed} \times \frac{P_{\text{target}}}{P_{\text{billed}}}, 2\right)$$
$$\text{Overcharge} = \text{Amount Billed} - \text{Expected Amount}$$

### Rule 3: Dimensional Weight Divisor (`dim_weight_divisor`)
Carriers charge freight based on the greater of actual scale weight ($W_{\text{actual}}$) and dimensional (volumetric) weight ($W_{\text{dim}}$). The dimensional weight formula is:
$$W_{\text{dim}} = \text{round}\left(\frac{\text{Length (in)} \times \text{Width (in)} \times \text{Height (in)}}{\text{Contract Divisor (e.g. 166)}}, 2\right)$$
$$W_{\text{billable, expected}} = \max(W_{\text{actual}}, W_{\text{dim}})$$

If the carrier bills for a higher weight ($W_{\text{billed}} > W_{\text{billable, expected}}$), the overcharge is calculated proportionally against the billed rate per pound:
$$R_{\text{per lb}} = \frac{\text{Amount Billed}}{W_{\text{billed}}}$$
$$\text{Expected Amount} = \text{round}(W_{\text{billable, expected}} \times R_{\text{per lb}}, 2)$$
$$\text{Overcharge} = \text{Amount Billed} - \text{Expected Amount}$$

### Rule 4: Minimum Charge Floor (`minimum_charge`)
If an invoice line item applies a minimum charge floor exceeding the contractual agreed minimum ($M_{\text{contract}}$):
$$\text{Expected Amount} = M_{\text{contract}}$$
$$\text{Overcharge} = \max(\$0.00, \text{Amount Billed} - M_{\text{contract}})$$

### Rule 5: Duplicate Charge Detection (`duplicate_charge`)
Identifies identical charges billed more than once for the same shipment ID. To guarantee order independence across batch uploads, lines are sorted canonically by `(invoice_date, line_id)`:
- The earliest occurrence is recognized as the legitimate original charge.
- Any subsequent line item sharing the same `(shipment_id, charge_code)` is flagged as a duplicate:
  $$\text{Expected Amount} = \$0.00$$
  $$\text{Overcharge} = \text{Amount Billed}$$

### Rule 6: Claim Window & Dispute Deadlines (`claim_window_days`)
Calculates the legal dispute expiration deadline based on the invoice date and contractual window ($D_{\text{days}}$):
$$\text{Claim Deadline} = \text{Invoice Date} + D_{\text{days}}$$
$$\text{Days Remaining} = \text{Claim Deadline} - \text{Reference Date}$$
Discrepancies approaching or exceeding the deadline are flagged with high-priority warnings in the dispute schedule.

### Rule 7: Base Freight Discount (`base_discount`)
When auditing against published standard baseline tariff rates ($R_{\text{published}}$) and contracted discount percentage ($D_{\text{contract}}$):
$$\text{Expected Amount} = \text{round}(R_{\text{published}} \times (1 - D_{\text{contract}}), 2)$$
$$\text{Overcharge} = \max(\$0.00, \text{Amount Billed} - \text{Expected Amount})$$

---

## 2. Mathematical Proof Generation

Every `AuditDiscrepancy` produced by the engine contains a fully generated `calculation_math` string detailing:
1. The contractual term cited (e.g., *"Contractual liftgate cap is $40.00"*).
2. The carrier's billed figures (e.g., *"Billed $65.00"*).
3. The exact arithmetic equation (e.g., *"$65.00 - $40.00 = $25.00"*).

This math string is rendered directly in the frontend drilldown modal and compiled into Schedule A of the dispute letter, leaving zero ambiguity during carrier billing rebuttals.
