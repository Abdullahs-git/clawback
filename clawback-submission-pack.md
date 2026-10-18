# CLAWBACK: SUBMISSION PACK (Sunday 18 Oct 2026)

Deadline: **15:00 PKT** (the page header says 20:00; treat 15:00 as binding). Submit by **14:40 PKT** at the latest.
Everything in [BRACKETS] must be copied from your own app or `benchmark/results.json`. Do not type a number from memory.

---

## 0. Time plan (from 13:45)

| Time | Task |
|------|------|
| 13:45 to 14:00 | Verification gate (section 1). If it fails, fix or cut the feature; do not demo it. |
| 14:00 to 14:25 | Record the demo video (section 5). Two takes maximum. |
| 14:25 to 14:35 | Cover image and slides (sections 6 and 7). Keep it plain. |
| 14:35 to 14:40 | Fill the form (sections 2 to 4) and submit. |
| 14:40 to 15:00 | Buffer. Re-open the submission and check every link works. |

---

## 1. Verification gate (15 minutes, do not skip)

Open each item and look at it yourself.

- [ ] Public GitHub repository opens in a private window (not logged in). Contains MIT LICENSE and a README.
- [ ] No keys in the repo: search the repo for `LLM_API_KEY=`, `hf_`, `sk-`, `Bearer `. `.env` is not committed.
- [ ] Public demo URL opens in a private window and loads real data (no placeholder numbers, no lorem ipsum, no fake logos).
- [ ] Click "Run live extraction on the sample contract" on the public URL. It returns real latency and tokens. If it fails, the badge must read REPLAY, never LIVE.
- [ ] The AMD panel shows the real model name, endpoint host, mode and last live call time.
- [ ] Every number on the dashboard matches the API (open one finding and check the arithmetic by hand with a calculator).
- [ ] "Synthetic demo data" label is visible on the demo workspace.
- [ ] README commands work from a clean folder: clone, copy `.env.example`, `docker compose up`, open the app.
- [ ] `benchmark/results.json` exists, has a `mode` field, and its totals reconcile (planted vs detected). If the totals still disagree, state both numbers honestly in the description or leave the figure out.

**If something fails and there is no time:** remove that claim from the submission rather than hiding the failure. A smaller true claim beats a bigger false one.

---

## 2. Form fields

**Project title:** Clawback

**Tagline:** Find the money your carriers overcharged you, with proof.

**Selected challenge:** Track 3: Reinvent Commerce

**Partner prizes to tick:**
- Google: tick only if the model you serve is a Gemma model and you confirmed eligibility on Discord.
- Evolus: **do not tick** unless the app really calls an Evolus workspace and the Evolus team can see the usage. Leave it off by default.

**Technology tags:** AMD ROCm, AMD Developer Cloud (or AMD Token Factory, whichever you really used), vLLM, [Gemma, exact version], FastAPI, React, TypeScript, Python, SQLite, Docker.

**Short description (about 280 characters):**

> Clawback is an AP copilot that reads a carrier contract with an open model on AMD, checks every extracted rule against the contract text, audits invoice lines with deterministic Decimal code, and drafts dispute letters for a human to approve. All demo data is synthetic.

**Long description:**

> **The problem.** Shippers pay carrier invoices with thousands of charges, and nobody has time to check each one against the negotiated contract. Audit vendors report that freight audits recover about 3 to 7 percent of freight spend, and carriers often allow only a short dispute window, commonly around 15 days for parcel. Outsourced audit firms commonly take 20 to 50 percent of what they recover. These figures come from vendor sources and are indicative only.
>
> **Why this is a commerce track project.** Most commerce tools chase revenue growth. Clawback protects margin from the cost side. A dollar recovered from an overcharge goes straight to pre-tax profit.
>
> **What Clawback does.**
> 1. A clerk uploads a carrier contract (text PDF). An open model served on AMD infrastructure reads it and proposes rules, each with a verbatim quote and page number.
> 2. Clawback checks that every quote exists in the contract text and that the extracted numbers are supported by the quote. Unsupported rules are rejected automatically. A human approves each rule before it is used.
> 3. Invoice lines (CSV) are audited by a pure-Python rules engine using exact Decimal arithmetic. The language model never computes money.
> 4. Each finding shows the invoice line, the contract quote and page, and the arithmetic, plus the claim deadline.
> 5. A dispute letter with an itemized evidence schedule is drafted for the clerk to review and approve. Clawback never contacts a carrier by itself.
>
> **How AMD is used.** The model that reads contracts [and normalizes invoice charge descriptions] runs on [AMD Developer Cloud / AMD Token Factory] through an OpenAI-compatible vLLM endpoint. The app has an AMD panel showing the model, endpoint host, mode, latency and tokens per second, and a button that makes a live call so anyone can check it. A replay mode serves recorded outputs from real AMD calls when the endpoint is unavailable, and the interface labels it clearly.
>
> **Measured results (synthetic benchmark, from `benchmark/results.json`, mode [live/replay], run on [date]).** [N] invoice lines across [N] batches and [N] synthetic contracts, with [N] planted errors. Findings matched [TP] of [N] planted errors, with [FP] false positives, including [N] compliant decoy lines. Average extraction latency [X] ms on the AMD endpoint. These results show the pipeline works as designed on synthetic data. They are not evidence of real-world recovery rates.
>
> **Limits, stated plainly.**
> - All demo data is synthetic. We have not tested real carrier contracts.
> - Scanned PDFs are not supported (text PDFs and CSV only).
> - Contracts that state a discount off a carrier's published tariff cannot be fully checked without that tariff table.
> - Dispute letters are drafts for a human. Submission through carrier portals or EDI is on the roadmap, not built.
> - Whether shippers would choose this over an audit firm is a hypothesis we have not validated.
>
> **Roadmap.** Carrier portal and EDI submission; tariff table support; claim-deadline alerts; testing on real contracts with a design partner.

