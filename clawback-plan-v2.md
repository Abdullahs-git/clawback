# CLAWBACK: MASTER PLAN v2 (replaces clawback-agent-prompt.md where they conflict)

Audience: the build agent(s) and the 2 to 3 humans. Read all of it before writing code.

Status of this plan: written Saturday 17 Oct 2026, about 02:00 PKT. Deadline: **Sunday 18 Oct, 15:00 PKT** (the event page header says 20:00; the schedule says 15:00; plan for 15:00). Feature freeze: **Sunday 12:00 PKT**.

---

## 1. Issues found and how this plan resolves them

| # | Issue | Source | Resolution in v2 |
|---|-------|--------|------------------|
| 1 | Contracts give a discount off published tariff tables; checking a discount needs the tariff | External review | MVP P0 rules are only: accessorial caps, fuel surcharge %, dimensional-weight divisor, duplicates, claim window. `base_discount` moves to P1 and works only against a **synthetic tariff CSV** we generate. |
| 2 | Carriers may require portal or EDI disputes, not emailed letters (unverified claim) | External review | The letter is the MVP output. Portal and EDI submission are roadmap. Clawback is positioned as a **copilot for the AP or logistics clerk**, never as autonomous dispute resolution. |
| 3 | "On-prem" is wrong; we run on AMD cloud | Our check | Say "private deployment on AMD infrastructure". Never say on-prem. |
| 4 | Evolus needs an event code we do not have; integration is expensive | Our check | **Off by default.** Revive only if a working workspace exists by Sat 12:00 PKT. Otherwise remove every Evolus mention from the submission. |
| 5 | OCR and scanned pages cost hours | Review | **Dropped.** Scanned file shows a clear error: "Scanned image detected. Upload a text PDF or CSV." |
| 6 | Multi-user auth costs hours | Review | **Dropped.** One demo session, no login. |
| 7 | Invented demo figures in reviews ($14,280 etc.) | Our check | Every number on screen or in the pitch comes from generated data plus `benchmark/results.json`. Enforced by a test (section 6.9). |
| 8 | Overclaims: "catches every penny", "saves 80% time", "40% cut", "15-20% of GMV" | Our check | Claims register (section 11). Anything not measured or sourced is banned from copy. |
| 9 | Track 3 is a stretch (customer and retail focus) | Our check | Submission opens with the margin argument: a recovered dollar goes straight to pre-tax profit. See section 10. |
| 10 | "Why not outsource to a contingency audit firm?" | Review | Positioning: audit firms often take 20 to 50 percent of recoveries (vendor-sourced, indicative); a flat-fee tool in the clerk's hands keeps that money. Labeled as a hypothesis, not validated. |
| 11 | AMD endpoint not confirmed; nothing works without it | Our check | Phase 0 gate with a decision rule (section 8). |
| 12 | Live demo can fail on network or GPU | Review | Replay mode, always labeled. Deterministic audit path needs no GPU. |
| 13 | Deadline conflict (15:00 vs 20:00) | Event page | Plan for 15:00. Ask on Discord which is binding. |
| 14 | Terraform and CI/CD add risk in a 35-hour window | Our check | Timeboxed (section 7.4). Demo URL must not depend on Terraform; fallback host is allowed. |
| 15 | Humans need sleep; a no-sleep plan produces bugs | Our check | Schedule includes sleep blocks (section 8). |
| 16 | Unverified technical details (action versions, AMD serving flags, provider specifics) | Our check | Agent must verify against current docs and pin versions. Do not write flags from memory. |

---

## 2. Product (unchanged core, tighter scope)

Clawback reads a carrier contract (text PDF), proposes rules with verified contract quotes, lets a human approve them, audits invoice lines with deterministic Decimal code, shows traceable findings with the total recoverable, and drafts dispute letters for human approval. Gemma runs on AMD through an OpenAI-compatible vLLM endpoint.

**P0 rule types:** `accessorial_rule` (allowed, rate, cap), `fuel_surcharge` (percent or band table), `dim_weight_divisor`, `duplicate_charge`, `claim_window_days`, `minimum_charge`.
**P1:** `base_discount` against a synthetic tariff CSV; claim-deadline tracker; Evolus (only if unlocked).
**Cut:** OCR, auth, email intake, EDI, ERP, multi-tenant.

Principles (unchanged): the model never computes money; every finding is traceable to invoice line, rule, contract page and quote; humans approve rules and letters; synthetic data labeled as such; no secrets in git or logs.

