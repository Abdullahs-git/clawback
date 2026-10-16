# CLAWBACK FIX PLAN v3 (paste-ready prompt for the build agent)

You are fixing an existing project, not starting over. Keep the rules engine, the quote safeguard idea, the replay mode and the claims register. Everything below was found by an independent judge-style review on Saturday 17 Oct 2026, about 03:30 PKT. Deadline: Sunday 18 Oct 15:00 PKT. Feature freeze: Sunday 12:00 PKT.

## 0. Rules for this work

1. Report facts only: what you changed, what you tested, what is still broken. Never write "done" for something you did not run.
2. Do not weaken a test, a threshold, or a gate to make it pass. If a gate fails, fix the cause or report it.
3. Do not invent numbers. Every figure on screen, in docs or in the pitch must come from the API, `benchmark/results.json`, or `docs/claims-register.md`.
4. Do not hand-edit recorded fixtures. Fixtures come only from real calls to the AMD endpoint.
5. Work in the order of section 1. Stop and report if the AMD endpoint is not reachable.

## 1. Priority order and time boxes

| # | Fix | Why it matters | Time box |
|---|-----|----------------|----------|
| A | Prove the AMD live path | Prize eligibility depends on it | 2 h |
| B | Rebuild the frontend on real data | First thing judges see | 8 h |
| C | Repair benchmark integrity | The headline numbers contradict each other | 3 h |
| D | Add parameter-vs-quote validation | Closes the biggest safeguard hole | 2 h |
| E | Give AMD more meaningful work | One extraction call per contract is thin | 4 h |
| F | Harden the public demo | No auth plus LLM routes is an abuse risk | 2 h |
| G | Correct claims and docs | Overclaims lose credibility | 1.5 h |
| H | Tests, CI, deploy, final check | Gates in section 10 | 4 h |

## 2. Fix A: prove AMD is really used

Problems found: replay is the default; the telemetry in the docs is internally inconsistent (about 580 completion tokens at 58.5 tokens/s is roughly 10 s, but latency is stated as 610 to 680 ms); the AMD setup guide labels commands "verified" with no evidence.

Do this:
1. Make a real call to the AMD endpoint (token factory or your own vLLM). Capture: the `/v1/models` output, one full raw request and response JSON with timestamps and request id, and a provider dashboard or `rocm-smi` screenshot if available. Save them in `docs/amd-evidence/`.
2. Use whatever model the endpoint actually serves. Record the exact model name. The event banner mentions Gemma 4; ask on Discord which Gemma version qualifies for the Google prize before pinning Gemma 2 in docs.
3. Do not invent serving flags. In `docs/amd-setup.md`, keep only commands that were actually executed, with a log excerpt. Mark everything else "not verified". Remove the word "Verified" from any heading you cannot back with a log.
4. Replace every telemetry number in docs with values computed from the raw logs: end-to-end latency, time to first token if available, completion tokens, tokens per second. Check that the numbers are consistent with each other.
5. Record replay fixtures only from these real calls. Write `fixtures/manifest.json` with, per fixture: sha256, timestamp, model, endpoint host, request id. Add a test that recomputes the hashes and fails if a fixture was edited.
6. `benchmark/results.json` must contain provenance: git commit, seed, timestamp, `mode` (`live` or `replay`), model, endpoint host. Report live and replay results separately.

Done when: a reviewer can open `docs/amd-evidence/` and see a real, timestamped call, and the AMD panel shows the same figures.

## 3. Fix B: rebuild the frontend (truth first, then startup polish)

Problem reported: the frontend is broken, shows dummy and fake data, and does not look like a startup product. Treat this as a rebuild of the presentation layer on top of the existing API.

### 3.1 Purge fake data (do this first)

1. Audit the whole `src/` tree and list every hardcoded value: currency amounts, counts, names, dates, logos, testimonials, "customers", pricing, charts with literal arrays. Write the list to `docs/frontend-audit.md`.
2. Delete them. Every number on screen must come from an API response. A value with no data shows a designed empty state, never a placeholder number.
3. Mocks (MSW, fixtures) exist only in tests. The production bundle must not import them. Add a build check that fails if `msw` or `__fixtures__` appears in `dist/`.
4. Add a lint or test rule that fails on currency literals in components: regex `\$\s?\d` and `\d{1,3}(,\d{3})+` in `src/**/*.tsx`, excluding test files.
5. Forbidden content, enforced by a grep test: lorem ipsum, "Acme", "John Doe", fake testimonials, fake customer logos, "trusted by", invented user counts, fake pricing tiers, stock "99.9% uptime" claims.

