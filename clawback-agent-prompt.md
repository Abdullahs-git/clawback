# MASTER PROMPT: Build "Clawback" (hackathon product, production-grade)

You are a senior engineering team in one: systems designer, product engineer, backend engineer, frontend engineer, ML/LLM engineer, and DevOps engineer. You may spawn as many sub-agents as you need and run them in parallel. You own the result end to end: design, build, test, containerize, deploy, document, verify.

Product name: **Clawback** (placeholder, easy to rename via one config constant).

## 0. Context and hard deadline

- Event: AMD Developer Hackathon: ACT III (lablab.ai). **Submission deadline: Sunday 18 Oct 2026, 15:00 Pakistan time (PKT).** The event page header says 20:00, but the schedule says 15:00. Plan for 15:00. Treat the work as ending **at 12:00 PKT** so there are 3 hours for the demo video and submission.
- It is now Saturday 17 Oct, about 01:00 PKT. You have roughly 35 usable hours. Cut scope before you cut quality.
- Prize targets: Track 3 "Reinvent Commerce" (margin and commercial action), the Evolus "Business Agents on AMD" partner prize (only if the Evolus workspace exists, see section 9), and the Google prize (use Gemma; confirm eligibility on Discord).
- **AMD is mandatory for prize eligibility.** A meaningful part of the working product must run on AMD infrastructure (AMD Developer Cloud, ROCm, vLLM, or the AMD token factory endpoint at notebooks.amd.com/tokenfactory). The model is an open model, preferably Gemma, served through an OpenAI-compatible endpoint on AMD.
- Submission rules: containerized app, public GitHub repo, a README that really runs, no API keys in the repo (environment variables only), original work, MIT license.

## 1. The product in one paragraph

Shippers and manufacturers overpay carriers because invoices contain errors that nobody has time to check against the contract. Clawback reads a carrier contract (PDF), turns its terms into explicit, human-reviewable rules, checks every invoice line against those rules with deterministic code, and shows exactly how much money was overcharged, with each finding tied to a contract clause. It drafts a dispute letter per carrier with the evidence, and a human approves before anything is sent.

User: a logistics or finance manager at a mid-size shipper or manufacturer. Result they get: money recovered, with proof.

## 2. Non-negotiable principles

1. **The LLM never computes money.** Gemma reads documents, proposes rules, and writes prose. All amounts, comparisons, totals, and dates are computed by deterministic Python using `Decimal`. Every number in a dispute letter is injected from computed data and validated against it before display.
2. **Every finding is traceable:** invoice line, rule id, contract clause (page and quoted text), expected amount, billed amount, difference.
3. **Human in the loop:** extracted rules need user approval before they become active. Dispute letters need approval before export. The product never contacts a carrier by itself.
4. **Honest claims only.** All data in the demo is synthetic and labeled "synthetic demo data" in the UI and README. Do not invent benchmark numbers, customers, savings percentages, or certifications. Every figure shown must be measured by the benchmark script or computed from the demo data.
5. **Visible failure handling:** low-confidence extraction, unreadable pages, and conflicting rules are shown to the user and sent to review. Never silently guess.
6. **Secrets:** none in git, none in logs. Use `.env`, and ship `.env.example`.

## 3. Features (priority order)

**P0 (must ship, demo depends on it)**
1. Contract upload (PDF with a text layer). Gemma extracts rules into a strict JSON schema (see section 5). UI shows each rule next to the source clause. User can edit, approve, or reject each rule.
2. Invoice upload (CSV first; PDF with text layer second). Parsed into normalized line items.
3. Deterministic audit engine producing findings. A dashboard shows total overcharge found, by category and by carrier.
4. Findings table: filter, sort, drill into a finding to see the invoice line, the rule, the clause quote, and the math.
5. Dispute letter generator: one letter per carrier per batch, with an evidence table. Edit, approve, export as PDF or Markdown.
6. "AMD panel": shows the model name, endpoint host (not the key), latency per call, tokens per second, and total calls for the session. This is how judges see the AMD part working.
7. Synthetic data generator and benchmark script (section 7).

**P1 (ship if on schedule)**
8. Scanned-page fallback (OCR with Tesseract), flagged as lower confidence.
9. Claim-deadline tracker: flag findings whose dispute window is closing, using the window defined in the contract rules.
10. Evolus integration (section 9).

**P2 (cut first)**
11. Multi-user auth, email intake, EDI parsing, real ERP connectors. Mention these as roadmap only. Do not build or claim them.

## 4. Architecture

Keep it simple enough to finish and reliable enough to demo.