---

## 3. Architecture

```
Browser (React+TS) -> FastAPI -> [LLM client] -> vLLM on AMD (Gemma)
                          |            ^
                          |            +-- LLM_MODE=replay -> recorded AMD outputs (labeled)
                          +-> Rules engine (pure Python, Decimal)  <- approved rules + invoice lines
                          +-> SQLite (Postgres-portable)
```

Repo layout (monorepo):

```
/apps/web            React, TypeScript, Tailwind, Jest, Cypress
/apps/api            FastAPI, pytest
/packages/engine     pure-Python rules engine (no network, no LLM imports)
/benchmark           generator, ground truth, runner, results.json
/infra/terraform     modules: network, compute; envs: demo
/.github/workflows   ci.yml, e2e.yml, security.yml, terraform.yml, deploy.yml, live-smoke.yml
/docs                architecture, amd-setup.md, claims-register.md, runbook.md
/scripts             verify_readme.sh, record_replay.py, smoke.sh
docker-compose.yml, .env.example, LICENSE (MIT), README.md
```

Interface contracts (OpenAPI + JSON schemas) are written in Phase 0 before parallel work starts. The OpenAPI spec is the source of truth; the frontend client is generated from it, and CI fails if the generated client is stale.

---

## 4. Test strategy (what exists, who owns it, what gate it enforces)

Pyramid: many fast unit tests, fewer API and component tests, a small number of end-to-end flows. Nothing in CI calls the live AMD endpoint; CI uses a mock LLM server that returns fixture responses.

### 4.1 Engine unit tests (pytest + Hypothesis), gate: 100% line and branch coverage

Per rule type, minimum cases:
- **Accessorial cap:** charge below cap (no finding); equal to cap (no finding); one cent above (finding of exactly 0.01); disallowed fee type (finding equals full fee); fee type absent from rules (no finding, flagged "no rule"); multiple fees on one shipment.
- **Fuel surcharge:** percent exact; rounding at half-cent (use the rounding mode stated in the contract rule, default ROUND_HALF_UP, tested explicitly); band table edges (value on a band boundary); billed higher and lower than contracted (lower produces no finding unless configured).
- **DIM divisor:** billable weight chosen as max(actual, dim); wrong divisor produces correct delta; unit conversion (lb/kg, in/cm) tested both ways; zero or missing dimensions yields "insufficient data", never a guess.
- **Duplicates:** same shipment id and charge code twice; same code different shipments (no finding); duplicate across batches; three copies (two findings).
- **Claim window:** day 14, 15, 16 around a 15-day window; invoice date vs today (clock injected, never `datetime.now()` inside the engine); timezone boundary.
- **Minimum charge:** below minimum billed at minimum (no finding); billed below minimum (no finding, or info); billed above with no basis (finding).
- **Money handling:** no `float` anywhere (a test greps the package for float literals and `float(`); currency mismatch raises; negative amounts (credits) handled; zero quantity; very large totals; decimal places preserved.
- **Property tests (Hypothesis):** total of findings equals sum of line deltas; result independent of line order; running twice gives identical output (idempotent); adding a compliant line never changes existing findings; a line with no applicable rule never produces a finding.
- **Determinism test:** run the same input 100 times, hash the output, assert one hash.

### 4.2 Extraction and LLM-layer tests (pytest, mock LLM server), gate: all pass

- Schema validation of model output (Pydantic): valid, missing field, wrong type, extra field, empty array.
- Invalid JSON triggers exactly one repair pass, then a visible failure (never a silent guess).
- **Quote verification:** exact match accepted; extra whitespace and line-break differences normalized and accepted; hyphenation across line breaks handled; changed word rejected; quote from a different page rejected; empty quote rejected; very short quote (under a minimum length) rejected; case difference decision documented and tested.
- Rule with unverifiable quote is auto-rejected and shown as "unsupported".
- Conflicting rules (two caps for one fee) are flagged for review, not merged.
- Confidence below threshold goes to review.
- Client behavior: timeout, retry with backoff (jittered, capped), 429 and 5xx handling, token and latency logging, no secrets in logs, prompt-injection fixture (a contract containing "ignore previous instructions") does not change the schema or approval status.
- **Replay mode:** returns recorded output for a known input; unknown input fails loudly; the response is tagged `replay`; the UI badge test relies on that tag.
- Letter generation: every amount in the letter equals the engine's amount (numbers are inserted from data; a validator extracts currency strings from the final text and compares them to the computed set).