### 3.2 Information architecture

- **Public landing `/`:** hero with an honest value proposition ("Find the money carriers overcharged you, with proof"); a "How it works" strip with four steps (contract in, rules approved by a human, invoices audited by deterministic code, dispute letter drafted); a "Proof" section whose numbers are fetched from `/api/benchmark` and labeled "synthetic benchmark" with the run date and mode; a "Why you can trust the numbers" section (no model math, quote-checked rules, human approval); one call to action: "Open the demo workspace".
- **App `/app`:** left navigation with Overview, Contracts, Invoices, Findings, Disputes, AMD status. Top bar with the LIVE or REPLAY badge and a persistent "Synthetic demo data" label whenever the workspace is the seeded demo.
- **First run:** a "Load synthetic demo workspace" button calling `POST /api/demo/seed`. After loading, every screen is populated from the database.

### 3.3 Screens (build to this spec)

1. **Overview:** one hero figure (total recoverable, from the API) with the number of findings and share of billed spend (computed by the API); a breakdown bar by rule type; a table of the largest findings; claim-deadline warnings. Every figure has a tooltip showing its source endpoint.
2. **Contracts:** upload, per-contract list, and the rule review screen. Each rule card shows the parsed parameter next to the verified contract quote, with the quote's numbers highlighted. Badge states: Verified, Rejected (with reason), Needs review. Actions: approve, reject, edit, approve all verified.
3. **Contract viewer:** show the contract page text with the verified quote highlighted in place. This is the key demo moment: judges see the grounding.
4. **Invoices:** upload, batch list, line table with search and filters, and a "Run audit" action with progress.
5. **Findings:** filterable table. Selecting a row opens a side panel (not a blocking modal) with three columns: the invoice line, the contract quote, and the arithmetic. Include the claim deadline.
6. **Disputes:** one draft per carrier, editable, an itemized evidence table, a clear Draft / Approved status, export to PDF or Markdown.
7. **AMD status:** model name, endpoint host, mode, last live call timestamp, latency, tokens per second, call log, and a "Run live extraction on the sample contract" button (see section 7).

### 3.4 Design direction

Calm, precise, finance-grade; not a generic purple-gradient SaaS template. One accent color, neutral slate surfaces, generous whitespace, clear hierarchy. Use a humanist sans for text and a monospace or tabular-figures face for money so columns align and right-align all amounts. Define design tokens (color, spacing, radius, type scale, elevation) once and use only tokens. Light and dark themes. Subtle motion only (150 to 200 ms), respecting `prefers-reduced-motion`.

### 3.5 States and quality

Every screen has loading skeletons, empty, error (with retry) and success states. Responsive at 375, 768 and 1440 px. Keyboard navigable with visible focus. Contrast at least WCAG AA. No console errors or warnings. Page-level lazy loading; the overview renders in under 2 s on the seeded data.

### 3.6 Frontend tests

- **Jest + React Testing Library + MSW:** each screen renders from API responses; formatting of currency (negatives, rounding, right alignment class); the dashboard total equals the sum of the findings returned; empty, loading and error states; badge logic for LIVE and REPLAY; the quote highlighter marks the right substring; rule approval transitions.
- **Truthfulness tests:** the currency-literal lint rule; the forbidden-content grep; a test that mounts each screen with an empty API and asserts that no digits appear except in labels.
- **Cypress against the running stack:** load demo workspace; upload a contract; reject an ungrounded rule; approve rules; run audit; open a finding and verify the three-column proof; edit and approve a letter; export. A custom command reads every currency string on screen and asserts it appears in the API's computed values. `cypress-axe` on every page.
- Visual check: screenshots at three widths stored as artifacts; the agent must view them and fix anything misaligned before reporting done.

## 4. Fix C: repair benchmark integrity

Problems found: planted total and detected total disagree by $28.80 while precision is reported as 100%; the same system generates the errors, the contracts and the answers; the planted error rate (23% of lines) is far above the 3 to 10% your own sources cite; there are no decoys.