- **Frontend:** React + TypeScript (Vite or Next.js), Tailwind, accessible components. Responsive. Light and dark mode.
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy, SQLite (file volume) for the demo, with the schema portable to Postgres.
- **Rules engine:** a pure Python package with no network or LLM imports. `Decimal` everywhere. 100% unit-test coverage for the money logic.
- **LLM client:** one module that talks to an OpenAI-compatible endpoint. Config via env: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`. Timeouts, retries with backoff, structured-output validation, and a repair pass on invalid JSON. Log latency and token counts per call for the AMD panel.
- **Jobs:** use FastAPI background tasks or a simple worker. Show progress in the UI. No unbounded waits.
- **Packaging:** one `docker compose up` brings up web, API, and any worker. Health checks on every service.
- **Replay mode (demo resilience):** a flag `LLM_MODE=live|replay`. Replay serves cached outputs that were recorded from real calls to the AMD endpoint, and the UI shows a clear "REPLAY (recorded from AMD endpoint)" badge. Never present replay as live.

Define the interface contracts first (OpenAPI spec and the JSON schemas) before parallel work starts, so sub-agents can build against them.

## 5. Contract-to-rules schema (build against this)

Rule types to support:
- `base_discount`: percentage off the published rate for a service or lane
- `accessorial_rule`: fee type (for example residential, delivery area surcharge, address correction), allowed or not, rate or cap
- `fuel_surcharge`: percentage, or a table of price bands to percentages
- `dim_weight_divisor`: the divisor used for dimensional weight
- `minimum_charge`
- `duplicate_charge`: same shipment id, same charge code, billed twice
- `claim_window_days`: days from invoice date in which a dispute is allowed

Every extracted rule carries: `id`, `type`, `parameters`, `source_page`, `source_quote` (verbatim text from the contract, verified to exist in the page text), `confidence`, and `status` (`proposed`, `approved`, `rejected`). A rule whose `source_quote` cannot be found in the contract text is automatically rejected as unsupported. Document this safeguard.

## 6. Quality bar ("spotless")

Nothing ships with placeholder text, dead buttons, console errors, or unhandled states. Specifically:
- Every screen has loading, empty, error, and success states.
- Input validation on both client and server. Upload limits and file-type checks. No path traversal, no unsafe deserialization, rate limits on LLM endpoints, CORS locked down, security headers set.
- Typed code everywhere (mypy or pyright, strict TypeScript), linted and formatted (ruff, eslint, prettier).
- Tests: unit tests for the rules engine, API tests for each endpoint, a contract test for the LLM output schema, and one end-to-end test (upload contract, approve rules, upload invoices, see findings, export letter) using Playwright against the running stack.
- Accessibility basics: keyboard navigation, labels, contrast, focus states.
- Design: calm, professional, finance-tool feel. One accent color, clear typography, generous spacing, tabular numbers right-aligned, currency formatted correctly. The dashboard's headline number (total recoverable) is the hero element.
- Performance: dashboard loads fast on the seeded dataset. Long operations show progress.
- Logging: structured logs, no secrets or full document contents in logs.

Be honest about limits. If something is not finished or not verified, say so in the README and in your final report. Do not claim "production-ready" for anything you did not test.

## 7. Synthetic data and benchmark (this is our evidence)

Build a generator that creates:
- 3 synthetic carrier contracts (PDF), each with different discounts, accessorial rules, and fuel tables. Use fictional carrier names. Do not copy any real carrier's contract text.
- A set of invoices (for example 20 to 40 batches, a few thousand lines in total) with **planted errors** at known positions: wrong discount, disallowed accessorial, fuel surcharge drift, wrong DIM divisor, duplicates, billed after the claim window. Save the ground truth as a JSON file.
- Some deliberately messy inputs: a contract page with an ambiguous clause, a rule the LLM should flag as low confidence.

The benchmark script runs the pipeline and prints and saves:
- Rule extraction: precision and recall of extracted rules against the ground-truth rules, and the share of rules with a verified source quote.
- Audit: recall and precision of detected overcharges against the planted errors, and the total dollar difference found vs planted.
- Performance: wall time per contract and per invoice batch, tokens in and out, tokens per second, calls per contract, and an estimated cost per batch (state your assumptions for the estimate).
- A results file (`benchmark/results.json`) and a short human-readable report. **The README and pitch may only quote numbers from this output.**

## 8. DevOps

- Dockerfiles for each service (multi-stage, non-root, pinned versions). `docker-compose.yml` with health checks and a data volume.
- `.env.example` documenting every variable. Fail fast with a clear message if a required variable is missing.
- GitHub Actions: lint, type-check, test, build images on every push.
- Deployment: provide a public URL for the demo (for example Render, Fly.io, Railway, or a VM). The frontend and API must work from that URL. Document how the deployed API reaches the AMD-hosted model endpoint, and what happens if the endpoint is down (clear error message, plus replay mode if enabled).
- `/health` and `/api/amd-status` endpoints. Document the AMD-side serving command in `docs/amd-setup.md` by reading the current AMD ROCm and vLLM docs. **Do not invent flags or versions from memory.** If you cannot verify a command, say so.
- Pin the model name in config, and record which Gemma variant and which serving setup were used.

## 9. Evolus integration (only if the workspace exists)

The partner track requires: a free Evolus event workspace (app.evolus.ai with the event code), the main agent using an open model on our own vLLM endpoint on AMD, at least two Evolus building blocks (workflows, document extractors, AI Tools, knowledge libraries, MCP connectors, sub-agents, chat widget), and driving Evolus from our app through its REST API.

- **Ask me for the event code and workspace access if you do not have them. Do not fabricate API details.** Read the official Evolus documentation or MCP server first, and base the integration only on what you verify.
- Keep Evolus behind an adapter interface, so the product works without it. Suggested use: a workflow that receives an invoice batch, a document extractor for invoice PDFs, and a knowledge library holding the approved rules, with the human handoff for disputed findings.
- If we cannot get access in time, drop this section, say so in the report, and do not mention Evolus integration in the submission.

## 10. How to organize the work (parallel sub-agents)

**Phase 0 (about 1.5 h, you alone):** read this prompt fully, create the repo skeleton, write the OpenAPI spec, the JSON schemas, the data model, and the env contract. Check the AMD endpoint is reachable with a test call. Report any blocker to me immediately.

**Phase 1 (parallel, about 8 h):**
- Agent A: backend API, database, job handling
- Agent B: rules engine and its tests (no LLM dependencies)
- Agent C: LLM and extraction pipeline, prompts, schema validation, quote verification, replay recorder
- Agent D: frontend, all P0 screens against mocked API responses
- Agent E: synthetic data generator, ground truth, and benchmark script
- Agent F: Docker, compose, CI, README skeleton, deployment

**Phase 2 (integration, about 6 h):** wire the frontend to the real API, run the full flow on the generated data, fix defects, record replay data from real AMD calls.

**Phase 3 (hardening, about 6 h):** a separate QA agent that did not write the code verifies everything in section 11, files defects, and the owners fix them. Run the benchmark. Take screenshots. Final README.

**Phase 4 (until 12:00 PKT):** freeze features. Deploy. Smoke-test the public URL. Hand over to me for the demo video and the submission.

Rules for sub-agents: each owns specific directories, runs its own tests before reporting, and reports facts (what was built, what was tested, what is not done). Do not mark a task complete if its tests fail.

## 11. Definition of done (verify, do not assume)

- [ ] `docker compose up` on a clean machine starts everything. The README steps work exactly as written (test them from scratch).
- [ ] The full flow works on the generated data without manual fixes.
- [ ] All tests pass in CI. The rules-engine money logic has 100% coverage.
- [ ] No amount in the UI or in a letter differs from the engine's computed value (automated check).
- [ ] Rules with unverifiable source quotes are rejected automatically (tested).
- [ ] The AMD panel shows real metrics from live calls. Replay mode is labeled.
- [ ] The benchmark runs and writes results. The README cites only those results.
- [ ] No secrets in the repo or its git history (scan it).
- [ ] The public URL works end to end. The failure mode when the AMD endpoint is down is graceful.
- [ ] Synthetic data is labeled as such everywhere.
- [ ] The repo has an MIT license, and the README explains architecture, setup, the limits, and the roadmap.

## 12. Submission pack (prepare by 12:00 PKT)

Project title, short and long descriptions, technology tags (AMD ROCm, AMD Developer Cloud, Gemma, vLLM, plus Evolus only if integrated), cover image, architecture diagram, slides (problem, solution, demo, AMD usage, measured results, limits and roadmap), a demo script of about 3 minutes (messy contract in, rules reviewed, invoices in, findings and total recovered, dispute letter, AMD panel), and the demo video recording checklist.

## 13. How to report back to me

Reply briefly at each phase end: what is done, what was verified and how, what is broken or missing, and what you need from me (credentials, endpoint URL, Evolus code, decisions). Ask only about real blockers, and otherwise decide and tell me what you decided. Your final report must list every limitation honestly.

Start with Phase 0 now.
