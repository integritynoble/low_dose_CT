# WS-4 — Permanent Leaderboard + Annual Review (Track 9 sub-track 9d)

A **self-sustaining citation-standard competition** launched at RSNA or ISBI, producing one peer-reviewed *State of the Field* review paper per year that compounds into a recurring publication record.

---

## Goals

1. **Launch a named competition** at RSNA 2027 or ISBI 2027 (whichever fits the 12-15 month post-mainnet window).
2. **Publish the *first annual review paper*** at ***npj Digital Medicine*** (primary; Nature sister journal, clinical-AI scope). Fallback: *Medical Image Analysis*.
3. **Recurring annual review paper** thereafter — one peer-reviewed publication per year, each citing every leaderboard entry from that year. By 2031 (long-term-vision five-year horizon), this stream alone produces **4 lead-author papers in a Nature sister journal** — more than WS-1 + WS-2 + WS-3 combined over the same span.

A successful WS-4 means: ≥ 20 community submissions in year 1, ≥ 1 industrial vendor participated, a named launch session at RSNA / ISBI, and the first review paper accepted before D9 + 900.

---

## Why a competition (not just a paper)

A paper drops once. A leaderboard accumulates citations every time a new method is published against it. By Year 2 (D9 + 730), the cumulative citations across the leaderboard's entries should exceed any single paper's citation count.

The annual review paper turns *every* community submission into a citation flowing back to the protocol. A 30-entry leaderboard becomes a 30-citation annual review that itself accumulates citations.

---

## Recurring-paper math