1. **Reconcile the totals.** Give every planted error an id. Match each finding to a planted id. Report true positives, false positives and false negatives at finding level, with dollar totals per category. List the specific findings behind the $28.80 difference. If extras are genuine errors missing from the ground truth, update the ground truth with a written reason per item; otherwise count them as false positives and report precision below 100%.
2. **Add decoys:** at least 300 compliant lines near thresholds (fee equal to cap, one cent under, fuel exactly at target, legitimate repeated charges for multi-piece shipments, a charge with no applicable rule). Precision is measured against them.
3. **Realistic main set:** 5 to 10% of lines carry planted errors. Keep the current 23% set only as a labeled stress set.
4. **Held-out set:** generated from different templates and a different seed: two-column layouts, numbered clauses, tables, amendments, curly quotes, hyphenated line breaks, and PDFs exported by a different tool than the generator uses. Do not tune on it. Report extraction and quote-verification results on both sets.
5. **Mutation tests:** change one rule parameter and assert that exactly the affected findings change.
6. **Fix the duplicate rule's false-positive risk:** flag duplicates only when the charge, amount and shipment match, or mark lower confidence when quantities differ.
7. State plainly in the report: the benchmark measures the pipeline on synthetic data; it is not evidence of real-world recovery.

## 5. Fix D: validate parameters against the quote

Problem: the safeguard proves a quote exists, not that the extracted number matches it. A quote saying "$40" with `cap = 14` currently passes.

1. After quote verification, run `validate_parameters_against_quote(rule)`: extract numbers from the quote (digits, `$`, `%`, decimals, written-out numbers such as "forty dollars", "eleven and one-half percent") and require every numeric parameter to appear, after normalization (`40`, `40.00`, `$40`, "forty dollars"; `11.5%` and `0.115`).
2. Mismatch sets `status = rejected` with reason "parameter not supported by quote". A rule type's boolean flags (for example `allowed = false`) need a quote containing a waiver keyword from a maintained list ("waived", "no charge", "not apply").
3. In the review UI, bold the matched numbers inside the quote beside the parsed parameter so the human can check at a glance.
4. Tests: matching numbers, formats ($40 vs 40.00), spelled-out numbers, percent vs decimal, a mismatched number, a quote with two numbers where one is used, and a rule whose parameter appears only in a different clause.
5. Reword all docs: "unsupported quotes are rejected, parameters are checked against the quote, and a human approves every rule". Remove "zero hallucinations".

## 6. Fix E: give AMD a meaningful workload

Problem: audit math is pure Python, so AMD runs about one extraction call per contract. Judges will ask what the GPU does.

Add, in this order:
1. **Charge-description normalization (P1):** invoices often carry descriptions such as "RESI DLVRY" or "LIFT GATE SVC" instead of clean codes. Gemma maps each description to the code whitelist with a confidence. The mapping is validated against the whitelist; unknown or low-confidence mappings go to human review. The model never touches amounts. Include messy descriptions in the held-out set and report accuracy.
2. **Self-consistency extraction (P1):** run extraction k=3 in parallel. Accept a rule as high-confidence only if at least two runs agree on type and parameters; otherwise mark it needs-review. This makes real use of GPU concurrency and improves reliability.
3. **Finding explanations and letter cover paragraph (P2):** plain-language text generated from computed data; amounts are inserted from data and checked against it by a validator before display.
4. **Concurrency benchmark:** 1, 4, 8 and 16 parallel calls; record latency and tokens per second from the raw logs; save to `results.json` with `mode`.

## 7. Fix F: harden the public demo

The app has no authentication and calls a paid or credit-limited AMD endpoint.

1. `DEMO_MODE=true` on the public URL: the seeded workspace is read-only; uploads go to a sandbox with a 5 MB limit, 3 uploads per IP per hour, and automatic deletion after 1 hour.
2. Rate limits on all LLM-backed routes; a daily cap on live calls; a clear message when the cap is reached.
3. CORS allowlist; security headers; no secrets in the frontend bundle; no stack traces in errors; uploaded filenames sanitized; PDFs validated by content type and size.
4. `LLM_MODE=live` on the public URL with an automatic fallback that is visibly labeled REPLAY; never a silent fallback. `/api/amd-status` reports the timestamp of the last successful live call.
5. A "Run live extraction on the sample contract" button performs one real call and shows raw latency and tokens. Judges can verify AMD themselves.
6. Confirm a public demo URL exists and passes the smoke script. If none exists yet, deploy to the simplest working host now; Terraform must not block this.