### 4.3 Backend API tests (pytest + httpx), gate: at least 85% coverage

- Each endpoint: success, validation error, not found, wrong method.
- Uploads: wrong type, empty file, oversize, double extension, path traversal filename, corrupt PDF, scanned-image PDF (expects the specific error message), CSV with missing columns, CSV with BOM, very long lines.
- Background jobs: states queued, running, done, failed; failure surfaces a readable error.
- Rate limit on LLM-backed routes; CORS allowlist; security headers present; no stack traces in error bodies.
- Status transitions: rules cannot be used in an audit until approved; rejected rules never affect findings.
- OpenAPI schema validity and drift check against the generated frontend client.
- Database: migrations apply on empty DB; seed script idempotent.

### 4.4 Frontend unit and component tests (Jest + React Testing Library + MSW), gate: at least 80% coverage

- Currency and number formatting: locale, negatives, rounding display, tabular alignment class.
- Dashboard: headline total equals the sum of the findings returned by the API; empty, loading and error states.
- Findings table: sort, filter, pagination, drill-down opens the trace panel with invoice line, rule, quote and math.
- Rule review: approve, reject, edit; unsupported rules show their badge and cannot be approved without an explicit override (or cannot at all; pick one and test it).
- Upload components: type and size validation, progress, error messages, scanned-PDF message.
- AMD panel: shows model name, latency, tokens per second; "LIVE" vs "REPLAY" badge from the response tag; no key ever rendered.
- API client: retries, timeout, error mapping (MSW).
- Accessibility smoke in component tests (`jest-axe`).

### 4.5 End-to-end tests (Cypress, against the running docker compose stack with the mock LLM), gate: all pass

1. **Happy path:** upload contract, see proposed rules with quotes, approve, upload invoices, see dashboard total, open a finding and its trace, edit and approve a letter, export it.
2. **Ungrounded rule:** fixture returns a rule with a fake quote; it appears rejected and does not affect findings.
3. **Reject a rule:** findings tied to it disappear after re-audit.
4. **Edit a rule parameter:** the finding amounts change accordingly.
5. **Bad uploads:** wrong type, oversize, scanned PDF, malformed CSV, each with the exact expected message.
6. **LLM down:** error state with retry; with replay enabled, the badge reads REPLAY and the flow still completes.
7. **Duplicate upload:** the same invoice batch twice flags duplicates without double counting.
8. **Claim-window warning** appears for lines past the window.
9. **Accessibility:** `cypress-axe` on every page, no serious or critical violations.
10. **Keyboard-only run** of the happy path; focus order and visible focus.
11. **Responsive:** 375, 768 and 1440 px; dark and light mode.
12. **Number integrity:** a custom command reads every currency string on the dashboard and letter and asserts it appears in the API's computed values.

### 4.6 Benchmark gates (run in CI without a GPU)

- **Deterministic audit gate:** feed the engine the ground-truth rules and the generated invoices; recall of planted errors must be 100 percent and precision at least 99 percent. This tests the engine and the generator together.
- **Extraction gate (replay):** recorded model outputs vs ground-truth rules must meet the thresholds written in `benchmark/thresholds.json`. Thresholds are set after the first real run and never loosened silently.
- The **live** benchmark (real AMD calls) runs manually and writes `benchmark/results.json`.

### 4.7 Infrastructure tests (Terraform)

- `terraform fmt -check`, `terraform validate`, `tflint`.
- Policy and security scan: `checkov` (or `tfsec`); no open SSH to the world, no public database ports, encrypted volumes where the provider supports it.
- Native `terraform test` (Terraform 1.6+) with mocked provider for: required variables present, firewall exposes only 80 and 443 (and SSH from a variable allowlist), outputs include the public IP, tags applied.
- Plan on pull requests when credentials exist; apply only by manual dispatch with an environment protection rule.
- Cloud-init and Compose validation: `docker compose config`, `shellcheck` on scripts.

### 4.8 Container, security and supply-chain checks

- `hadolint` on Dockerfiles; `trivy` on images and filesystem; images run as non-root; no secrets in layers.
- `gitleaks` on the full git history; `pip-audit`, `npm audit` (fail on high); `bandit` on Python; license check (MIT-compatible dependencies).
- Optional if time allows: OWASP ZAP baseline scan against the compose stack.