| Year | Annual review paper | Cumulative WS-4 papers | Cumulative Track 9 lead-author papers |
|---|---|---|---|
| 2028 (D9 + 730) | State of the Field — Year 1 | 1 | 4 (WS-1 + WS-2 + WS-3 + WS-4 #1) |
| 2029 | State of the Field — Year 2 | 2 | 5 |
| 2030 | State of the Field — Year 3 | 3 | 6 |
| 2031 | State of the Field — Year 4 | 4 | 7 |
| 2032 | State of the Field — Year 5 | 5 | 8 |

This is the mechanism that compounds Track 9 into a long-running publication engine, predictable on an annual cadence.

---

## Why *npj Digital Medicine* over *Medical Image Analysis*

| Factor | npj Digital Medicine | Medical Image Analysis |
|---|---|---|
| Family | Nature sister journal | Elsevier journal |
| Scope | Clinical AI, digital health interventions | Medical image analysis methods |
| Review-paper acceptance | Routine; publishes recurring competition reviews | Possible but rarer for recurring competition reviews |
| Per-year CV impact | Nature-family line per year | Strong field-specific line per year |
| Clinical framing fit | Strong — dose-equivalence is fundamentally a clinical decision | Medium |
| Impact factor (2025) | ~15 | ~11 |

The clinical framing of dose-equivalence ("at what dose ratio can we still confidently diagnose lung nodule X") is exactly what *npj Digital Medicine* publishes. *Medical Image Analysis* would accept a more technically-framed version of the same paper, but the recurring Nature-sister cadence is the stronger long-game.

---

## Tasks

### Phase 1 — Pre-launch design (D9 + 365 → D9 + 450)

| # | Task | Output |
|---|---|---|
| 1.1 | Containerized scoring service spec — takes a RunBundle, executes in sandbox, verifies published vs live `results.json` | `scoring/spec.md` |
| 1.2 | S1-S4 verification pipeline implementation | `scoring/verifier.py` |
| 1.3 | Public-facing leaderboard web app (responsive; sortable by metric, dose level, vendor, year) | `web/` |
| 1.4 | Submission contract document (what a RunBundle must contain; per L2 + L3 specs) | `submission_contract.md` |
| 1.5 | Conference venue secured (RSNA or ISBI 2027); speaking slot + workshop slot | Confirmation letter |

### Phase 2 — Launch (D9 + 540 → D9 + 730)

| # | Task | Output |
|---|---|---|
| 2.1 | Seed leaderboard with 4 reference entries (3 baselines + WS-3 reference method v1) | Live leaderboard with 4 entries |
| 2.2 | Open public submission window; announce on RSNA / ISBI mailing lists, arXiv-imaging, MICCAI Slack | Submission portal live |
| 2.3 | Industrial vendor outreach (Siemens, GE, Canon, Philips) — invite as challengers post-WS-3 paper | Outreach emails sent |
| 2.4 | Prize-pool setup ($50-200K equivalent in PWM tokens, Reserve-funded; top-10 distribution) | Prize structure on chain |
| 2.5 | Named launch event at conference (speaking slot + workshop demo + sponsor table) | Launch event executed |

### Phase 3 — Annual review paper #1 (D9 + 730 → D9 + 900)

| # | Task | Output |
|---|---|---|
| 3.1 | Curate year-1 submissions; summarize each entry (method, performance, novel ideas, failure modes) | Draft entry-summary section |
| 3.2 | Cross-year trend analysis (where does the field stand on PSNR, on UQ, on cross-vendor?) | Trends section |
| 3.3 | Clinical-impact analysis (which dose levels are now diagnostically equivalent across which subpopulations?) | Clinical-impact section |
| 3.4 | Recommendations to the field (open problems, dataset gaps, methodology suggestions) | Recommendations section |
| 3.5 | Submit to *npj Digital Medicine*; revise to acceptance | Acceptance letter |

### Phase 4 — Recurring annual cadence (D9 + 730+)

| # | Task | Annual cadence |
|---|---|---|
| 4.1 | Year-N leaderboard refresh (new submissions integrated; old kept) | Every May |
| 4.2 | Year-N annual review paper drafted | Every June-July |
| 4.3 | Year-N annual review paper submitted to *npj Digital Medicine* | Every August |
| 4.4 | Year-N annual review paper accepted (typical ~6 mo cycle) | Every February-March |

---

## Timeline (D9-anchored)

| Date | Milestone | Status |
|---|---|---|
| D9 + 365 | Scoring service design started; conference venue outreach | pending |
| D9 + 450 | Scoring service prototype green; web leaderboard mockup approved | pending |
| D9 + 540 | Scoring service live; 4 seed entries posted; submission portal open | pending |
| D9 + 730 | **Competition launched at RSNA / ISBI 2028; ≥ 20 community submissions; ≥ 1 vendor entry** | pending |
| D9 + 900 | **Annual review paper #1 submitted to *npj Digital Medicine*** | pending |
| D9 + 1095 (2029) | Annual review paper #1 accepted; year-2 leaderboard refresh begins | pending |
| Annually thereafter | One annual review paper per year through 2032+ | pending |

---

## Done when

- [ ] Live leaderboard at `lowdosect.pwm.platformai.org` (or equivalent subdomain)
- [ ] ≥ 20 community submissions in year 1
- [ ] ≥ 1 industrial vendor participated
- [ ] Named launch session held at RSNA / ISBI 2028
- [ ] **First annual review paper accepted in *npj Digital Medicine* (or fallback *Medical Image Analysis*)**
- [ ] Year-2 leaderboard refresh + Year-2 review paper drafted

---

## Subfolders (created on demand)

| Path | Purpose | Status |
|---|---|---|
| `scoring/` | Containerized scoring service; S1-S4 verification pipeline | pending Phase 1 |
| `web/` | Public leaderboard at lowdosect.pwm.platformai.org | pending Phase 1 |
| `submission_contract/` | Specification of what a RunBundle must contain | pending Phase 1 |
| `launch_event/` | RSNA / ISBI 2028 prep — slot logistics, sponsor outreach, prize fund | pending Phase 2 |
| `annual_review/` | "State of the Field" annual review papers, one per year | pending Phase 3 |

---

## Launch parameters

| Item | Target |
|---|---|
| Launch venue | RSNA 2027 or ISBI 2027 (12-15 months post-mainnet) |
| Prize pool | $50-200K equivalent in PWM tokens (Reserve-funded) |
| Prize distribution | Top-10: 1st 25% / 2nd 15% / 3rd 10% / 4th-10th ~7% each |
| Submission process | Containerized RunBundle → S1-S4 verification → leaderboard score |
| Industrial outreach | Invite Siemens, GE, Philips, Canon after WS-3 paper publishes; anonymized submissions OK |
| Citations target (24 mo post-launch) | ≥ 100 |
| Annual cadence | Year-N leaderboard refresh + Year-N State-of-the-Field review |

---

## Cross-references

- [`../WS-1_dataset/`](../WS-1_dataset/) — leaderboard scores submissions against this dataset
- [`../WS-3_reference_method/`](../WS-3_reference_method/) — provides one of the seed entries
- [`../pwm_integration/l3_spec.md`](../pwm_integration/l3_spec.md) — submission contract format
- [`../pwm_integration/l2_spec.md`](../pwm_integration/l2_spec.md) — credential requirement for submissions
