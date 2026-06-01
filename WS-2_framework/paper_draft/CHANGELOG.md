# `manuscript.tex` changelog

This file records substantive edits to the signal-equivalence framework
manuscript draft. Each entry lists the audit item it closed, the commit it
landed in, and what the change was for. Trivial typo and formatting fixes are
not logged here — see `git log -- manuscript.tex` for the full history.

The audit-item labels (A1–A6, B1–B5) refer to the Nature Methods
reviewer-readiness audit posted in the 2026-06-01 working session.

---

## v0.2 — 2026-06-01

Seven pure-text edits + one synthetic experiment, all done before any Phase 1
or Phase 3 empirical work landed. The draft is now reviewer-readier than v0.1
without depending on data the team does not yet have.

### Landed

| ID | Commit | What changed | Why |
|---|---|---|---|
| **A4** | `5e90b88` | Demoted the on-chain registry from "contribution #4" to a deployment-only detail; SHA-256 content-addressing is now the methodological substance. Renamed `l2_framework_hash` → `framework_hash`; removed *blockchain* / *on-chain* / *L2 spec* jargon from the abstract, intro, results case study, and discussion. | The blockchain framing was the most reviewer-hostile claim in v0.1; Nature Methods reviewers reach for "gimmick" when they see *blockchain* attached to a methods paper. Content-addressing is the actual contribution and survives that framing intact. |
| **B2** | `5e90b88` | Title shortened from "Signal-Equivalence: A Probabilistic Framework for Comparing Reconstruction Methods Across Reduced-Signal Imaging Modalities" (18 words) to "Signal-equivalence: testable dose-reduction claims for medical imaging" (8 words). Abstract restructured into four beats (problem / framework / library + worked examples / implications) without literal headings. | v0.1 title front-loaded "probabilistic" and was too long for Nature Methods house style. |
| **A3** | `5e90b88` | In §framework and clarification C5: `Π` carries acquisition-protocol metadata (CT vendor/kVp, MRI mask family, PET tracer/scanner). The MRI mask family rides inside `Π`, not as a sixth tuple slot. | open_questions §7 had flagged that the 5-tuple was effectively a 6-tuple for MRI. This edit closes the asymmetry inside the manuscript, not just in the proofs. |
| **B3** | `5e90b88` | "Out-of-scope claim types" rewritten as "Point-evaluated by design"; superiority / cross-modality / composition / multi-task framed as deliberate non-derivability rather than refusals. "Subpopulation failure modes" softened to "Subpopulation specificity" with explicit FDA subgroup-stratified-reporting alignment. | v0.1 read as a list of apologies. Same content, defensive instead of apologetic. |
| **B1** | `1cb17dd` | Added "Population claim vs.\ sample evidence" paragraph immediately after Definition 1: the two expectations are deterministic population objects the credential **asserts**; the bootstrap procedure at significance `α` provides finite-sample **evidence** from a test set drawn from `Π`. The credential records `n_test` and a slug resolving to the operational sampling protocol. | v0.1 conflated "population mean" (LHS of Eq. 1) with "α-confidence under the paired bootstrap" inside a single iff. The cleanest reviewer attack on the v0.1 draft. |
| **A5** | `5f0317e` | New "Ground-truth protocol" paragraph at the top of §methods-estimator borrowing the PWM-LDCT v0.5 annotation QA protocol verbatim (eligibility / 20-case calibration κ ≥ 0.60 / IoU ≥ 0.3 matching / >50 % majority-vote consolidation / third-rad discordance adjudication / rotating 5-case drift re-calibration). New "Label-noise refusal threshold" paragraph: the library refuses to issue a credential when documented inter-reader disagreement exceeds `ε/2`. Unified the credential JSON `ground_truth_protocol` field across the two worked-example JSONs. | v0.1's `ground_truth = "majority-vote-2-rads"` slug was hand-waved; for lung-nodule AUC this is the single most attackable claim in the paper. |
| **A6** | `120c61b` | New "Relation to task-based image-quality assessment" intro paragraph positioning signal-equivalence as complementary to the Barrett 1990 / Barrett & Myers 2013 / AAPM TG-233 lineage. Three anchor cites added to `refs.bib`. Theory folder: seeded `theory/related_work.md` with the four-paper memo skeleton and a "what is genuinely new" novelty gate for the v0.2 framework draft. | Closes the "you have reinvented task-based image quality" reviewer attack. open_questions §1 literature pass has a head start. |
| **A2** | `a5b67e2` | New Results subsection "Cross-modality consistency on synthetic data" with **real numbers** (not `\todo`): six credentials (3 modalities × 2 candidates) produced by the same paired-bootstrap code path show 3 expected PASS and 3 expected FAIL verdicts. New `experiments/cross_modality_consistency/` with a self-contained Python script, frozen `results.json`, and README. | The three independent per-modality worked examples did not rule out the possibility that the framework's generality is rhetorical. This experiment closes the gap with reproducible (seed = 42, bit-for-bit) numbers. |

### Schema bumps

- Credential JSON `schema_version`: `pwm-signal-equivalence/v0.1` → `v0.2`. Field renames (`l2_framework_hash` → `framework_hash`; `ground_truth` → `ground_truth_protocol`) are technically breaking; in pre-v1 we bump MINOR rather than introduce a parallel-versioning shim. The library, once it exists in Phase 3, ships against the v0.2 schema directly.

### What v0.2 still does **not** contain

- **Real per-modality Results tables.** Gated on WS-2 Phase 1 (CT, D9+90) and Phase 3 (MRI + PET validators, D9+270 → D9+365).
- **Numbers in the end-to-end worked example prose** (B4). Gated on the per-modality tables.
- **Real software-rigor counts.** `$N_{\textrm{tests}}$` and coverage % remain `\todo` until Phase 3 `pwm_dose_equivalence` v0.1 ships.
- **Closed-form sample-size derivation + coverage simulations.** open_questions §2 (BLOCK, ~2 wk) and §3 (BLOCK, ~1.5 wk); not data-gated but theory work that has not been scheduled into this pass.

### Theory-doc lag (intentional)

`theory/dose-equivalence-framework.md` remains at **v0.1**. Its own headline says it "Will be superseded by v0.2 after literature pass (see [`open_questions.md`](open_questions.md) §1)," and the literature pass has only been *seeded* (`theory/related_work.md` v0.1) rather than completed in depth. The manuscript-side v0.2 has therefore moved ahead of the theory-doc v0.1 — that is the documented gap.

What would close the gap: the depth-pass reading of fastMRI reader studies, one CHO-for-low-dose-CT paper, and Wunderlich/Noo on observer-model variance (listed in `theory/related_work.md` §5). At that point the theory doc bumps to v0.2 with the [SHARPEN-N] points reconciled against the manuscript edits in this changelog.

---

## v0.1 — 2026-05-20

Initial Nature Methods working draft seeded alongside `theory/dose-equivalence-framework.md` v0.1 and `theory/open_questions.md` v0.1. Not logged in detail here; see commit `5e90b88`'s parent for the seed state.