### 4.9 Copy and claims tests

- `scripts/check_claims.py` scans README, slides source and the submission text for numbers; every number must appear in `benchmark/results.json`, the generated data summary, or `docs/claims-register.md` with a source. CI fails otherwise.
- A banned-phrase check: "on-prem", "every penny", "100% accurate", "certified", "guaranteed".

### 4.10 Performance and resilience

- Backend smoke load (k6 or locust): 20 virtual users on dashboard and findings endpoints; p95 under 500 ms on the seeded dataset (agree the number after a baseline run).
- AMD concurrency test: 1, 4, 8, 16 parallel extraction calls; record latency and tokens per second for the benchmark report.
- Chaos checks: kill the LLM endpoint mid-job (job fails cleanly); restart the API (state survives in SQLite volume).

### 4.11 README test

`scripts/verify_readme.sh` follows the README commands literally on a clean CI runner: clone, copy `.env.example`, `docker compose up`, wait for health, run the smoke script. If it fails, the README is wrong.

---

## 5. CI/CD pipelines

Pin every action to a major version or commit SHA and verify current versions before writing; the YAML below is a skeleton, not final.

### 5.1 `ci.yml` (every push and pull request)

```yaml
name: ci
on:
  push:
  pull_request:
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
jobs:
  engine:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: pip }
      - run: pip install -e packages/engine[test]
      - run: ruff check packages/engine && ruff format --check packages/engine
      - run: mypy packages/engine
      - run: pytest packages/engine --cov=clawback_engine --cov-branch --cov-fail-under=100
  api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: pip }
      - run: pip install -e packages/engine -e apps/api[test]
      - run: ruff check apps/api && ruff format --check apps/api && mypy apps/api
      - run: pytest apps/api --cov=app --cov-fail-under=85
      - run: python scripts/check_openapi_drift.py
  web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm, cache-dependency-path: apps/web/package-lock.json }
      - run: npm ci
        working-directory: apps/web
      - run: npm run lint && npm run typecheck
        working-directory: apps/web
      - run: npm test -- --coverage --coverageThreshold='{"global":{"lines":80}}'
        working-directory: apps/web
      - run: npm run build
        working-directory: apps/web
  benchmark-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: pip }
      - run: pip install -e packages/engine -e benchmark
      - run: python benchmark/generate.py --seed 42
      - run: python benchmark/run_audit_gate.py   # deterministic, no GPU
      - run: python benchmark/run_extraction_replay_gate.py
      - run: python scripts/check_claims.py
```

### 5.2 `e2e.yml` (pull requests to main, and on main)

```yaml
name: e2e
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
jobs:
  cypress:
    runs-on: ubuntu-latest
    timeout-minutes: 25
    steps:
      - uses: actions/checkout@v4
      - run: cp .env.example .env && echo "LLM_MODE=mock" >> .env
      - run: docker compose -f docker-compose.yml -f docker-compose.ci.yml up -d --build --wait
      - uses: cypress-io/github-action@v6
        with:
          working-directory: apps/web
          wait-on: "http://localhost:3000"
          wait-on-timeout: 120
          browser: chrome
      - if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: cypress-artifacts
          path: |
            apps/web/cypress/screenshots
            apps/web/cypress/videos
      - if: always()
        run: docker compose logs --no-color > compose.log || true
      - run: bash scripts/verify_readme.sh
```

### 5.3 `security.yml` (push, pull request, nightly)

Jobs: `gitleaks` (full history), `pip-audit`, `npm audit --audit-level=high`, `bandit -r apps/api packages/engine`, `hadolint`, `trivy fs` and `trivy image` on built images, license check. Fail on high severity.

### 5.4 `terraform.yml` (paths: `infra/**`)

```yaml
name: terraform
on:
  pull_request:
    paths: ["infra/**"]
  workflow_dispatch:
    inputs:
      apply: { description: "apply?", type: boolean, default: false }
jobs:
  validate:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: infra/terraform } }
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
      - run: terraform fmt -check -recursive
      - run: terraform init -backend=false
      - run: terraform validate
      - run: terraform test
      - uses: terraform-linters/setup-tflint@v4
      - run: tflint --recursive
      - run: pip install checkov && checkov -d . --quiet
  plan:
    needs: validate
    if: github.event_name == 'pull_request' && vars.HAS_CLOUD_CREDS == 'true'
    # init with real backend, plan, post summary as PR comment (secrets from environment)
  apply:
    needs: validate
    if: github.event_name == 'workflow_dispatch' && inputs.apply
    environment: demo   # requires manual approval
    # terraform apply -auto-approve with provider token from environment secret
```