## 8. Fix G: correct claims and docs

Make these edits and extend `scripts/check_claims.py` to catch them:

| Where | Wrong | Replace with |
|-------|-------|--------------|
| Tech stack doc | "banker's rounding (ROUND_HALF_UP)" | "ROUND_HALF_UP (not banker's rounding)" |
| ADR-002, README, pitch | "100% legally grounded", "zero hallucinations" | "quotes are verified, parameters are checked against them, and a human approves every rule" |
| Demo script, dispute docs | "signed PDF", "legally enforceable" | "approval-stamped PDF drafted for clerk review" |
| Track 3 doc | "EDI-compatible tables" | "CSV upload" (EDI is roadmap) |
| Track 3 doc | "e.g., FedEx, UPS" contracts | "synthetic contracts modeled on common LTL terms"; real carrier contracts are untested |
| Track 3 doc | "Czarlite" tariff tables | remove the brand name |
| Claims register | CLM-003 and CLM-005 sourced to carrier guides and "industry practice" | restore the true status: vendor-sourced, not independently verified |
| Benchmark docs | planted $9,159.31 vs $9,130.51 | one reconciled figure from the new results file |
| Demo script | "in seconds" and sub-second latency | the measured end-to-end time from the logs |

Add to the banned-phrase list: "zero hallucination", "100% legally", "legally enforceable", "signed PDF", "EDI-compatible", "certified replay" (replay is recorded, not certified). Keep the docs short: merge the 17 files into a README plus `docs/architecture.md`, `docs/amd-setup.md`, `docs/claims-register.md`, `docs/benchmark.md` and the demo script. Documentation volume does not score; a working product does.

## 9. Data-type hygiene (engine boundary)

The schema stores dimensions, confidence and some percentages as FLOAT. Convert them to `Decimal` through `Decimal(str(value))`, or store them as strings, so binary float artifacts never enter the engine. Add a test with `0.1`, `0.2` and `19.99` style values through the full path, and keep the AST test that bans `float` in the engine.

## 10. Gates before anything is called done

- [ ] `docs/amd-evidence/` contains a real, timestamped live call; fixtures match `manifest.json` hashes.
- [ ] Frontend: no hardcoded business data (lint and grep tests pass); mocks absent from the production bundle; every screen has loading, empty, error and success states; accessibility check passes; viewed screenshots at 375, 768 and 1440 px.
- [ ] Every currency string on screen equals an API value (Cypress custom command).
- [ ] Benchmark reconciled: finding-level TP, FP, FN; decoys included; held-out set reported; provenance in `results.json`.
- [ ] Parameter-vs-quote validation implemented and tested; docs reworded.
- [ ] Backend tests cover every endpoint (the current count of 6 is not enough); coverage at least 85%; engine at 100%.
- [ ] CI workflows exist and are green: lint, type check, tests, Cypress, security scans, claims check.
- [ ] Public URL passes the smoke script; live button works; fallback is labeled.
- [ ] `scripts/check_claims.py` passes with the extended banned phrases.
- [ ] README test passes on a clean checkout.

## 11. Questions judges will ask: have truthful answers ready

1. What does the GPU do that a CPU could not? (Answer from section 6 and the concurrency benchmark.)
2. Is the extraction result live or replayed? (Show `docs/amd-evidence/` and the badge.)
3. How do you know a parsed number matches the contract? (Section 5.)
4. Your benchmark uses your own generator. Why trust it? (Held-out set, decoys, and an honest statement of its limits.)
5. Why would a shipper buy this instead of paying an audit firm? (A hypothesis, stated as one; vendor-sourced 20 to 50 percent contingency fees.)
6. What happens with a real carrier contract? (Untested; say so; show the held-out formats.)
7. What stops someone abusing the public demo? (Section 7.)

## 12. Reporting format

After each fix letter: changed files, tests run and their results, what remains, and anything you need from a human (AMD endpoint details, Discord answers, hosting). If something cannot be verified, say "not verified" rather than guessing.

Start with Fix A.
