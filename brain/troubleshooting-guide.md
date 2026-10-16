# Clawback Troubleshooting & Operational Runbook

This guide provides operational runbooks, common failure modes, port management, and debugging procedures for developers and evaluators.

---

## 1. Quick Diagnostic Health Checks

To verify overall system health across the backend, frontend, rules engine, and benchmarks:

```bash
# 1. Run all quality gates and tests
python scripts/verify_readme.py

# 2. Run the deployment smoke test against local backend
python scripts/smoke.py http://localhost:8000

# 3. Check copy integrity and claims grounding
python scripts/check_claims.py
```

---

## 2. Common Issues & Resolutions

### Issue 1: Port 8000 is Already in Use
- **Symptom:** Uvicorn fails to start with `[Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000): only one usage of each socket address is normally permitted`.
- **Cause:** Another background process or Docker container (e.g., an existing container or local service) is listening on port 8000.
- **Resolution:**
  1. Identify the occupying process:
     ```powershell
     Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess
     ```
  2. If it is an old Docker container, stop it:
     ```bash
     docker stop <container_name>
     ```
  3. Alternatively, launch Clawback on an alternate port:
     ```bash
     python -m uvicorn backend.app.main:app --port 8001
     ```

### Issue 2: Scanned PDF Upload Error (HTTP 400)
- **Symptom:** Contract upload returns:
  ```json
  {"detail": "Scanned image detected. Upload a text PDF or CSV."}
  ```
- **Cause:** The uploaded PDF is a rasterized scan without an embedded digital text layer.
- **Resolution:** As specified in Plan v2, Clawback avoids error-prone optical character recognition (OCR) and requires text PDFs. Re-export or download the digital contract PDF from the carrier portal or provide invoice data as CSV.

### Issue 3: Replay Mode vs Live AMD Inference
- **Symptom:** UI displays amber `REPLAY (recorded from AMD endpoint)` badge.
- **Cause:** `LLM_MODE=replay` is enabled by default to ensure deterministic offline execution without requiring GPU credentials.
- **Resolution:**
  To switch to live AMD GPU inference:
  1. Open `.env`
  2. Set `LLM_MODE=live`
  3. Provide your AMD Token Factory API key in `LLM_API_KEY=your_token`
  4. Ensure `LLM_BASE_URL=https://notebooks.amd.com/tokenfactory/v1`

### Issue 4: Resetting & Re-Seeding the Database
- **Symptom:** Need to restore demo state with fresh carrier contracts and planted invoice batches.
- **Resolution:**
  ```bash
  # Delete local SQLite database
  rm data/clawback.db

  # Re-run the idempotent seed script
  python -m backend.app.seed
  ```

---

## 3. Useful Verification Commands

| Action | Command | Expected Output |
|:---|:---|:---|
| **Rules Engine Unit Tests** | `pytest rules_engine/tests -v` | 36 passed in ~1.2s |
| **Backend Integration Tests**| `pytest backend/tests -v` | 6 passed in ~4.0s |
| **Deterministic Audit Gate** | `python benchmark/run_audit_gate.py` | 100% recall, 100% precision |
| **Extraction Replay Gate** | `python benchmark/run_extraction_replay_gate.py` | 100% quote verification rate |
| **Build Frontend** | `cd frontend && npm run build` | Zero TypeScript errors, `dist/` created |