### 5.4a Terraform scope (timeboxed to 2 hours total, P1)

Modules: `network` (firewall: 80, 443, SSH from allowlist) and `compute` (one VM, cloud-init installs Docker and the Compose plugin, pulls images, writes `.env` from secrets passed at apply time, starts the stack). Outputs: public IP. State: local or the provider's remote state; never commit state or tfvars with secrets. Provider is a decision for the team (a cloud account you already hold). **If Terraform is not working by Sunday 06:00 PKT, deploy the demo to a simple host (Render, Fly.io, Railway or a manual VM) and keep the Terraform code as documented but unused. Say so in the README.**

### 5.5 `deploy.yml` (on push to main after CI and e2e succeed, or on a version tag)

```yaml
name: deploy
on:
  workflow_run:
    workflows: [ci, e2e]
    types: [completed]
    branches: [main]
jobs:
  build-push:
    if: github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with: { registry: ghcr.io, username: "${{ github.actor }}", password: "${{ secrets.GITHUB_TOKEN }}" }
      - uses: docker/build-push-action@v6
        with: { context: apps/api, push: true, tags: "ghcr.io/${{ github.repository }}/api:${{ github.sha }}" }
      - uses: docker/build-push-action@v6
        with: { context: apps/web, push: true, tags: "ghcr.io/${{ github.repository }}/web:${{ github.sha }}" }
  release:
    needs: build-push
    environment: demo
    runs-on: ubuntu-latest
    steps:
      - run: echo "ssh to host, record previous tag, set IMAGE_TAG=${{ github.sha }}, docker compose pull && up -d"
      - run: bash scripts/smoke.sh "$DEMO_URL"        # /health, /api/amd-status, one audit call
      - if: failure()
        run: echo "roll back: IMAGE_TAG=<previous>, docker compose up -d, re-run smoke"
```

Smoke script checks: `/health` OK, `/api/amd-status` reports mode and model, a seeded audit returns the expected total, and the home page returns 200.

### 5.6 `live-smoke.yml` (manual only)

Uses repository secrets for the real AMD endpoint. One short call, records latency and tokens per second, uploads the result as an artifact. **Never runs on pull requests**, so secrets cannot leak to forks.

### 5.7 Repository hygiene

Branch protection on `main`: required checks `engine`, `api`, `web`, `benchmark-gate`, `cypress`, `security`. Conventional commits. Dependabot for pip, npm, Docker and Actions. `CODEOWNERS`. PR template with the definition-of-done checklist. Secrets only in GitHub environment secrets.

---

## 6. Quality gates summary (merge or release is blocked unless all pass)

| Gate | Threshold |
|------|-----------|
| Engine coverage | 100% lines and branches |
| API coverage | at least 85% |
| Web coverage | at least 80% lines |
| Audit gate (deterministic) | recall 100%, precision at least 99% on planted errors |
| Extraction replay gate | thresholds in `benchmark/thresholds.json` |
| Cypress | all flows pass, no serious accessibility violations |
| Security | no high-severity findings, no leaked secrets |
| Terraform | fmt, validate, tflint, checkov, `terraform test` pass (if infra exists) |
| Claims check | every figure traceable |
| README test | passes on a clean runner |

---

## 7. Work breakdown (parallel agents)

Phase 0 contracts first (OpenAPI, JSON schemas, data model, env contract, mock LLM server, folder layout, CI skeleton that runs empty jobs green).

- **A. API and DB:** FastAPI, SQLite, jobs, upload validation, rate limits, headers.
- **B. Engine:** rules, Decimal, 100% coverage, Hypothesis tests.
- **C. LLM layer:** client, prompts, schema validation, quote verifier, repair pass, replay recorder, mock server.
- **D. Frontend:** screens, Jest tests, Cypress specs.
- **E. Data and benchmark:** generator (seeded, reproducible), ground truth, tariff CSV (P1), runner, thresholds.
- **F. DevOps:** Dockerfiles, compose (plus CI override), workflows above, Terraform (timeboxed), scripts, README skeleton.
- **G. QA (separate agent that wrote no code):** owns the quality gates, tries to break things, files defects, verifies fixes, runs the README test and the claims check.

