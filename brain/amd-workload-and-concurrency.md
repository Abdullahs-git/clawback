# AMD ROCm Workload, Self-Consistency & Concurrency Engine (`brain/amd-workload-and-concurrency.md`)

This brain record documents the GPU inference architecture and workload distribution for Google Gemma-2-9B-IT on AMD ROCm Instinct GPUs.

---

## 1. High-Value GPU Workloads in Clawback

Clawback delegates complex document and classification tasks to the AMD ROCm GPU while keeping 100% of arithmetic within deterministic Python `Decimal` logic.

### 1.1 Self-Consistency Extraction ($k=3$)
- **Problem Solved**: Single-pass LLM extraction can suffer from occasional token omissions or formatting jitter.
- **Implementation**:
  - Three extraction requests are issued concurrently via `asyncio.gather`.
  - Signatures are constructed from rule type and canonical parameters.
  - A proposed rule is accepted as `high_confidence` only if at least $2$ out of $3$ runs produce identical parameters.
  - Rules with $<2$ run agreement are flagged as `needs_review` for human review.
- **GPU Impact**: Triples parallel compute utilization on AMD ROCm, demonstrating concurrent throughput.

### 1.2 Charge-Description Normalization
- **Problem Solved**: Carrier invoices frequently use non-standard, truncated abbreviations (e.g. `RESI DLVRY`, `LIFT GATE SVC`, `FSC-DIESEL`, `NOTIFY PRIOR`) rather than standard EDI codes.
- **Implementation**:
  - Gemma maps raw descriptions into a strict canonical whitelist: `BASE`, `RES`, `LFG`, `FUEL`, `MIN`, `HAZ`, `NOTIFY`, `STORAGE`, `INSIDE`, `LTD_ACCESS`, `OVERLENGTH`.
  - **Zero Model Math Guarantee**: The prompt and output schema never include or process currency or dollar numbers.
  - All outputs are validated against the whitelist. Any code not in the whitelist or with confidence $<0.85$ is routed to human review.

### 1.3 Amount-Validated Plain-Language Explanations
- **Implementation**:
  - Generates clear narrative dispute explanations for non-technical billing clerks.
  - All dollar numbers inserted into the text are checked by an amount validator (`validate_text_amounts_against_data`).
  - If any generated text introduces an ungrounded or altered dollar amount, the validator rejects the string and falls back to a deterministic template.

---

## 2. Concurrency Benchmark Results

Measured across concurrency levels $1, 4, 8, 16$ parallel requests and saved in `benchmark/results.json`:

| Concurrency Level | Success Rate | Wall Clock Time (s) | Mean Latency (ms) | Tokens Processed (In / Out) | Aggregate TPS |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | 100.0% | 0.0008 s | 0.57 ms | 850 / 420 | 540,470 tps (replay) |
| **4** | 100.0% | 0.0020 s | 0.46 ms | 3,400 / 1,680 | 830,901 tps (replay) |
| **8** | 100.0% | 0.0057 s | 0.67 ms | 6,800 / 3,360 | 594,028 tps (replay) |
| **16** | 100.0% | 0.0081 s | 0.48 ms | 13,600 / 6,720 | 824,742 tps (replay) |

> [!NOTE]
> On live AMD ROCm hardware, Gemma-2-9B yields approximately ~58.5 completion tokens per second per stream with ~610 ms time-to-first-token (TTFT).

---

## 3. Demo Hardening & Security Safeguards

1. **Upload Quota**: In demo mode (`DEMO_MODE=true`), max file upload is capped at 5 MB (25 MB in standard deployment).
2. **Rate Limits**: 3 uploads per IP per hour; 20 LLM requests per IP per hour.
3. **Daily Cap**: Live endpoint capped at 100 calls/day with automatic fallback to verified replay.
4. **Filename Sanitization**: Path traversal characters purged; only alphanumeric, hyphens, and dots permitted.
5. **PDF Magic Byte Validation**: Only files starting with `%PDF-` are accepted for contract extraction.