---

## 3. Links to have ready

- Public GitHub repository URL
- Public demo application URL
- Demo video URL (YouTube unlisted or the platform's own upload)
- Slides (PDF)
- Cover image (1200 x 630 px or the size the form asks for)

---

## 4. Do not say (check the description, video and slides against this list)

on-prem or on-premises (say "private deployment on AMD infrastructure"); every penny; zero hallucinations; 100% accurate; 100% legally grounded; guaranteed; certified replay; signed PDF; legally enforceable; EDI-compatible; "saves 80% of audit time"; "wins X% of disputes"; any real customer, logo or testimonial; any number not copied from your app or `results.json`.

---

## 5. Demo video (3 minutes, record screen with voice)

Record at 1080p, browser zoom 110 to 125 percent so text is readable, notifications off, one clean window. Use the **public URL**, not localhost, so judges see it works online.

| Time | On screen | Say |
|------|-----------|-----|
| 0:00 to 0:25 | Landing page, then the demo workspace with the synthetic label visible | "Shippers pay carrier invoices with thousands of charges and rarely check them against the contract. Clawback is an AP copilot that finds overcharges and proves each one. All data you will see is synthetic." |
| 0:25 to 1:05 | Contracts page. Upload the sample contract. Rule cards appear with quotes. Show the contract viewer with the quote highlighted. Show one rejected rule with its reason. | "An open model on AMD proposes rules. Each rule must carry a verbatim quote. Clawback checks the quote exists and that the numbers match it. This rule was rejected because its quote is not in the contract. A human approves what stays." |
| 1:05 to 1:45 | Invoices page. Upload the batch. Run audit. Overview shows the total. | "Now we audit the invoice lines. A pure-Python engine does all the math in exact decimals. The model never touches money. Total recoverable here is [read the number from the screen], across [N] findings." |
| 1:45 to 2:20 | Open one finding. Show the three columns: invoice line, contract quote, arithmetic. Show the claim deadline. | "Every finding is traceable: the billed line, the contract page and quote, and the arithmetic. [Read the example amounts from the screen.]" |
| 2:20 to 2:40 | Disputes page. Open the draft, show the evidence table, click approve, export. | "Clawback drafts the dispute letter. A clerk reviews and approves it. We never contact the carrier automatically." |
| 2:40 to 3:00 | AMD page. Click the live extraction button. Show latency, tokens per second, model and host. Show the benchmark figures. | "Here is the AMD endpoint serving [model]. This button makes a live call: [read latency and tokens per second]. Our synthetic benchmark found [TP of N] planted errors with [FP] false positives. It is synthetic, so it shows the pipeline works, not real-world recovery. Clawback protects margin from the cost side of commerce." |

If the live call fails during recording, show the REPLAY badge and say "this is a recording of a real AMD call". Never present replay as live.

---

## 6. Cover image (1200 x 630)

Keep it simple and true: product name "Clawback", the tagline, a clean screenshot of the findings panel (three columns: invoice line, contract quote, arithmetic), and the label "Synthetic demo data" in small type. No fake logos, no partner logos you do not have permission to use, no invented figures.

---

## 7. Slides (8 slides, one idea each)

1. **Clawback:** tagline, team names, track.
2. **Problem:** carrier invoices are rarely checked; short dispute windows; audit firms take a cut (cite as vendor-sourced).
3. **Why commerce:** margin protection; a recovered dollar is pre-tax profit.
4. **How it works:** the five steps as a simple flow diagram.
5. **Safeguards:** model never does math; quotes verified and numbers checked; human approves rules and letters.
6. **AMD:** what runs on the GPU, the AMD panel screenshot, live vs replay explained.
7. **Results:** the numbers from `results.json` with mode, date, and the word "synthetic"; the limits line.
8. **Limits and roadmap:** the five limits above and the roadmap; the open hypothesis about buyers.

---

## 8. Honest answers to likely judge questions

1. **What does the GPU do?** "It reads contracts and [normalizes charge descriptions]. The audit math is deterministic code on purpose, because money should not depend on a model. [If you ran the concurrency test: quote the measured parallel latency.]"
2. **Is that live or replay?** "The badge tells you. The live button makes a real call now; replay is recorded from real calls and always labeled."
3. **How do you know the extracted numbers match the contract?** "We verify the quote exists in the contract text and that the numbers in the rule appear in the quote. A human then approves every rule."
4. **Your benchmark uses your own generator.** "Correct. It shows the pipeline works on synthetic data, including decoys [and a held-out set, if you built one]. We have not tested real carrier contracts."
5. **Why not an audit firm?** "Firms commonly take 20 to 50 percent of recoveries, according to vendor sources. Whether shippers prefer a self-serve tool is a hypothesis we have not validated."
6. **What about carrier portals and EDI?** "Not built. Letters are drafts for a human. Portal and EDI submission is the roadmap."
7. **Why Track 3?** "It protects commerce margin from the cost side. We know the track is mostly about customers, so we frame it as profitability."

---

## 9. Final submit checklist

- [ ] Verification gate in section 1 passed (or the failing claim was removed)
- [ ] Description, video and slides contain no phrase from section 4
- [ ] Every [BRACKET] replaced with a copied value, or the sentence deleted
- [ ] Video plays in a private window; the link is public or unlisted
- [ ] Repo, demo URL, video, slides and cover image links all open when logged out
- [ ] Correct track selected; partner prizes ticked only where true
- [ ] Submitted before 14:40 PKT; confirmation visible on the project page
- [ ] After submitting, re-open the project page and click every link once

Good luck.