Rules for every agent: own your directories; run your tests before reporting; report facts (built, tested, not done); do not mark a task complete if its tests fail; do not weaken a test or a threshold to pass.

---

## 8. Schedule (PKT) with sleep built in

| When | What |
|------|------|
| Sat 02:00 to 03:30 | Phase 0: contracts, repo, CI skeleton, **AMD endpoint test call** |
| Sat 03:30 | **Decision gate:** endpoint works? Yes: continue. No: use the other AMD option (token factory vs Developer Cloud) and ask on Discord. Do not build further on an unreachable model. |
| Sat 03:30 to 07:00 | Humans sleep; agents run Phase 1 in parallel |
| Sat 07:00 to 12:00 | Review Phase 1 output; decide on Evolus (keep only if workspace works by 12:00) |
| Sat 12:00 to 20:00 | Phase 2: integration, real AMD calls recorded for replay, first live benchmark |
| Sat 20:00 to 23:00 | Phase 3a: QA agent pass, fixes, Terraform and deploy attempt |
| Sat 23:00 to Sun 05:00 | Humans sleep; agents fix defects and run full test suite |
| Sun 05:00 to 06:00 | Terraform checkpoint (see 5.4a) |
| Sun 06:00 to 12:00 | Final live benchmark, deploy, smoke test the public URL, freeze at 12:00 |
| Sun 12:00 to 15:00 | Demo video, slides, submission form; submit by 14:00 |

---

## 9. Definition of done

- [ ] `docker compose up` works on a clean machine; README test passes in CI.
- [ ] All gates in section 6 are green on `main`.
- [ ] Full flow works on generated data with live AMD and with replay (badge correct in both).
- [ ] Public demo URL passes the smoke script; endpoint-down behavior is graceful.
- [ ] `benchmark/results.json` exists from a real run; README and slides cite only it.
- [ ] Every claim traces to the claims register or the results file.
- [ ] Synthetic labels visible in the UI, README and slides.
- [ ] MIT license; no secrets in the repo or history.
- [ ] Limitations and roadmap are written honestly in the README.

---

## 10. Submission and pitch framing (Track 3)

Open with: "Most commerce tools chase top-line growth. Clawback protects margin from the cost side: it audits carrier invoices against the contract, and every dollar recovered goes straight to pre-tax profit." Describe the product as a copilot for the logistics or finance clerk. Say "private deployment on AMD infrastructure". Present dispute letters as the MVP output and portal or EDI submission as the roadmap. State plainly that all demo data is synthetic.

Demo (3 minutes): contract in, rules with verified quotes (show one ungrounded rule rejected), invoice batch in, findings and total from the generated data, one traced finding (invoice line, contract quote, arithmetic), the dispute letter, the AMD panel with live numbers, the benchmark figures from `results.json`.

Submission pack: title, short and long descriptions, tags (AMD ROCm, AMD Developer Cloud, Gemma, vLLM; Evolus only if integrated), cover image, architecture diagram, slides, demo video, public repo, demo URL.

---

## 11. Claims register (starting contents; the agent keeps it current)

| Claim | Status | Allowed wording |
|-------|--------|-----------------|
| Freight audits recover 3 to 7 percent of spend for mid-market shippers | Vendor-sourced, not verified | "Audit vendors report about 3 to 7 percent" |
| Up to 10 percent of freight bills contain errors | Vendor-sourced, not verified | "Up to" with attribution |
| UPS and FedEx claim windows are typically 15 days | Vendor-sourced, not verified | "Typically about 15 days; check your contract" |
| Audit firms often take 20 to 50 percent of recoveries | Vendor-sourced, not verified | "Commonly 20 to 50 percent" |
| Carriers require portal or EDI disputes | Unverified | Roadmap note only, no factual claim |
| Time saved for clerks | Not measured | Do not claim |
| Recovery rate in real life | Not measured | Do not claim; benchmark is synthetic |
| Fulfillment costs 15 to 20 percent of GMV | No source | Do not use |

---

## 12. Open items that need a human

1. AMD endpoint URL, API key, model name (blocks everything).
2. Public GitHub repo and a hosting or cloud account.
3. Discord answers: which deadline is binding; does Gemma qualify for the Google prize; can one project compete for Track 3 and a partner prize.
4. Evolus event code (only if you want that prize; default is off).
5. Cloud provider choice for Terraform (default assumption: a provider where you already have an account).

Start with Phase 0 now. Report at each phase end: done, verified how, broken, needed from humans.
