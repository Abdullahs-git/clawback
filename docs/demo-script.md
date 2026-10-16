# Clawback: 3-Minute Video Walkthrough Script

**Presenter Role:** Product Engineer / AP Automation Specialist  
**Time Limit:** 3 minutes (180 seconds)  
**Dataset:** Synthetic Demo Data (`Apex Freight Logistics`, 25 invoice batches, 1,250 lines)  

---

## Act 1: The Freight Margin Problem (0:00 - 0:30)

*Visual: Title slide + Clawback Dashboard headline.*

> "Most commerce tools chase top-line growth. Clawback protects margin from the cost side: it audits carrier invoices against the contract, and every dollar recovered goes straight to pre-tax profit.
>
> In commerce, shipping is often a brand's second largest expense. Freight audit vendors report that about 3 to 7 percent of freight spend is lost to billing discrepancies. But auditing is either manual spreadsheet work or outsourced to third parties who take up to half the recovery. 
>
> Today, we present **Clawback**: a deterministic freight contract audit engine and AP copilot powered by Google Gemma on AMD infrastructure."

---

## Act 2: Contract Ingestion & The Quote Verification Safeguard (0:30 - 1:15)

*Visual: Navigate to Contracts View -> Upload `apex_contract.pdf` -> Rule review list opens.*

> "We begin by uploading our carrier agreement with Apex Freight.
>
> In seconds, Gemma 2 on our AMD ROCm inference endpoint extracts the contractual rules:
> - Waived residential surcharges
> - A $40.00 liftgate cap
> - An 11.5% fixed fuel surcharge
> - A 166 dimensional weight divisor
> - Duplicate charge prohibitions
>
> Crucially, Clawback enforces a **Quote Verification Safeguard**: every rule must contain a verbatim quote directly from the contract text. Notice this simulated ungrounded rule: because its quote does not match the contract text layer, Clawback automatically rejected it. Zero LLM hallucinations ever reach our audit pipeline.
>
> We approve the verified rules."

---

## Act 3: Deterministic Invoice Audit & Math Traceability (1:15 - 2:00)

*Visual: Navigate to Invoices View -> Ingest 25 invoice batches (1,250 lines) -> Click 'Run Deterministic Audit' -> Dashboard updates to $9,159.31.*

> "Next, we ingest 25 invoice batches totaling 1,250 line items.
>
> We trigger the audit. The pure-Python rules engine runs across all 1,250 lines in just **2.13 milliseconds**. 
>
> The result: **$9,159.31** in recoverable overcharges identified. 
>
> Because an LLM never touches financial calculations, every finding has mathematical proof. Let's inspect this liftgate charge:
> - Invoice line billed: $65.00
> - Contractual cap: $40.00
> - Contract Page 3, verbatim quote: *'Where requested, liftgate service charges shall not exceed forty dollars ($40.00) per occurrence.'*
> - Arithmetic: $65.00 minus $40.00 equals an exact $25.00 overcharge."

---

## Act 4: Dispute Generation & Human-in-the-Loop Export (2:00 - 2:35)

*Visual: Navigate to Dispute Letters -> Click 'Generate Dispute Notice' -> Review itemized Schedule A -> Click 'Approve & Export PDF'.*

> "With one click, Clawback consolidates findings into a formal billing dispute letter addressed to Apex Freight Logistics.
>
> The letter itemizes every shipment tracking number, BOL, contract citation, and dollar delta in Schedule A. 
>
> The AP clerk reviews the letter, approves it, and exports a signed PDF ready for transmission."

---

## Act 5: AMD Hardware Telemetry & Benchmark Gates (2:35 - 3:00)

*Visual: Open the AMD Status Panel in top navigation bar -> View benchmark/results.json.*

> "Looking at our AMD Telemetry Panel, we monitor real-time inference metrics: Google Gemma 2 9B running on AMD Developer Cloud, with certified replay mode available for offline auditing.
>
> Our automated benchmark verifies 100% recall on 287 planted billing errors with 0% dollar variance.
>
> Clawback: turning carrier contract ambiguity into verified, deterministic margin recovery on AMD. Thank you."
